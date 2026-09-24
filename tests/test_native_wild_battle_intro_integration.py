"""Focused wild-battle introduction integration regression.

Drive the live wild branches of InitEnemy and BattleStartMessage in sequence.
Wild-mon generation itself is stubbed so the fixture can inject ordinary,
extended, cosmetic and mechanical-variant legacy opponent records deterministically.
After that boundary the real SendInUserPkmn native-shadow publication, native
front-picture preparation/LZ decode/direct VRAM copies, BattleAnimateFrontpic
native dispatch, and native animation-record setup remain real.

This is not a full interactive battle test. UI/text/audio helpers and the final
animation tick are stubbed so the CPU harness can stop at the integration point.
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
            species & 0xFF,
            data[p + 4] | ((species >> 8) << 5),
        ))
    assert len(variants) >= 2, "Need at least two regional variants"

    # Each tuple is (native ID expected after SendInUserPkmn,
    # legacy opponent species byte, encoded legacy form byte).
    cases = [
        (25, 25, 1),       # ordinary root with cosmetic presentation
        (257, 1, 0x21),    # root above $00ff
        (201, 201, 2),     # ordinary root with another cosmetic overlay
        (25, 25, 3),
    ] + variants[:2]

    pyboy = PyBoy(
        str(rom), window="null", sound_emulated=False,
        cgb=True, log_level="ERROR"
    )
    mem, regs = pyboy.memory, pyboy.register_file

    stride = addr("wPartyMon2Species") - addr("wPartyMon1Species")
    form_offset = addr("wOTPartyMon1Form") - addr("wOTPartyMon1Species")
    base_start, base_end = addr("wCurBaseData"), addr("wCurBaseDataEnd")
    base_len = base_end - base_start
    anim_bank = symbols["wPokeAnimStruct"][0] & 7

    v0_start = addr("vTiles2")
    v0_end = v0_start + 7 * 7 * 16
    v1_start = addr("vTiles4")
    v1_end = addr("vBGMap2")
    v1_base_offset = addr("vTiles5") - v1_start

    load_wild_calls = []
    picture_calls = []
    animation_calls = []
    native_base_calls = []
    legacy_calls = []
    ticks = []
    placed = []

    def install_stub(label, opcodes, callback=None):
        bank, address = symbols[label]
        for i, value in enumerate(opcodes):
            mem[bank, address + i] = value
        if callback is not None:
            pyboy.hook_register(bank, address, callback, None)

    def call(label, max_frames=48):
        bank, target = symbols[label]
        mem[0x2000] = bank
        mem[addr("hROMBank")] = bank
        mem[0xC100:0xC106] = [
            0xF3, 0xCD, target & 0xFF, target >> 8, 0x18, 0xFE
        ]
        regs.SP, regs.PC = 0xC0FF, 0xC100
        for _ in range(max_frames):
            pyboy.tick(1, False, False)
            if (regs.PC, regs.SP) == (0xC104, 0xC0FF):
                break
        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF), (
            label, hex(regs.PC), hex(regs.SP)
        )
        assert mem[addr("hROMBank")] == bank, label
        assert mem[0xFF70] & 7 == 1, label
        assert mem[0xFF4F] & 1 == 0, label

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

    def read_anim(label):
        old = mem[0xFF70]
        mem[0xFF70] = anim_bank
        try:
            return mem[addr(label)]
        finally:
            mem[0xFF70] = old

    def setup_case(native, species, form):
        mem[0xFF40] = 0
        mem[0xFF70] = 1
        mem[0xFF4F] = 0
        mem[0xFFFF] = 0
        mem[0xFF0F] = 0

        mem[addr("wOtherTrainerClass")] = 0
        mem[addr("wBattleType")] = 0
        mem[addr("wLinkMode")] = 0
        mem[addr("wInBattleTowerBattle")] = 0
        mem[addr("wDeferredSwitch")] = 0
        mem[addr("wEnemySubStatus4")] = 0
        mem[addr("wEnemyMonNativeSpecies"):addr("wEnemyMonNativeSpecies") + 2] = [0xA5, 0xA5]
        mem[addr("wBattleMonNativeSpecies"):addr("wBattleMonNativeSpecies") + 2] = [143, 0]

        # Prebuild the wild opponent record at the boundary normally produced
        # by LoadEnemyWildmon. SendInUserPkmn must derive the native word from
        # these existing legacy opponent bytes.
        source = addr("wOTPartyMon1Species")
        record = [0] * stride
        record[0] = species
        record[form_offset] = form
        mem[source:source + stride] = record

        # Supply stable, non-fainted battle stats copied by SendInUserPkmn.
        mem[addr("wOTPartyMon1Level")] = 30
        mem[addr("wOTPartyMon1HP")] = 0
        mem[addr("wOTPartyMon1HP") + 1] = 100
        mem[addr("wOTPartyMon1MaxHP")] = 0
        mem[addr("wOTPartyMon1MaxHP") + 1] = 100

        mem[addr("wOTPartyCount")] = 1
        mem[addr("wCurOTMon")] = 0
        mem[addr("wCurPartyMon")] = 0
        mem[addr("wEnemySwitchTarget")] = 0

        # Conflicting globals prove the live wild path republishes identity.
        mem[addr("wEnemyMonSpecies")] = 59
        mem[addr("wEnemyMonForm")] = 0x23
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

        load_wild_calls.clear()
        picture_calls.clear()
        animation_calls.clear()
        native_base_calls.clear()
        legacy_calls.clear()
        ticks.clear()
        placed.clear()

    count = 0
    digests = []
    try:
        mem[0xFF50] = 1
        mem[0xFF40] = 0
        mem[0xFF70] = 1
        mem[0xFF4F] = 0

        # Wild generation is the fixture boundary. Everything after it that
        # carries native identity into the picture and animation path is real.
        install_stub("LoadEnemyWildmon", [0xC9], lambda _: load_wild_calls.append(True))

        # UI/text/audio work is deliberately outside this regression.
        install_stub("ClearBox", [0xC9])
        install_stub("ClearSprites", [0xC9])
        install_stub("LoadTileMapToTempTileMap", [0xC9])
        install_stub("SetSeenMon", [0xC9])
        install_stub("PlaceGraphic", [0xC9], lambda _: placed.append(True))
        install_stub("BattleCheckEnemyShininess", [0xA7, 0xC9])
        install_stub("CheckSleepingTreeMon", [0xA7, 0xC9])
        install_stub("ResetVariableBattleMusicCondition", [0xC9])
        install_stub("BattleStart_TrainerHuds", [0xC9])
        install_stub("StdBattleTextbox", [0xC9])
        install_stub("CheckBattleEffects", [0xA7, 0xC9])
        install_stub("TickPokeAnim", [0x37, 0xC9], lambda _: ticks.append(True))

        # Observe real native integration points without replacing them.
        for label, dest in (
            ("PrepareNativeEnemyBattleAnimatedFrontpic", picture_calls),
            ("AnimateNativeEnemyBattleFrontpic", animation_calls),
            ("GetBaseDataFromEnemyBattleNativeSpecies", native_base_calls),
            ("GetBaseData", legacy_calls),
        ):
            bank, address = symbols[label]
            pyboy.hook_register(bank, address, lambda _, d=dest: d.append(True), None)

        for native, species, form in cases:
            setup_case(native, species, form)
            expected_base = bytes(data[
                offset("BaseDataRecords") + (native - 1) * base_len:
                offset("BaseDataRecords") + native * base_len
            ])
            context = (native, species, form)

            # Live wild branch: WILD_BATTLE, SendInUserPkmn native publication,
            # real native picture preparation, then PlaceGraphic.
            call("InitEnemy")

            shadow = int.from_bytes(
                bytes(mem[
                    addr("wEnemyMonNativeSpecies"):
                    addr("wEnemyMonNativeSpecies") + 2
                ]),
                "little",
            )
            assert load_wild_calls == [True], ("wild branch not entered once", context)
            assert shadow == native, ("native shadow publication mismatch", context, shadow)
            assert mem[addr("wBattleMode")] == 1, ("not WILD_BATTLE", context)
            assert picture_calls == [True], ("native picture path count", context, picture_calls)
            assert placed == [True], ("wild picture was not placed", context, placed)
            assert not legacy_calls, ("wild picture used legacy GetBaseData", context)
            assert bytes(mem[base_start:base_end]) == expected_base, (
                "picture-stage base data mismatch", context
            )

            front, animated = snapshot_vram()
            assert front != bytes([0x5A] * len(front)), (
                "wild front picture did not reach VRAM", context
            )
            base_anim = animated[
                v1_base_offset:v1_base_offset + len(front)
            ]
            assert base_anim != bytes([0x5A] * len(base_anim)), (
                "wild animated base frame did not reach VBK1:vTiles5", context
            )

            # Live wild start-message branch: shininess/sleep guards followed
            # by BattleAnimateFrontpic -> native animation record setup.
            call("BattleStartMessage")
            assert animation_calls == [True], (
                "native wild animation path count", context, animation_calls
            )
            assert ticks == [True], ("wild animation record was not entered", context, ticks)
            assert int.from_bytes(
                bytes(mem[
                    addr("wEnemyMonNativeSpecies"):
                    addr("wEnemyMonNativeSpecies") + 2
                ]),
                "little",
            ) == native, ("native shadow changed during wild intro", context)
            assert bytes(mem[base_start:base_end]) == expected_base, (
                "animation-stage base data mismatch", context
            )
            assert len(native_base_calls) >= 3, (
                "native base-data path did not span send-in/picture/animation",
                context, len(native_base_calls)
            )

            assert read_anim("wPokeAnimSpecies") == species, (
                "wild animation species mismatch",
                context, read_anim("wPokeAnimSpecies"), species
            )
            assert read_anim("wPokeAnimVariant") == form, (
                "wild animation form mismatch",
                context, read_anim("wPokeAnimVariant"), form
            )
            assert read_anim("wPokeAnimFrontpicHeight") != 0xA5, (
                "wild animation dimensions were not recorded", context
            )
            assert read_anim("wPokeAnimGraphicStartTile") == 0, (
                "wild animation start tile changed", context
            )
            assert mem[addr("hBattleTurn")] == 1, context

            digests.append(hashlib.sha256(front + animated).hexdigest()[:12])
            count += 1

        print(
            f"PASS: {count} native wild-battle introduction integration cases; "
            f"VRAM digests {', '.join(digests[:4])}"
        )
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
