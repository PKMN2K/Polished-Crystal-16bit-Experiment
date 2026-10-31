"""Run the real hatch-time stat calculator for an extended native root."""
import argparse
from pathlib import Path

from pyboy import PyBoy


LEVEL = 5
DV = 15


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

    pyboy = PyBoy(
        str(rom),
        window="null",
        sound_emulated=False,
        cgb=True,
        log_level="ERROR",
    )
    mem, regs = pyboy.memory, pyboy.register_file

    party = addr("wPartyMon1Species")
    form_offset = addr("wPartyMon1Form") - party
    level_offset = addr("wPartyMon1Level") - party
    ev_offset = addr("wPartyMon1EVs") - party
    dv_offset = addr("wPartyMon1DVs") - party
    hp_offset = addr("wPartyMon1HP") - party
    maxhp_offset = addr("wPartyMon1MaxHP") - party
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

    def words_from_record(start, count):
        result = []
        for i in range(count):
            p = start + i * 2
            result.append((mem[p] << 8) | mem[p + 1])
        return result

    def invoke_update():
        bank, target = symbols["UpdatePkmnStats"]
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

    def run_case(native):
        # Native-format party record. Deliberately poison the legacy species byte
        # so the full transient ID is the only correct source of identity.
        mem[addr("wPokemonDataFormat"):addr("wPokemonDataFormat") + 2] = [0xBC, 0x16]
        mem[0xFF70] = 2
        entry = addr("wPokemonIndexTableEntries") + 12
        mem[entry:entry + 2] = list(native.to_bytes(2, "little"))
        mem[0xFF70] = 1

        mem[party:party + (addr("wPartyMon2Species") - party)] = [0] * (
            addr("wPartyMon2Species") - party
        )
        mem[party] = 7
        mem[party + form_offset] = 1
        mem[party + level_offset] = LEVEL
        mem[party + ev_offset:party + ev_offset + 6] = [0] * 6
        mem[party + dv_offset:party + dv_offset + 3] = [0xFF] * 3
        mem[party + nature_offset] = 0

        # A nonzero current HP lets UpdatePkmnStats take its normal HP-adjust path.
        mem[party + hp_offset:party + hp_offset + 2] = [0, 20]
        mem[party + maxhp_offset:party + maxhp_offset + 12] = [0] * 12
        mem[party + maxhp_offset:party + maxhp_offset + 2] = [0, 20]

        mem[addr("wCurPartyMon")] = 0
        mem[addr("wPartyCount")] = 1
        mem[addr("wInitialOptions")] = 0
        mem[addr("wInitialOptions2")] = 0
        mem[addr("wCurSpecies")] = 91
        mem[addr("wCurPartySpecies")] = 92
        mem[addr("wCurForm")] = 3

        invoke_update()

        return {
            "stats": words_from_record(party + maxhp_offset, 6),
            "hp": (mem[party + hp_offset] << 8) | mem[party + hp_offset + 1],
            "species": mem[addr("wCurSpecies")],
            "party_species": mem[addr("wCurPartySpecies")],
            "form": mem[addr("wCurForm")],
            "base": bytes(mem[addr("wCurBaseData"):addr("wCurBaseDataEnd")]),
        }

    try:
        mem[0xFF50] = 1
        mem[0xFFFF] = 0
        mem[0xFF0F] = 0
        mem[0xFF40] = 0
        mem[0xFF70] = 1

        ordinary = run_case(0x0001)
        extended = run_case(0x0101)

        ordinary_expected = expected_stats(0x0001)
        extended_expected = expected_stats(0x0101)

        assert ordinary["stats"] == ordinary_expected, (ordinary, ordinary_expected)
        assert extended["stats"] == extended_expected, (extended, extended_expected)
        assert extended["stats"] != ordinary_expected, (
            "extended root collapsed to low-byte stats",
            extended["stats"],
            ordinary_expected,
        )

        # Current HP should gain exactly the max-HP increase from the seeded 20.
        assert ordinary["hp"] == ordinary_expected[0], ordinary
        assert extended["hp"] == extended_expected[0], extended

        assert (ordinary["species"], ordinary["party_species"], ordinary["form"]) == (1, 1, 1)
        assert (extended["species"], extended["party_species"], extended["form"]) == (1, 1, 0x21)

        ext_base = data[
            base_start + 0x0100 * base_size:
            base_start + 0x0101 * base_size
        ]
        assert extended["base"] == ext_base

        print(
            "PASS: real hatch-time UpdatePkmnStats distinguishes native $0101 from $0001; "
            "exact six stats, HP adjustment, decoded identity, and native base data"
        )
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
