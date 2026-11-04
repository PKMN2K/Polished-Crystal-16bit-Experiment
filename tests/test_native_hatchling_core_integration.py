"""Integrated core HatchEggs test for native ordinary and extended party identities."""
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
    party_end = addr("wPartyMon2Species")
    stride = party_end - party
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

    def call_home(name, b=0, c=0):
        bank, target = symbols[name]
        assert bank == 0, (name, bank)
        mem[0x2000] = 1
        mem[addr("hROMBank")] = 1
        mem[0xC100:0xC106] = [
            0xF3,
            0xCD,
            target & 0xFF,
            target >> 8,
            0x18,
            0xFE,
        ]
        regs.B = b
        regs.C = c
        regs.SP = 0xC0FF
        regs.PC = 0xC100
        pyboy.tick(4, False, False)
        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF), (
            name,
            hex(regs.PC),
            hex(regs.SP),
        )
        return bool(regs.F & 0x80)  # Z flag

    def invoke_hatch():
        bank, target = symbols["HatchEggs"]
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
        regs.SP = 0xC0FF
        regs.PC = 0xC100
        pyboy.tick(4, False, False)
        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF), (
            hex(regs.PC),
            hex(regs.SP),
        )

    try:
        mem[0xFF50] = 1
        mem[0xFFFF] = 0
        mem[0xFF0F] = 0
        mem[0xFF40] = 0
        mem[0xFF70] = 1

        # Keep the core hatch path real while bypassing only text/UI execution.
        print_bank, print_addr = symbols["PrintText"]
        mem[print_bank, print_addr] = 0xC9

        cases = [
            (0x0019, 25, 0x01),
            (0x0101, 1, 0x21),
        ]

        for native, root, decoded_form in cases:
            # Reset party, temp buffers and Dex flags.
            mem[party:party + stride] = [0] * stride
            mem[addr("wTempMon"):addr("wTempMon") + stride] = [0] * stride
            mem[addr("wPokedexFlags"):addr("wEndPokedexFlags")] = [0] * (
                addr("wEndPokedexFlags") - addr("wPokedexFlags")
            )

            # Native-format authoritative identity.
            mem[addr("wPokemonDataFormat"):addr("wPokemonDataFormat") + 2] = [0xBC, 0x16]
            mem[0xFF70] = 2
            entry = addr("wPokemonIndexTableEntries") + 12
            mem[entry:entry + 2] = list(native.to_bytes(2, "little"))
            mem[0xFF70] = 1

            # Deliberately stale legacy species/form identity plus Egg bit.
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
            mem[addr("wOptions3")] = 0xFF  # NICKNAMES_NEVER wins first.
            mem[addr("wDexCacheValid")] = 1
            mem[addr("wCurSpecies")] = 91
            mem[addr("wCurPartySpecies")] = 92
            mem[addr("wCurForm")] = 3

            invoke_hatch()

            # Core party mutation.
            assert mem[party + happiness_offset] == HATCHED_HAPPINESS, native
            assert not (mem[party + form_offset] & 0x40), native
            assert mem[party + form_offset] & 0x80, native
            assert bytes(mem[party + id_offset:party + id_offset + 2]) == bytes([0x12, 0x34]), native
            assert bytes(mem[party + status_offset:party + status_offset + 2]) == bytes([0, 0]), native

            stats = expected_stats(native)
            assert read_words(party + maxhp_offset, 6) == stats, (native, read_words(party + maxhp_offset, 6), stats)
            assert ((mem[party + hp_offset] << 8) | mem[party + hp_offset + 1]) == stats[0], native

            # Native identity survives the integrated copy/base-data/stat path.
            assert mem[addr("wTempMonSpecies")] == (root & 0xFF), native
            assert mem[addr("wTempMonForm")] & 0x3F == decoded_form, (
                native,
                hex(mem[addr("wTempMonForm")]),
            )

            base_expected = data[
                base_start + (native - 1) * base_size:
                base_start + native * base_size
            ]
            assert bytes(mem[addr("wCurBaseData"):addr("wCurBaseDataEnd")]) == base_expected, native

            # The literal Egg nickname is replaced by the native root's species name.
            name_expected = data[
                name_start + native * NAME_RECORD_LENGTH:
                name_start + (native + 1) * NAME_RECORD_LENGTH
            ]
            nickname = bytes(mem[addr("wPartyMon1Nickname"):addr("wPartyMon1Nickname") + NAME_RECORD_LENGTH])
            assert nickname == name_expected, (native, nickname.hex(), name_expected.hex())

            # Real Dex registration must mark the native identity, not a low-byte alias.
            form_for_dex = decoded_form
            assert not call_home("CheckCaughtMon", form_for_dex, root & 0xFF), ("caught", native)
            assert not call_home("CheckSeenMon", form_for_dex, root & 0xFF), ("seen", native)
            if native == 0x0101:
                assert call_home("CheckCaughtMon", 0x01, 0x01), "extended caught alias"
                assert call_home("CheckSeenMon", 0x01, 0x01), "extended seen alias"

            assert mem[addr("wDexCacheValid")] == 0, native

        print(
            "PASS: integrated core HatchEggs ordinary+$0101 cases; Egg clear, friendship/OT/status, "
            "native temp identity/base data, real stats+HP, species nickname replacement, and Dex anti-alias"
        )
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
