"""Freshly hatched native species must survive primary save/load without low-byte aliasing."""
import argparse
from pathlib import Path

from pyboy import PyBoy


LEVEL = 5
DV = 15
HATCHED_HAPPINESS = 120
MON_NAME_LENGTH = 11
NAME_RECORD_LENGTH = MON_NAME_LENGTH - 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    rom = parser.parse_args().rom

    symbols = {}
    for line in rom.with_suffix(".sym").read_text().splitlines():
        fields = line.split()
        if len(fields) == 2 and ":" in fields[0]:
            symbols[fields[1]] = tuple(int(v, 16) for v in fields[0].split(":"))

    def addr(name):
        return symbols[name][1]

    def offset(name):
        bank, address = symbols[name]
        return bank * 0x4000 + address - (0x4000 if bank else 0)

    data = rom.read_bytes()
    base_size = addr("wCurBaseDataEnd") - addr("wCurBaseData")
    base_start = offset("BaseDataRecords")
    name_start = offset("PokemonNameRecords")

    pyboy = PyBoy(
        str(rom),
        window="null",
        sound_emulated=False,
        cgb=True,
        log_level="ERROR",
    )
    mem, regs = pyboy.memory, pyboy.register_file

    party = addr("wPartyMon1Species")
    stride = addr("wPartyMon2Species") - party
    form_offset = addr("wPartyMon1Form") - party
    happiness_offset = addr("wPartyMon1Happiness") - party
    id_offset = addr("wPartyMon1ID") - party
    level_offset = addr("wPartyMon1Level") - party
    status_offset = addr("wPartyMon1Status") - party
    hp_offset = addr("wPartyMon1HP") - party
    maxhp_offset = addr("wPartyMon1MaxHP") - party
    ev_offset = addr("wPartyMon1EVs") - party
    dv_offset = addr("wPartyMon1DVs") - party
    nature_offset = addr("wPartyMon1Nature") - party
    table_entry = lambda slot: addr("wPokemonIndexTableEntries") + 2 * (slot - 1)

    def expected_stats(native):
        start = base_start + (native - 1) * base_size
        base = list(data[start:start + 6])
        out = []
        for i, stat in enumerate(base):
            value = ((2 * (stat + DV) + 1) * LEVEL) // 100
            value += LEVEL + 10 if i == 0 else 5
            out.append(value)
        return out

    def read_words(start, count):
        return [
            (mem[start + i * 2] << 8) | mem[start + i * 2 + 1]
            for i in range(count)
        ]

    def prepare_sram_access():
        mem[0x0000] = 0x0A
        mem[0x4000] = symbols["sSRAMAccessCount"][0]
        mem[addr("sSRAMAccessCount")] = 0
        mem[addr("wSRAMAccessCount")] = 1

    def invoke(name, hl=None, de=None):
        prepare_sram_access()
        bank, target = symbols[name]
        bank = bank or 1
        mem[0x2000] = bank
        mem[addr("hROMBank")] = bank
        mem[0xC100:0xC106] = [
            0xF3,
            0xCD,
            target & 0xFF,
            target >> 8,
            0x18,
            0xFE,
        ]
        if hl is not None:
            regs.HL = hl
        if de is not None:
            regs.DE = de
        regs.SP = 0xC0FF
        regs.PC = 0xC100
        pyboy.tick(10, False, False)
        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF), (
            name,
            hex(regs.PC),
            hex(regs.SP),
        )
        assert mem[addr("hROMBank")] == bank
        assert mem[0xFF70] & 7 == 1

    try:
        mem[0xFF50] = 1
        mem[0xFFFF] = 0
        mem[0xFF0F] = 0
        mem[0xFF40] = 0
        mem[0xFF70] = 1

        # Bypass only hatch text/UI. Core HatchEggs work remains real.
        print_bank, print_addr = symbols["PrintText"]
        mem[print_bank, print_addr] = 0xC9

        native = 0x0101
        root = 0x0001
        decoded_form = 0x21

        # Native-format party Egg with authoritative ID in transient slot 7.
        mem[addr("wPokemonData"):addr("wPokemonDataEnd")] = [0] * (
            addr("wPokemonDataEnd") - addr("wPokemonData")
        )
        mem[addr("wPokemonDataFormat"):addr("wPokemonDataFormat") + 2] = [0xBC, 0x16]
        mem[0xFF70] = 2
        mem[addr("wPokemonIndexTable"):addr("wPokemonIndexTableEnd")] = [0] * (
            addr("wPokemonIndexTableEnd") - addr("wPokemonIndexTable")
        )
        mem[table_entry(7):table_entry(7) + 2] = list(native.to_bytes(2, "little"))
        mem[addr("wPokemonIndexTableUsedSlots")] = 7
        mem[0xFF70] = 1

        mem[party] = 7
        mem[party + form_offset] = 0xC1
        mem[party + happiness_offset] = 0
        mem[party + level_offset] = LEVEL
        mem[party + ev_offset:party + ev_offset + 6] = [0] * 6
        mem[party + dv_offset:party + dv_offset + 3] = [0xFF] * 3
        mem[party + nature_offset] = 0
        mem[party + status_offset] = 0xA5
        mem[party + status_offset + 1] = 0x5A
        mem[party + hp_offset:party + hp_offset + 2] = [0, 20]
        mem[party + maxhp_offset:party + maxhp_offset + 12] = [0] * 12
        mem[party + maxhp_offset:party + maxhp_offset + 2] = [0, 20]

        mem[addr("wPartyCount")] = 1
        mem[addr("wCurPartyMon")] = 0
        mem[addr("wPlayerID"):addr("wPlayerID") + 2] = [0x12, 0x34]
        mem[addr("wInitialOptions")] = 0
        mem[addr("wInitialOptions2")] = 0
        mem[addr("wOptions3")] = 0xFF
        mem[addr("wDexCacheValid")] = 1

        invoke("HatchEggs")

        stats = expected_stats(native)
        expected_name = data[
            name_start + native * NAME_RECORD_LENGTH:
            name_start + (native + 1) * NAME_RECORD_LENGTH
        ]
        assert mem[party + happiness_offset] == HATCHED_HAPPINESS
        assert not (mem[party + form_offset] & 0x40)
        assert bytes(mem[party + id_offset:party + id_offset + 2]) == bytes([0x12, 0x34])
        assert bytes(mem[party + status_offset:party + status_offset + 2]) == bytes([0, 0])
        assert read_words(party + maxhp_offset, 6) == stats
        assert ((mem[party + hp_offset] << 8) | mem[party + hp_offset + 1]) == stats[0]
        assert bytes(
            mem[addr("wPartyMon1Nickname"):addr("wPartyMon1Nickname") + NAME_RECORD_LENGTH]
        ) == expected_name

        # Save the exact two pieces required to preserve native party identity.
        invoke("SavePokemonData")
        invoke("SavePokemonIndexTable")

        # The saved native table must be internally valid before reload.
        invoke("VerifyPokemonIndexTable")
        assert regs.F & 0x80, "saved native index table failed verification"

        # Simulate a fresh process by destroying both live Pokemon data and the
        # live native index table before loading the primary save copy.
        mem[addr("wPokemonData"):addr("wPokemonDataEnd")] = [0xA5] * (
            addr("wPokemonDataEnd") - addr("wPokemonData")
        )
        mem[0xFF70] = 2
        mem[addr("wPokemonIndexTable"):addr("wPokemonIndexTableEnd")] = [0x5A] * (
            addr("wPokemonIndexTableEnd") - addr("wPokemonIndexTable")
        )
        mem[0xFF70] = 1

        invoke("LoadPokemonData")
        invoke("LoadPokemonIndexTable")

        # The ordinary saved party payload is restored exactly.
        assert mem[addr("wPartyCount")] == 1
        assert mem[party + happiness_offset] == HATCHED_HAPPINESS
        assert not (mem[party + form_offset] & 0x40)
        assert bytes(mem[party + id_offset:party + id_offset + 2]) == bytes([0x12, 0x34])
        assert bytes(mem[party + status_offset:party + status_offset + 2]) == bytes([0, 0])
        assert read_words(party + maxhp_offset, 6) == stats
        assert ((mem[party + hp_offset] << 8) | mem[party + hp_offset + 1]) == stats[0]
        assert bytes(
            mem[addr("wPartyMon1Nickname"):addr("wPartyMon1Nickname") + NAME_RECORD_LENGTH]
        ) == expected_name

        # Most importantly, ask the real native decoder what the reloaded party
        # record is. Garbage collection may renumber the transient slot, so only
        # the decoded full native word is authoritative.
        form_delta = form_offset
        invoke("GetNativeSpeciesIDFromPokemonDataStruct", hl=party, de=form_delta)
        decoded = (regs.B << 8) | regs.C
        assert decoded == native, hex(decoded)
        assert decoded != root, "reloaded hatchling collapsed to low-byte species"

        # Its decoded presentation identity must still be the extended root.
        invoke("LoadCurSpeciesAndFormFromPokemonDataStruct", hl=party)
        assert mem[addr("wCurSpecies")] == 1
        assert mem[addr("wCurPartySpecies")] == 1
        assert mem[addr("wCurForm")] & 0x3F == decoded_form

        print(
            "PASS: hatched native $0101 survives primary SavePokemonData + "
            "SavePokemonIndexTable, RAM wipe, reload, full native decode, stats/HP, "
            "nickname, Egg clear, happiness, OT and status without $0001 aliasing"
        )
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
