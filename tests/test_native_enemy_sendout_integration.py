"""Focused enemy send-out integration regression for native species identity.

Execute the real top-level trainer enemy send-out helper far enough to cover:
1. the real temporary-record bridge,
2. real native front-picture decode + VRAM transfer, and
3. the real native battle-animation record setup.

Only unrelated presentation/audio helpers and the animation tick are stubbed.
The test intentionally keeps the LCD off because Request2bpp/VBlank scheduling
is covered separately; this regression checks that send-out joins the already
validated native picture and animation paths without losing the 16-bit shadow.
"""
import argparse
import hashlib
from pathlib import Path

from pyboy import PyBoy


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom", type=Path)
    rom = ap.parse_args().rom

    symbols = {}
    for line in rom.with_suffix(".sym").read_text().splitlines():
        fields = line.split()
        if len(fields) == 2 and ":" in fields[0]:
            symbols[fields[1]] = tuple(int(v, 16) for v in fields[0].split(":"))

    def addr(label):
        return symbols[label][1]

    def offset(label):
        bank, address = symbols[label]
        return bank * 0x4000 + address - (0x4000 if bank else 0)

    data = rom.read_bytes()
    root = Path(__file__).resolve().parents[1]
    nvariants = sum(
        line.strip().startswith("native_variant_identity ")
        for line in (root / "data/pokemon/native_variant_name_roots.asm").read_text().splitlines()
    )
    table = offset("NativeVariantIdentityTable")
    variants = []
    for p in range(table, table + 5 * nvariants, 5):
        native = int.from_bytes(data[p:p + 2], "little")
        species = int.from_bytes(data[p + 2:p + 4], "little")
        variants.append((
            native,
            0xFF,
            species & 0xFF,
            data[p + 4] | ((species >> 8) << 5),
        ))
    assert len(variants) >= 2, "Need at least two regional variants"

    cases = [
        (25, 0xE1, 25, 1),
        (257, 1, 1, 0x21),
        (201, 0xE2, 201, 2),
        (25, 3, 25, 3),
        (26, 2, 26, 1),
    ] + variants[:2]

    pyboy = PyBoy(
        str(rom), window="null", sound_emulated=False, cgb=True, log_level="ERROR"
    )
    mem, regs = pyboy.memory, pyboy.register_file

    stride = addr("wOTPartyMon2Species") - addr("wOTPartyMon1Species")
    form_offset = addr("wOTPartyMon1Form") - addr("wOTPartyMon1Species")
    base_start, base_end = addr("wCurBaseData"), addr("wCurBaseDataEnd")
    base_len = base_end - base_start

    v0_start = addr("vTiles2")
    v0_end = v0_start + 7 * 7 * 16
    v1_start = addr("vTiles4")
    v1_end = addr("vBGMap2")
    v1_base_offset = addr("vTiles5") - v1_start

    anim_bank = symbols["wPokeAnimStruct"][0] & 7

    legacy_calls = []
    native_base_calls = []
    picture_calls = []
    animation_calls = []
    sendout_anim_calls = []
    ticks = []

    def read_anim(label):
        old = mem[0xFF70]
        mem[0xFF70] = anim_bank
        try:
            return mem[addr(label)]
        finally:
            mem[0xFF70] = old

    def install_stub(label, opcodes, callback=None):
        bank, address = symbols[label]
        for i, value in enumerate(opcodes):
            mem[bank, address + i] = value
        if callback is not None:
            pyboy.hook_register(bank, address, callback, None)

    def clear_vram():
        mem[0xFF4F] = 0
        mem[v0_start:v0_end] = [0x5A] * (v0_end - v0_start)
        mem[0xFF4F] = 1
        mem[v1_start:v1_end] = [0x5A] * (v1_end - v1_start)
        mem[0xFF4F] = 0

    def snapshot_vram():
        old = mem[0xFF4F] & 1
        mem[0xFF4F] = 0
        front = bytes(mem[v0_start:v0_end])
        mem[0xFF4F] = 1
        animated = bytes(mem[v1_start:v1_end])
        mem[0xFF4F] = old
        return front, animated

    def prepare_case(native, raw_form, slot):
        mem[0xFF70] = 1
        mem[0xFF4F] = 0
        mem[0xFF40] = 0  # direct VRAM copies; LCD-on scheduler has its own test
        mem[0xFFFF] = 0
        mem[0xFF0F] = 0

        mem[addr("hBattleTurn")] = 1
        mem[addr("wBattleType")] = 0
        mem[addr("wDeferredSwitch")] = 0
        mem[addr("wEnemySubStatus4")] = 0
        mem[addr("wCurPartyMon")] = slot
        mem[addr("wCurOTMon")] = slot
        mem[addr("wEnemyMonSpecies")] = 59
        mem[addr("wEnemyMonForm")] = raw_form
        mem[addr("wBattleMonNativeSpecies"):addr("wBattleMonNativeSpecies") + 2] = [143, 0]
        mem[addr("wEnemyMonNativeSpecies"):addr("wEnemyMonNativeSpecies") + 2] = list(
            native.to_bytes(2, "little")
        )

        # Deliberately conflicting legacy opponent-party identity. The native
        # active shadow must still choose the picture/base data/animation record.
        source = addr("wOTPartyMon1Species") + slot * stride
        record = [((i * 19) + slot * 7 + 3) & 0xFF for i in range(stride)]
        record[0] = 59
        record[form_offset] = 0
        mem[source:source + stride] = record

        mem[addr("wCurSpecies")] = 91
        mem[addr("wCurPartySpecies")] = 92
        mem[addr("wCurForm")] = 0x23
        mem[addr("wBoxAlignment")] = 0
        mem[addr("wMonPicSize")] = 0
        mem[addr("wMonAnimationSize")] = 0
        mem[base_start:base_end] = [0xA5] * base_len

        mem[0xFF70] = anim_bank
        for label in (
            "wPokeAnimSpecies",
            "wPokeAnimVariant",
            "wPokeAnimFrontpicHeight",
            "wPokeAnimGraphicStartTile",
        ):
            mem[addr(label)] = 0xA5
        mem[0xFF70] = 1
        clear_vram()

        legacy_calls.clear()
        native_base_calls.clear()
        picture_calls.clear()
        animation_calls.clear()
        sendout_anim_calls.clear()
        ticks.clear()

    def invoke_sendout():
        bank, target = symbols["Function_SetEnemyPkmnAndSendOutAnimation"]
        mem[0x2000] = bank
        mem[addr("hROMBank")] = bank
        mem[0xC100:0xC106] = [
            0xF3, 0xCD, target & 0xFF, target >> 8, 0x18, 0xFE
        ]
        regs.SP, regs.PC = 0xC0FF, 0xC100
        for _ in range(48):
            pyboy.tick(1, False, False)
            if (regs.PC, regs.SP) == (0xC104, 0xC0FF):
                break
        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF), (
            hex(regs.PC), hex(regs.SP)
        )
        assert mem[addr("hROMBank")] == bank
        assert mem[0xFF70] & 7 == 1
        assert mem[0xFF4F] & 1 == 0

    count = 0
    digests = []
    try:
        mem[0xFF50] = 1
        mem[0xFF40] = 0
        mem[0xFF70] = 1
        mem[0xFF4F] = 0

        # Presentation/audio helpers are outside this regression. Each stub
        # returns exactly the condition the normal send-out path needs.
        install_stub(
            "PlayBattleAnimDE", [0xC9],
            lambda _: sendout_anim_calls.append((regs.D << 8) | regs.E)
        )
        install_stub("BattleCheckEnemyShininess", [0xA7, 0xC9])  # clear carry
        install_stub("ResetVariableBattleMusicCondition", [0xC9])
        install_stub("CheckFaintedFrzSlp", [0xA7, 0xC9])  # clear carry
        install_stub("CheckBattleEffects", [0xA7, 0xC9])  # clear carry
        install_stub("UpdateEnemyHUD", [0xC9])
        install_stub("TickPokeAnim", [0x37, 0xC9], lambda _: ticks.append(True))

        # Observe, but do not replace, the native integration points.
        for label, dest in (
            ("GetBaseData", legacy_calls),
            ("GetBaseDataFromEnemyBattleNativeSpecies", native_base_calls),
            ("PrepareNativeEnemyBattleAnimatedFrontpic", picture_calls),
            ("AnimateNativeEnemyBattleFrontpic", animation_calls),
        ):
            bank, address = symbols[label]
            pyboy.hook_register(bank, address, lambda _, d=dest: d.append(True), None)

        for slot in (0, 2):
            for native, raw_form, species, form in cases:
                prepare_case(native, raw_form, slot)
                shadow_before = bytes(
                    mem[addr("wEnemyMonNativeSpecies"):addr("wEnemyMonNativeSpecies") + 2]
                )
                expected_base = bytes(data[
                    offset("BaseDataRecords") + (native - 1) * base_len:
                    offset("BaseDataRecords") + native * base_len
                ])

                invoke_sendout()
                front, animated = snapshot_vram()
                context = (slot, native, raw_form)

                assert bytes(
                    mem[addr("wEnemyMonNativeSpecies"):addr("wEnemyMonNativeSpecies") + 2]
                ) == shadow_before, ("native shadow changed", context)
                assert not legacy_calls, ("send-out used legacy GetBaseData", context)
                assert picture_calls == [True], ("native picture path count", context, picture_calls)
                assert animation_calls == [True], (
                    "native animation path count", context, animation_calls
                )
                assert len(native_base_calls) >= 3, (
                    "native base-data path did not span send-out/picture/animation",
                    context, len(native_base_calls)
                )
                assert len(sendout_anim_calls) == 1, (
                    "unexpected send-out ball animation count", context, sendout_anim_calls
                )
                assert ticks == [True], ("animation record was not entered", context, ticks)
                assert bytes(mem[base_start:base_end]) == expected_base, (
                    "final base data mismatch", context
                )

                assert front != bytes([0x5A] * len(front)), (
                    "front picture did not reach VRAM", context
                )
                base_anim = animated[
                    v1_base_offset:v1_base_offset + len(front)
                ]
                assert base_anim != bytes([0x5A] * len(base_anim)), (
                    "animated base frame did not reach VBK1:vTiles5", context
                )

                assert read_anim("wPokeAnimSpecies") == species, (
                    "animation species mismatch", context,
                    read_anim("wPokeAnimSpecies"), species
                )
                assert read_anim("wPokeAnimVariant") == form, (
                    "animation form mismatch", context,
                    read_anim("wPokeAnimVariant"), form
                )
                assert read_anim("wPokeAnimFrontpicHeight") != 0xA5, (
                    "animation dimensions were not recorded", context
                )
                assert read_anim("wPokeAnimGraphicStartTile") == 0, (
                    "battle animation start tile changed", context
                )
                assert mem[addr("hBattleTurn")] == 1, context
                assert mem[addr("wEnemyMonSpecies")] == 59, context
                assert mem[addr("wEnemyMonForm")] == raw_form, context

                digests.append(hashlib.sha256(front + animated).hexdigest()[:12])
                count += 1

        print(
            f"PASS: {count} native enemy send-out integration cases; "
            f"VRAM digests {', '.join(digests[:4])}"
        )
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
