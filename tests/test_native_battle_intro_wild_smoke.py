"""Single-entry BattleIntro wild smoke regression for native species identity.

Enter the real BattleIntro once and keep its outer wild sequencing real through
LoadTrainerOrWildMonPic, ClearBattleRAM, InitEnemy, SendInUserPkmn, native enemy
front-picture decode/VRAM transfer, BattleStartMessage and the native frontpic
animation-record path.

Wild generation itself is a deterministic fixture boundary. Presentation-only
transition, text, palette, HUD and animation-timing helpers are stubbed so this
is a smoke/integration regression rather than a full interactive battle test.
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

    # (native ID, transitional opponent species byte, encoded legacy form)
    cases = [
        (25, 25, 1),
        (257, 1, 0x21),
        (201, 201, 2),
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

    current_case = [None]
    outer_pic_calls = []
    clear_ram_calls = []
    init_enemy_calls = []
    load_wild_calls = []
    display_calls = []
    start_message_calls = []
    picture_calls = []
    animation_calls = []
    native_base_calls = []
    active_base_calls = []
    legacy_calls = []
    ticks = []
    placed = []
    hud_calls = []

    def install_stub(label, opcodes, callback=None):
        bank, address = symbols[label]
        for i, value in enumerate(opcodes):
            mem[bank, address + i] = value
        if callback is not None:
            pyboy.hook_register(bank, address, callback, None)

    def hook(label, dest):
        bank, address = symbols[label]
        pyboy.hook_register(bank, address, lambda _, d=dest: d.append(True), None)

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

    def inject_wild(_):
        native, species, form = current_case[0]
        load_wild_calls.append(True)

        # ClearBattleRAM has already run. Recreate exactly the boundary that a
        # completed LoadEnemyWildmon would hand to InitEnemy/SendInUserPkmn.
        mem[0xFF70] = 1
        source = addr("wOTPartyMon1Species")
        record = [0] * stride
        record[0] = species
        record[form_offset] = form
        mem[source:source + stride] = record

        mem[addr("wOTPartyMon1Level")] = 30
        mem[addr("wOTPartyMon1HP")] = 0
        mem[addr("wOTPartyMon1HP") + 1] = 100
        mem[addr("wOTPartyMon1MaxHP")] = 0
        mem[addr("wOTPartyMon1MaxHP") + 1] = 100
        mem[addr("wOTPartyCount")] = 1
        mem[addr("wCurOTMon")] = 0
        mem[addr("wCurPartyMon")] = 0

        # NewEnemyMonStatus resets the outgoing enemy ability before the
        # incoming record republishes identity, so give it a valid old shadow.
        mem[
            addr("wEnemyMonNativeSpecies"):
            addr("wEnemyMonNativeSpecies") + 2
        ] = [143, 0]

    def setup_case(native, species, form):
        current_case[0] = (native, species, form)

        mem[0xFF40] = 0  # direct copies; LCD-on scheduling is tested separately
        mem[0xFF70] = 1
        mem[0xFF4F] = 0
        mem[0xFFFF] = 0
        mem[0xFF0F] = 0

        mem[addr("wOtherTrainerClass")] = 0
        mem[addr("wBattleType")] = 0
        mem[addr("wWildMonForm")] = form
        mem[addr("wTempWildMonSpecies")] = species
        mem[addr("wLinkMode")] = 0
        mem[addr("wInBattleTowerBattle")] = 0
        mem[addr("wDeferredSwitch")] = 0
        mem[addr("wEnemySubStatus4")] = 0

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

        for calls in (
            outer_pic_calls, clear_ram_calls, init_enemy_calls, load_wild_calls,
            display_calls, start_message_calls, picture_calls, animation_calls,
            native_base_calls, active_base_calls, legacy_calls, ticks, placed,
            hud_calls,
        ):
            calls.clear()

    def call_battle_intro():
        bank, target = symbols["BattleIntro"]
        mem[0x2000] = bank
        mem[addr("hROMBank")] = bank
        mem[0xC100:0xC106] = [
            0xF3, 0xCD, target & 0xFF, target >> 8, 0x18, 0xFE
        ]
        regs.SP, regs.PC = 0xC0FF, 0xC100
        for _ in range(96):
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

        # Deterministic outer presentation boundaries.
        for label in (
            "PlayBattleMusic",
            "ShowLinkBattleParticipants",
            "FindFirstAliveMonAndStartBattle",
            "DisableSpriteUpdates",
            "BackUpBGMap2",
            "GetCGBLayout",
            "ClearWindowData",
            "EmptyBattleTextbox",
            "ClearBox",
            "ClearSprites",
            "LoadTileMapToTempTileMap",
            "SetSeenMon",
            "BattleCheckEnemyShininess",
            "CheckSleepingTreeMon",
            "ResetVariableBattleMusicCondition",
            "BattleStart_TrainerHuds",
            "StdBattleTextbox",
            "CheckBattleEffects",
        ):
            install_stub(label, [0xC9])

        install_stub("LoadEnemyWildmon", [0xC9], inject_wild)
        install_stub("InitBattleDisplay", [0xC9], lambda _: display_calls.append(True))
        install_stub("PlaceGraphic", [0xC9], lambda _: placed.append(True))
        install_stub("UpdateEnemyHUD", [0xC9], lambda _: hud_calls.append(True))
        install_stub("TickPokeAnim", [0x37, 0xC9], lambda _: ticks.append(True))

        # Observe real outer and native integration points.
        for label, dest in (
            ("LoadTrainerOrWildMonPic", outer_pic_calls),
            ("ClearBattleRAM", clear_ram_calls),
            ("InitEnemy", init_enemy_calls),
            ("BattleStartMessage", start_message_calls),
            ("PrepareNativeEnemyBattleAnimatedFrontpic", picture_calls),
            ("AnimateNativeEnemyBattleFrontpic", animation_calls),
            ("GetBaseDataFromEnemyBattleNativeSpecies", native_base_calls),
            ("GetBaseDataFromActiveBattleNativeSpecies", active_base_calls),
            ("GetBaseData", legacy_calls),
        ):
            hook(label, dest)

        for native, species, form in cases:
            setup_case(native, species, form)
            expected_base = bytes(data[
                offset("BaseDataRecords") + (native - 1) * base_len:
                offset("BaseDataRecords") + native * base_len
            ])
            context = (native, species, form)

            call_battle_intro()

            shadow = int.from_bytes(bytes(mem[
                addr("wEnemyMonNativeSpecies"):
                addr("wEnemyMonNativeSpecies") + 2
            ]), "little")

            assert outer_pic_calls == [True], ("outer wild picture setup count", context, outer_pic_calls)
            assert clear_ram_calls == [True], ("ClearBattleRAM count", context, clear_ram_calls)
            assert init_enemy_calls == [True], ("InitEnemy count", context, init_enemy_calls)
            assert load_wild_calls == [True], ("wild fixture count", context, load_wild_calls)
            assert display_calls == [True], ("InitBattleDisplay boundary count", context, display_calls)
            assert start_message_calls == [True], ("BattleStartMessage count", context, start_message_calls)
            assert picture_calls == [True], ("native picture path count", context, picture_calls)
            assert animation_calls == [True], ("native animation path count", context, animation_calls)
            assert ticks == [True], ("wild animation record not entered", context, ticks)
            assert placed == [True], ("wild picture not placed", context, placed)
            assert hud_calls == [True], ("final wild HUD boundary count", context, hud_calls)

            assert shadow == native, ("native shadow publication mismatch", context, shadow)
            assert mem[addr("wBattleMode")] == 1, ("not WILD_BATTLE", context)
            assert mem[addr("hBattleTurn")] == 1, ("enemy turn not retained", context)
            assert mem[addr("hBGMapMode")] != 0, ("final tilemap transfer not requested", context)
            assert not legacy_calls, ("BattleIntro wild path used legacy GetBaseData", context)
            assert active_base_calls == [True], (
                "wild send-in did not use active native base data", context, active_base_calls
            )
            assert len(native_base_calls) >= 2, (
                "native enemy base-data path did not span picture/animation",
                context, len(native_base_calls)
            )
            assert bytes(mem[base_start:base_end]) == expected_base, (
                "final native base-data mismatch", context
            )

            front, animated = snapshot_vram()
            assert front != bytes([0x5A] * len(front)), (
                "BattleIntro front picture did not reach VRAM", context
            )
            base_anim = animated[
                v1_base_offset:v1_base_offset + len(front)
            ]
            assert base_anim != bytes([0x5A] * len(base_anim)), (
                "BattleIntro animated base frame did not reach VBK1:vTiles5", context
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
                "animation dimensions not recorded", context
            )
            assert read_anim("wPokeAnimGraphicStartTile") == 0, (
                "battle animation start tile changed", context
            )

            digests.append(hashlib.sha256(front + animated).hexdigest()[:12])
            count += 1

        print(
            f"PASS: {count} single-entry native BattleIntro wild smoke cases; "
            f"VRAM digests {', '.join(digests[:4])}"
        )
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
