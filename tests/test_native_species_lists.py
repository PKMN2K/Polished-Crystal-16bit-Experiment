"""Bank-aware legendary lists and native Battle Tower party eligibility."""
import argparse
from pathlib import Path

from pyboy import PyBoy


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom", type=Path)
    rom = ap.parse_args().rom
    syms = {}
    for line in rom.with_suffix(".sym").read_text().splitlines():
        fields = line.split()
        if len(fields) == 2 and ":" in fields[0]:
            syms[fields[1]] = tuple(int(v, 16) for v in fields[0].split(":"))

    def addr(label):
        return syms[label][1]

    def offset(label):
        bank, address = syms[label]
        return bank * 0x4000 + address - (0x4000 if bank else 0)

    data = rom.read_bytes()
    root = Path(__file__).resolve().parents[1]
    nvariants = sum(line.strip().startswith("native_variant_identity ")
                    for line in (root / "data/pokemon/native_variant_name_roots.asm").read_text().splitlines())
    table = offset("NativeVariantIdentityTable")
    variants = []
    for p in range(table, table + 5 * nvariants, 5):
        native = int.from_bytes(data[p:p + 2], "little")
        species = int.from_bytes(data[p + 2:p + 4], "little")
        variants.append((native, species & 255, data[p + 4] | ((species >> 8) << 5)))
    cases = [(n, n & 255, 1 | ((n >> 8) << 5))
             for n in (144, 145, 146, 243, 244, 245, 150, 151, 249, 250, 251, 25, 256, 257)]
    cases += variants
    banned = {150, 151, 249, 250, 251}
    legendary = banned | {144, 145, 146, 243, 244, 245}
    pyboy = PyBoy(str(rom), window="null", sound_emulated=False,
                  cgb=True, log_level="ERROR")
    mem, regs = pyboy.memory, pyboy.register_file

    def invoke(label):
        bank, target = syms[label]
        mem[0x2000] = bank
        mem[addr("hROMBank")] = bank
        mem[0xC100:0xC106] = [0xF3, 0xCD, target & 255, target >> 8, 0x18, 0xFE]
        regs.SP, regs.PC = 0xC0FF, 0xC100
        pyboy.tick(2, False, False)
        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF), label
        assert mem[addr("hROMBank")] == bank, label
        assert mem[0xFF70] & 7 == 1, label
        return bool(regs.F & 0x10)

    try:
        mem[0xFF50] = 1
        mem[0xFFFF] = mem[0xFF0F] = mem[0xFF40] = 0
        mem[0xFF70] = 1
        list_cases = 0
        for list_name, members in (("LegendaryMons", legendary), ("UberMons", banned)):
            for native, species, form in cases:
                for metadata in (0, 0x80):
                    regs.A = syms[list_name][0]
                    regs.B, regs.C = form | metadata, species
                    regs.D, regs.E, regs.HL = 0x56, 0x78, addr(list_name)
                    actual = invoke("IsLegacySpeciesInNativeList")
                    assert actual == (native in members), (list_name, native, form, actual)
                    assert (regs.D, regs.E) == (0x56, 0x78)
                    list_cases += 1

        stride = addr("wPartyMon2Species") - addr("wPartyMon1Species")
        party = addr("wPartyMon1Species")
        table_start = addr("wPokemonIndexTableEntries")
        tower_cases = 0
        # Keep the live eligibility checks focused on roots and one variant;
        # the list adapter above exercises the complete mechanical catalog.
        tower_identities = cases[:14] + variants[:1]
        for marker in (0, 0x16BC, 0x00BC, 0x1600):
            for native, species, form in tower_identities:
                mem[0xFF70] = 2
                mem[table_start:table_start + 254] = [0] * 254
                mem[table_start + 12:table_start + 14] = list(native.to_bytes(2, "little"))
                mem[addr("wPokemonIndexTableUsedSlots")] = 1
                table_before = bytes(mem[table_start:table_start + 254])
                mem[0xFF70] = 1
                mem[addr("wPokemonDataFormat"):addr("wPokemonDataFormat") + 2] = list(marker.to_bytes(2, "little"))
                for slot in range(6):
                    for egg in (False, True):
                        mem[party:party + 6 * stride] = [0] * (6 * stride)
                        record = party + slot * stride
                        mem[record] = 7 if marker == 0x16BC else species
                        form_addr = addr("wPartyMon1Form") + slot * stride
                        # Marked records must ignore a deliberately conflicting
                        # compact identity form; gender and Egg flags survive.
                        mem[form_addr] = (1 if marker == 0x16BC else form) | 0x80 | (0x40 if egg else 0)
                        mem[addr("wBT_PartySelectCounter")] = 0
                        party_before = bytes(mem[party:party + 6 * stride])
                        regs.A = slot
                        regs.B, regs.C, regs.D, regs.E, regs.HL = 0x12, 0x34, 0x56, 0x78, 0xC222
                        actual = invoke("BT_CheckEnterState")
                        expected = egg or native in banned
                        assert actual == expected, (hex(marker), native, slot, egg, actual)
                        assert regs.F & 0x80, ("unentered/banned must return Z", native)
                        assert (regs.B, regs.C, regs.D, regs.E, regs.HL) == (0x12, 0x34, 0x56, 0x78, 0xC222)
                        assert bytes(mem[party:party + 6 * stride]) == party_before
                        mem[0xFF70] = 2
                        assert bytes(mem[table_start:table_start + 254]) == table_before
                        mem[0xFF70] = 1
                        tower_cases += 1
        print(f"PASS: {list_cases} bank-aware legendary/Uber list cases and {tower_cases} "
              "native Battle Tower eligibility cases; both formats, all six slots, "
              "Egg exclusions, variants, register/record/table preservation")
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
