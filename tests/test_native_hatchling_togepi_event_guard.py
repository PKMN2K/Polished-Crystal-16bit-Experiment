"""The Togepi hatch event guard must reject an extended species sharing Togepi's low byte."""
import argparse
from pathlib import Path

from pyboy import PyBoy


TOGEPI = 0xAF
EXTSPECIES_MASK = 0x20


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

    pyboy = PyBoy(
        str(rom),
        window="null",
        sound_emulated=False,
        cgb=True,
        log_level="ERROR",
    )
    mem, regs = pyboy.memory, pyboy.register_file

    def compare(species, form):
        bank, target = symbols["CompareSpeciesWithDE"]
        assert bank == 0, bank

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

        regs.B = form
        regs.C = species
        regs.D = 0
        regs.E = TOGEPI
        regs.SP = 0xC0FF
        regs.PC = 0xC100

        pyboy.tick(4, False, False)

        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF), (
            hex(regs.PC),
            hex(regs.SP),
        )
        return bool(regs.F & 0x80)  # Z flag means the hatch identity matches Togepi.

    try:
        mem[0xFF50] = 1
        mem[0xFFFF] = 0
        mem[0xFF0F] = 0
        mem[0xFF40] = 0
        mem[0xFF70] = 1

        # The hatch event intentionally accepts any ordinary Togepi form.
        for form in (0x00, 0x01, 0x05, 0x1F):
            assert compare(TOGEPI, form), ("ordinary Togepi rejected", form)

        # A native root $01AF has the same low species byte but must never
        # trigger EVENT_TOGEPI_HATCHED.
        for form in (EXTSPECIES_MASK, EXTSPECIES_MASK | 0x01, EXTSPECIES_MASK | 0x1F):
            assert not compare(TOGEPI, form), ("extended alias matched Togepi", form)

        # A neighboring ordinary species must also remain a non-match.
        assert not compare(TOGEPI - 1, 0), "neighbor species matched Togepi"

        print(
            "PASS: Togepi hatch-event identity guard accepts ordinary Togepi forms "
            "and rejects native $01AF plus neighboring species"
        )
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
