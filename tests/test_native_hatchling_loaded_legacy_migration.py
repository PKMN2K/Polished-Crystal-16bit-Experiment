"""A legacy save loaded through TryLoadSaveFile must migrate, hatch, and re-save native identity."""
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
            regs.D = (de >> 8) & 0xFF
            regs.E = de & 0xFF
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

        # Start exactly like an old legacy save: species $01 plus EXTSPECIES
        # encodes native root $0101, with Egg and gender metadata sharing the form byte.
        mem[addr("wPokemonData"):addr("wPokemonDataEnd")] = [0] * (
            addr("wPokemonDataEnd") - addr("wPokemonData")
        )
        mem[addr("wPokemonDataFormat"):addr("wPokemonDataFormat") + 2] = [0, 0]
        mem[0xFF70] = 2
        mem[addr("wPokemonIndexTable"):addr("wPokemonIndexTableEnd")] = [0] * (
            addr("wPokemonIndexTableEnd") - addr("wPokemonIndexTable")
        )
        mem[0xFF70] = 1

        mem[party] = 1
        mem[party + form_offset] = 0xE1
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

        # Serialize an actual legacy primary save envelope. SavePokemonData
        # stamps the current envelope/version, so patch only those compatibility
        # markers back to the accepted version-10 legacy representation, then
        # recompute the real game-data checksum.
        invoke("SavePlayerData")
        invoke("SavePokemonData")
        mem[0x0000] = 0x0A
        mem[0x4000] = symbols["sPokemonData"][0]
        saved_data = addr("sPokemonData")
        format_delta = addr("wPokemonDataFormat") - addr("wPokemonData")
        table_format_delta = addr("wPokemonIndexTableFormat") - addr("wPokemonData")
        mem[saved_data + format_delta:saved_data + format_delta + 2] = [0, 0]
        mem[saved_data + table_format_delta:saved_data + table_format_delta + 2] = [0, 0]
        mem[0x4000] = symbols["sSaveVersion"][0]
        mem[addr("sSaveVersion"):addr("sSaveVersion") + 2] = [0, 10]
        mem[0x4000] = symbols["sPokemonIndexTableMagic"][0]
        mem[addr("sPokemonIndexTableMagic"):addr("sPokemonIndexTableMagic") + 2] = [0, 0]
        invoke("SaveChecksum")

        # Destroy live Pokemon state, then enter the real primary legacy-load
        # path. Only unrelated storage/mail backup maintenance is bypassed.
        mem[addr("wPokemonData"):addr("wPokemonDataEnd")] = [0xA5] * (
            addr("wPokemonDataEnd") - addr("wPokemonData")
        )
        mem[0xFF70] = 2
        mem[addr("wPokemonIndexTable"):addr("wPokemonIndexTableEnd")] = [0x5A] * (
            addr("wPokemonIndexTableEnd") - addr("wPokemonIndexTable")
        )
        mem[0xFF70] = 1
        for name in ("LoadStorageSystem", "WriteBackupSave"):
            bank, target = symbols[name]
            mem[bank, target] = 0xC9
        bank, target = symbols["RestorePartyMonMail"]
        mem[bank, target] = 0xC9

        invoke("TryLoadSaveFile")
        assert not (regs.F & 0x10), "legacy primary save did not load"
        assert bytes(
            mem[addr("wPokemonDataFormat"):addr("wPokemonDataFormat") + 2]
        ) == bytes([0, 0])
        assert mem[party] == 1
        assert mem[party + form_offset] == 0xE1

        # Exercise the activation-gate converter on data that actually arrived
        # through the real legacy save loader.
        invoke("MigrateLegacyPlayerPokemonData")
        assert bytes(
            mem[addr("wPokemonDataFormat"):addr("wPokemonDataFormat") + 2]
        ) == bytes([0xBC, 0x16])
        transient_slot = mem[party]
        assert transient_slot != 0, "migration produced an empty transient species slot"
        mem[0xFF70] = 2
        mapped_native = int.from_bytes(
            mem[table_entry(transient_slot):table_entry(transient_slot) + 2], "little"
        )
        mem[0xFF70] = 1
        assert mapped_native == native, hex(mapped_native)
        assert mem[party + form_offset] == 0xE1, hex(mem[party + form_offset])

        invoke("GetNativeSpeciesIDFromPokemonDataStruct", hl=party, de=form_offset)
        migrated_native = (regs.B << 8) | regs.C
        assert migrated_native == native, hex(migrated_native)

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

        # Re-save the migrated/hatch-complete party in the native envelope.
        invoke("SavePokemonData")
        invoke("SavePokemonIndexTable")
        invoke("SaveChecksum")

        invoke("VerifyChecksum")
        assert regs.F & 0x80, "native re-save game checksum failed verification"
        invoke("VerifyPokemonIndexTable")
        assert regs.F & 0x80, "native re-save index table failed verification"

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
            "PASS: version-10 legacy save loads through TryLoadSaveFile, migrates $0101 Egg, "
            "hatches it, re-saves a valid native primary envelope, and reloads full identity "
            "with stats/HP, nickname, Egg clear, happiness, OT and status intact"
        )
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
