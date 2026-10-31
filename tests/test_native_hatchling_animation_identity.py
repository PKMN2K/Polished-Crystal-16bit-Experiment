"""Egg hatch reveal re-decodes native party identity after the egg picture."""
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

    # Cover an ordinary root, a full-word root, and mechanical variants from
    # across the table without turning the hatch animation regression into a
    # long exhaustive graphics test.
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

    def word(symbol, value):
        mem[addr(symbol):addr(symbol) + 2] = list(value.to_bytes(2, "little"))

    def patch_ret(symbol):
        bank, target = syms[symbol]
        mem[bank, target] = 0xC9

    captures = []

    try:
        mem[0xFF50] = 1
        mem[0xFFFF] = 0
        mem[0xFF0F] = 0
        mem[0xFF40] = 0
        mem[0xFF70] = 1

        # Keep the real party decoder, hatchling frontpic identity setup, egg
        # identity clobber, and reveal-boundary code. Stub only presentation,
        # timing, sound, and the final animation body.
        for symbol in (
            "PlayMusic",
            "FadeOutPalettes",
            "BlankScreen",
            "DisableLCD",
            "GetCGBLayout",
            "FarCopyBytes",
            "ClearSpriteAnims",
            "PrepareAnimatedFrontpic",
            "GetFrontpic",
            "Hatch_UpdateFrontpicBGMapCenter",
            "DelayFrames",
            "EggHatch_DoAnimFrame",
            "EggHatch_CrackShell",
            "PlaySFX",
            "ClearSprites",
            "Hatch_InitShellFragments",
            "Hatch_ShellFragmentLoop",
            "WaitSFX",
            "EnableLCD",
            "AnimateFrontpic",
        ):
            patch_ret(symbol)

        anim_bank, anim_at = syms["AnimateFrontpic"]

        def capture(_):
            captures.append(
                (
                    mem[addr("wCurSpecies")],
                    mem[addr("wCurPartySpecies")],
                    mem[addr("wCurForm")],
                )
            )

        pyboy.hook_register(anim_bank, anim_at, capture, None)

        start = addr("wPartyMon1Species")
        stride = addr("wPartyMon2Species") - start
        form_offset = addr("wPartyMon1Form") - start
        count = 0

        for native, base, mechanical_form in samples:
            for marker in (0, 0x16BC, 0x00BC, 0x1600):
                raw_form = 1 if marker == 0x16BC else mechanical_form
                metadata = 0xC0
                for slot in range(6):
                    context = (native, base, mechanical_form, marker, slot)
                    word("wPokemonDataFormat", marker)

                    # Transient species 7 maps through slot six (zero-based)
                    # when the native marker is valid.
                    mem[0xFF70] = 2
                    entry = addr("wPokemonIndexTableEntries") + 12
                    mem[entry:entry + 2] = list(native.to_bytes(2, "little"))
                    mem[0xFF70] = 1

                    mem[start:start + 6 * stride] = [0xA5] * (6 * stride)
                    record = start + slot * stride
                    mem[record] = 7 if marker == 0x16BC else base & 0xFF
                    encoded = raw_form | metadata
                    if marker != 0x16BC:
                        encoded |= (base >> 8) << 5
                    mem[record + form_offset] = encoded

                    put("wCurPartyMon", slot)
                    put("wPartyCount", 6)
                    put("wNamedObjectIndex", base & 0xFF)
                    put("wCurSpecies", 91)
                    put("wCurPartySpecies", 92)
                    put("wCurForm", 3)

                    previous = len(captures)

                    bank, target = syms["EggHatch_AnimationSequence"]
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
                    regs.SP = 0xC0FF
                    regs.PC = 0xC100
                    pyboy.tick(4, False, False)

                    assert (regs.PC, regs.SP) == (0xC104, 0xC0FF), (
                        context,
                        hex(regs.PC),
                        hex(regs.SP),
                    )
                    assert len(captures) == previous + 1, context

                    expected_form = (
                        mechanical_form if native != base else raw_form & 0x1F
                    ) | ((base >> 8) << 5)
                    assert captures[-1] == (
                        base & 0xFF,
                        base & 0xFF,
                        expected_form,
                    ), (context, captures[-1])

                    # EggHatch_AnimationSequence restores the caller's
                    # wCurSpecies after the reveal.
                    assert mem[addr("wCurSpecies")] == 91, context
                    assert mem[addr("wCurPartySpecies")] == base & 0xFF, context
                    assert mem[addr("wCurForm")] == expected_form, context
                    count += 1

        print(
            f"PASS: {count} hatchling reveal identity cases; "
            "native/legacy/partial markers, full-word roots, mechanical variants, "
            "all six party slots, egg-picture form clobber, and caller species restore"
        )
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
