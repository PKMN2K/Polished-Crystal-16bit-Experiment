"""Hatchling Dex registration keeps the temporary mon's extended native identity distinct."""
import argparse
from pathlib import Path

from pyboy import PyBoy


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

    def invoke_home(name):
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
        regs.SP = 0xC0FF
        regs.PC = 0xC100
        pyboy.tick(4, False, False)
        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF), (
            name,
            hex(regs.PC),
            hex(regs.SP),
        )
        return not bool(regs.F & 0x80)  # NZ means the Dex flag is set.

    def register_from_tempmon():
        bank, target = symbols["SetSeenAndCaughtMon"]
        assert bank == 0, bank
        species = addr("wTempMonSpecies")
        form = addr("wTempMonForm")

        # Exact HatchEggs handoff:
        #   ld a,[wTempMonSpecies] / ld c,a
        #   ld a,[wTempMonForm]    / ld b,a
        #   call SetSeenAndCaughtMon
        stub = [
            0xFA,
            species & 0xFF,
            species >> 8,
            0x4F,
            0xFA,
            form & 0xFF,
            form >> 8,
            0x47,
            0xCD,
            target & 0xFF,
            target >> 8,
            0x18,
            0xFE,
        ]
        mem[0x2000] = 1
        mem[addr("hROMBank")] = 1
        mem[0xC100:0xC100 + len(stub)] = stub
        regs.SP = 0xC0FF
        regs.PC = 0xC100
        pyboy.tick(4, False, False)
        assert (regs.PC, regs.SP) == (0xC10B, 0xC0FF), (
            hex(regs.PC),
            hex(regs.SP),
        )

    def check(name, species, form):
        regs.B = form
        regs.C = species
        return invoke_home(name)

    try:
        mem[0xFF50] = 1
        mem[0xFFFF] = 0
        mem[0xFF0F] = 0
        mem[0xFF40] = 0
        mem[0xFF70] = 1

        flags_start = addr("wPokedexCaught")
        flags_end = addr("wEndPokedexFlags")

        cases = [
            # Ordinary root and the first extended root sharing low byte 1.
            (25, 0x01, None),
            (1, 0x21, (1, 0x01)),
        ]

        tested = 0
        for species, form, alias in cases:
            mem[flags_start:flags_end] = [0] * (flags_end - flags_start)
            mem[addr("wDexCacheValid")] = 1
            mem[addr("wTempMonSpecies")] = species
            mem[addr("wTempMonForm")] = form

            register_from_tempmon()

            assert mem[addr("wDexCacheValid")] == 0, (species, form)
            assert check("CheckCaughtMon", species, form), ("caught", species, form)
            assert check("CheckSeenMon", species, form), ("seen", species, form)

            if alias is not None:
                alias_species, alias_form = alias
                assert not check("CheckCaughtMon", alias_species, alias_form), (
                    "caught alias",
                    species,
                    form,
                    alias,
                )
                assert not check("CheckSeenMon", alias_species, alias_form), (
                    "seen alias",
                    species,
                    form,
                    alias,
                )

            tested += 1

        print(
            f"PASS: {tested} hatchling Dex-registration cases; "
            "exact HatchEggs temp-mon handoff, caught+seen writes, "
            "Dex-cache invalidation, and species $0101 kept distinct from $0001"
        )
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
