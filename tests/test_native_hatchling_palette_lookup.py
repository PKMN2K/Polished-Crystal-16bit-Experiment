"""Hatchling palette lookup resolves the temp-mon native species/form identity."""
import argparse
from pathlib import Path

from pyboy import PyBoy


PALETTE_ENTRY_SIZE = 8


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom", type=Path)
    rom = ap.parse_args().rom

    syms = {}
    for line in rom.with_suffix(".sym").read_text().splitlines():
        fields = line.split()
        if len(fields) == 2 and ":" in fields[0]:
            syms[fields[1]] = tuple(int(v, 16) for v in fields[0].split(":"))

    def addr(symbol):
        return syms[symbol][1]

    root = Path(__file__).resolve().parents[1]
    data = rom.read_bytes()
    bank, at = syms["NativeVariantIdentityTable"]
    pos = bank * 0x4000 + at - 0x4000
    variant_count = sum(
        line.strip().startswith("native_variant_identity ")
        for line in (root / "data/pokemon/native_variant_name_roots.asm").read_text().splitlines()
    )
    variants = [
        (
            int.from_bytes(data[p:p + 2], "little"),
            int.from_bytes(data[p + 2:p + 4], "little"),
            data[p + 4],
        )
        for p in range(pos, pos + 5 * variant_count, 5)
    ]

    samples = [(25, 25, 1), (257, 257, 1)]
    if variants:
        for index in sorted({0, len(variants) // 2, len(variants) - 1}):
            samples.append(variants[index])

    palette_bank, palette_base = syms["PokemonPaletteData"]

    pyboy = PyBoy(
        str(rom),
        window="null",
        sound_emulated=False,
        cgb=True,
        log_level="ERROR",
    )
    mem, regs = pyboy.memory, pyboy.register_file

    def put(symbol, value):
        mem[addr(symbol)] = value

    try:
        mem[0xFF50] = 1
        mem[0xFFFF] = 0
        mem[0xFF0F] = 0
        mem[0xFF40] = 0
        mem[0xFF70] = 1

        count = 0
        personality = addr("wTempMonPersonality")

        for native, base, mechanical_form in samples:
            for metadata in (0, 0x40, 0x80, 0xC0):
                context = (native, base, mechanical_form, metadata)

                # The hatch palette path points BC at wTempMonPersonality.
                # Its following byte is the decoded temporary form byte.
                mem[personality] = 0  # non-shiny
                mem[personality + 1] = (
                    mechanical_form
                    | ((base >> 8) << 5)
                    | metadata
                )

                # Stale globals must not affect this lookup; the evolution
                # layout uses the species byte supplied in A plus temp-mon form.
                put("wCurSpecies", 91)
                put("wCurPartySpecies", 92)
                put("wCurForm", 3)

                bank, target = syms["GetPlayerOrMonPalettePointer"]
                mem[0x2000] = bank
                put("hROMBank", bank)
                mem[0xC100:0xC106] = [
                    0xF3,
                    0xCD,
                    target & 0xFF,
                    target >> 8,
                    0x18,
                    0xFE,
                ]

                regs.A = base & 0xFF
                regs.B = personality >> 8
                regs.C = personality & 0xFF
                regs.SP = 0xC0FF
                regs.PC = 0xC100
                pyboy.tick(4, False, False)

                assert (regs.PC, regs.SP) == (0xC104, 0xC0FF), (
                    context,
                    hex(regs.PC),
                    hex(regs.SP),
                )

                expected = palette_base + native * PALETTE_ENTRY_SIZE
                assert syms["PokemonPaletteData"][0] == palette_bank, context
                assert regs.HL == expected, (
                    context,
                    hex(regs.HL),
                    hex(expected),
                )
                assert (regs.B << 8 | regs.C) == personality, context
                assert mem[addr("wCurSpecies")] == 91, context
                assert mem[addr("wCurPartySpecies")] == 92, context
                assert mem[addr("wCurForm")] == 3, context
                count += 1

        print(
            f"PASS: {count} hatchling temp-mon palette lookup cases; "
            "low-byte and extended roots, representative mechanical variants, "
            "metadata masking, exact native palette pointers, and stale-global independence"
        )
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
