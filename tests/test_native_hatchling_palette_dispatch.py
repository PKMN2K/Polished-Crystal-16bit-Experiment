"""Hatch palette dispatch preserves decoded native hatchling identity."""
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

    # Ordinary low-byte root, an extended root, and representative mechanical
    # variants exercise both halves of the species/form palette identity.
    samples = [(25, 25, 1), (257, 257, 1)]
    if variants:
        for index in sorted({0, len(variants) // 2, len(variants) - 1}):
            samples.append(variants[index])

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

    def patch_ret(symbol):
        patch_bank, patch_at = syms[symbol]
        mem[patch_bank, patch_at] = 0xC9

    captures = []

    try:
        mem[0xFF50] = 1
        mem[0xFFFF] = 0
        mem[0xFF0F] = 0
        mem[0xFF40] = 0
        mem[0xFF70] = 1

        # Keep Hatch_LoadFrontpicPal and the real CGB dispatcher. Skip palette
        # clearing and stop exactly when the dispatcher reaches the evolution
        # layout so the handoff can be inspected without presentation work.
        patch_ret("ResetBGPals")
        evolution_bank, evolution_at = syms["_CGB_Evolution"]
        mem[evolution_bank, evolution_at] = 0xC9

        def capture(_):
            captures.append(
                (
                    regs.C,
                    mem[addr("wPlayerHPPal")],
                    mem[addr("wCurSpecies")],
                    mem[addr("wCurPartySpecies")],
                    mem[addr("wCurForm")],
                )
            )

        pyboy.hook_register(evolution_bank, evolution_at, capture, None)

        count = 0
        for native, base, mechanical_form in samples:
            low = base & 0xFF
            form = mechanical_form | ((base >> 8) << 5)
            context = (native, base, mechanical_form)

            put("wPlayerHPPal", 0xEE)
            put("wCurSpecies", low)
            put("wCurPartySpecies", low)
            put("wCurForm", form)
            previous = len(captures)

            bank, target = syms["Hatch_LoadFrontpicPal"]
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
            regs.A = low
            regs.SP = 0xC0FF
            regs.PC = 0xC100
            pyboy.tick(4, False, False)

            assert (regs.PC, regs.SP) == (0xC104, 0xC0FF), (
                context,
                hex(regs.PC),
                hex(regs.SP),
            )
            assert len(captures) == previous + 1, context
            assert captures[-1] == (2, low, low, low, form), (
                context,
                captures[-1],
            )
            count += 1

        print(
            f"PASS: {count} hatchling palette-dispatch identity cases; "
            "real CGB layout dispatch, low-byte and extended roots, representative "
            "mechanical variants, and unchanged species/form handoff"
        )
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
