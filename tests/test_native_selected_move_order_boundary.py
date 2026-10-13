"""Selected-move -> move-order boundary smoke regression.

Drive the validated wild BattleIntro -> DoBattle -> first BattleTurn path
through a deterministic Fight action and valid selected move. Keep the
remaining ParsePlayerAction setup real, then stop immediately after reaching
DetermineMoveOrder so PerformMove cannot execute.

This proves both active 16-bit native identity shadows survive selection of a
real move and the transition into move ordering.
"""
import argparse
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

    # (native enemy ID, transitional enemy species byte, encoded legacy form)
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
    ot_form_offset = addr("wOTPartyMon1Form") - addr("wOTPartyMon1Species")
    player_form_offset = addr("wPartyMon1Form") - addr("wPartyMon1Species")
    base_start, base_end = addr("wCurBaseData"), addr("wCurBaseDataEnd")
    base_len = base_end - base_start

    current_case = [None]
    intro_calls = []
    do_battle_calls = []
    wild_fixture_calls = []
    enemy_sendin_calls = []
    player_sendin_calls = []
    battle_turn_calls = []
    battle_turn_shadows = []
    ai_choose_calls = []
    ai_switch_calls = []
    enemy_flee_calls = []
    battle_menu_calls = []
    battle_menu_snapshots = []
    parse_action_calls = []
    parse_action_snapshots = []
    move_selection_calls = []
    move_selection_snapshots = []
    update_move_data_calls = []
    parse_enemy_calls = []
    determine_order_calls = []
    determine_order_snapshots = []
    perform_move_calls = []
    active_base_calls = []
    enemy_base_calls = []
    legacy_calls = []

    def install_stub(label, opcodes, callback=None):
        bank, address = symbols[label]
        for i, value in enumerate(opcodes):
            mem[bank, address + i] = value
        if callback is not None:
            pyboy.hook_register(bank, address, callback, None)

    def hook(label, callback):
        bank, address = symbols[label]
        pyboy.hook_register(bank, address, callback, None)

    def invoke(label, max_frames=128):
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

    def read_native(label):
        return int.from_bytes(
            bytes(mem[addr(label):addr(label) + 2]), "little"
        )

    def inject_wild(_):
        native, species, form = current_case[0]
        wild_fixture_calls.append(True)
        mem[0xFF70] = 1

        source = addr("wOTPartyMon1Species")
        record = [0] * stride
        record[0] = species
        record[ot_form_offset] = form
        mem[source:source + stride] = record

        mem[addr("wOTPartyMon1Level")] = 30
        mem[addr("wOTPartyMon1HP")] = 0
        mem[addr("wOTPartyMon1HP") + 1] = 100
        mem[addr("wOTPartyMon1MaxHP")] = 0
        mem[addr("wOTPartyMon1MaxHP") + 1] = 100
        mem[addr("wOTPartyCount")] = 1
        mem[addr("wCurOTMon")] = 0
        mem[addr("wCurPartyMon")] = 0

        # Enemy ability reset happens before the incoming identity is
        # republished, so the old active slot must hold a valid native ID.
        mem[
            addr("wEnemyMonNativeSpecies"):
            addr("wEnemyMonNativeSpecies") + 2
        ] = [143, 0]

    def observe_sendin(_):
        if mem[addr("hBattleTurn")] & 1:
            enemy_sendin_calls.append(True)
        else:
            player_sendin_calls.append(True)

    def observe_battle_turn(_):
        battle_turn_calls.append(True)
        battle_turn_shadows.append(read_native("wEnemyMonNativeSpecies"))

    def observe_battle_menu(_):
        battle_menu_calls.append(True)
        battle_menu_snapshots.append((
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
            mem[addr("wTotalBattleTurns")],
            mem[addr("wPlayerTurnsTaken")],
            mem[addr("wEnemyTurnsTaken")],
        ))
        # Deterministic Fight action. BattleMenu returns carry clear via its
        # stub, so BattleTurn proceeds into real ParsePlayerAction.
        mem[addr("wBattlePlayerAction")] = 0
        mem[addr("wBattleEnded")] = 0

    def observe_parse_action(_):
        parse_action_calls.append(True)
        parse_action_snapshots.append((
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
            mem[addr("wBattlePlayerAction")],
        ))

    def observe_move_selection(_):
        move_selection_calls.append(True)
        move_selection_snapshots.append((
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
            mem[addr("wBattlePlayerAction")],
            mem[addr("wMoveSelectionMenuType")],
            mem[addr("wFXAnimIDLo")],
        ))
        # Deterministic valid move: Tackle (33) in slot 0. Return Z so the
        # real ParsePlayerAction path commits the selection and continues.
        mem[addr("wCurMoveNum")] = 0
        mem[addr("wCurPlayerMove")] = 33

    def observe_determine_order(_):
        determine_order_calls.append(True)
        determine_order_snapshots.append((
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
            mem[addr("wCurPlayerMove")],
            mem[addr("wCurMoveNum")],
            mem[addr("wTotalBattleTurns")],
        ))

    def setup_player_party():
        # Legacy persistent layout is deliberate here; the real player
        # SendInUserPkmn path must publish native Pikachu ID 25.
        mem[addr("wPokemonDataFormat"):addr("wPokemonDataFormat") + 2] = [0, 0]
        mem[addr("wPartyCount")] = 1

        source = addr("wPartyMon1Species")
        record = [0] * stride
        record[0] = 25
        record[player_form_offset] = 0
        mem[source:source + stride] = record

        mem[addr("wPartyMon1Level")] = 30
        mem[addr("wPartyMon1HP")] = 0
        mem[addr("wPartyMon1HP") + 1] = 100
        mem[addr("wPartyMon1MaxHP")] = 0
        mem[addr("wPartyMon1MaxHP") + 1] = 100
        mem[addr("wBattleMonNativeSpecies"):addr("wBattleMonNativeSpecies") + 2] = [0, 0]

    def setup_case(native, species, form):
        current_case[0] = (native, species, form)
        mem[0xFF40] = 0
        mem[0xFF70] = 1
        mem[0xFF4F] = 0
        mem[0xFFFF] = 0
        mem[0xFF0F] = 0

        setup_player_party()

        mem[addr("wOtherTrainerClass")] = 0
        mem[addr("wBattleType")] = 0
        mem[addr("wWildMonForm")] = form
        mem[addr("wTempWildMonSpecies")] = species
        mem[addr("wLinkMode")] = 0
        mem[addr("wInBattleTowerBattle")] = 0
        mem[addr("wDeferredSwitch")] = 0
        mem[addr("wEnemySubStatus4")] = 0

        mem[base_start:base_end] = [0xA5] * base_len

        for calls in (
            intro_calls, do_battle_calls, wild_fixture_calls,
            enemy_sendin_calls, player_sendin_calls, battle_turn_calls,
            battle_turn_shadows, ai_choose_calls, ai_switch_calls,
            enemy_flee_calls, battle_menu_calls, battle_menu_snapshots,
            parse_action_calls, parse_action_snapshots,
            move_selection_calls, move_selection_snapshots,
            update_move_data_calls, parse_enemy_calls,
            determine_order_calls, determine_order_snapshots,
            perform_move_calls,
            active_base_calls, enemy_base_calls, legacy_calls,
        ):
            calls.clear()

    try:
        mem[0xFF50] = 1
        mem[0xFF40] = 0
        mem[0xFF70] = 1
        mem[0xFF4F] = 0

        # BattleIntro presentation boundaries. Native picture/animation code
        # stays real; only transition/UI/audio/timing work is skipped.
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
            "ResetVariableBattleMusicCondition",
            "BattleStart_TrainerHuds",
            "StdBattleTextbox",
            "PlayBattleAnimDE",
            "InitBattleDisplay",
            "PlaceGraphic",
            "UpdateEnemyHUD",
            "SendOutPlayerMon",
            "UserSentOutText",
            "SlidePlayerPicOut",
            "DelayFrames",
            "SafeLoadTempTileMapToTileMap",
            "FarCopyColorWRAM",
            "SetDefaultBGPAndOBP",
            "PlayClickSFX",
            "AutomaticBattleWeather",
            "SpikesDamageBoth",
            "CustomTrainerActions",
            "RunBothEntryAbilities",
            "FixPlayerEVsAndStats",
            "BackupBattleItems",
            "ResetParticipants",
            "ParseEnemyAction",
        ):
            install_stub(label, [0xC9])

        # Normal wild guards need an explicit carry-clear result.
        install_stub("BattleCheckEnemyShininess", [0xA7, 0xC9])
        install_stub("CheckSleepingTreeMon", [0xA7, 0xC9])
        install_stub("CheckBattleEffects", [0xA7, 0xC9])
        install_stub("TickPokeAnim", [0x37, 0xC9])

        # Keep BattleTurn itself real. Unrelated per-turn effect helpers and
        # deep AI decision internals are deterministic boundaries; their call
        # sites and turn-state sequencing remain real.
        install_stub("CheckContestBattleOver", [0xA7, 0xC9])
        install_stub("HandleBerserkGene", [0xC9])
        install_stub("CheckMirrorHerb", [0xC9])
        install_stub("AIChooseMove", [0xC9], lambda _: ai_choose_calls.append(True))
        install_stub("AI_MaybeSwitch", [0xC9], lambda _: ai_switch_calls.append(True))
        install_stub("TryEnemyFlee", [0xC9], lambda _: enemy_flee_calls.append(True))

        # BattleMenu selects Fight and returns carry clear.
        install_stub("BattleMenu", [0xA7, 0xC9], observe_battle_menu)

        # Enter MoveSelectionScreen through real ParsePlayerAction, inject a
        # valid selected move, and return Z so the remaining setup continues.
        install_stub("MoveSelectionScreen", [0xAF, 0xC9], observe_move_selection)
        install_stub("LoadEnemyWildmon", [0xC9], inject_wild)

        # ParseEnemyAction is outside this player-selection checkpoint, but its
        # real call site remains exercised. Return directly after recording it.
        install_stub("ParseEnemyAction", [0xC9], lambda _: parse_enemy_calls.append(True))

        # DetermineMoveOrder is the terminal boundary. Return a deterministic
        # carry state, and patch the caller's next instruction to RET so no
        # .do_move / PerformMove path can execute.
        install_stub("DetermineMoveOrder", [0x37, 0xC9], observe_determine_order)

        battle_bank, battle_addr = symbols["BattleTurn"]
        _, order_addr = symbols["DetermineMoveOrder"]
        call_bytes = [0xCD, order_addr & 0xFF, order_addr >> 8]
        next_addr = symbols["SafariBattleTurn"][1]
        call_site = None
        for pc in range(battle_addr, next_addr - 2):
            if [mem[battle_bank, pc + i] for i in range(3)] == call_bytes:
                call_site = pc
                break
        assert call_site is not None, "DetermineMoveOrder call not found in BattleTurn"
        mem[battle_bank, call_site + 3] = 0xC9

        hook("BattleIntro", lambda _: intro_calls.append(True))
        hook("DoBattle", lambda _: do_battle_calls.append(True))
        hook("BattleTurn", observe_battle_turn)
        hook("ParsePlayerAction", observe_parse_action)
        hook("UpdateMoveData", lambda _: update_move_data_calls.append(True))
        hook("PerformMove", lambda _: perform_move_calls.append(True))
        hook("SendInUserPkmn", observe_sendin)
        hook(
            "GetBaseDataFromActiveBattleNativeSpecies",
            lambda _: active_base_calls.append(True),
        )
        hook(
            "GetBaseDataFromEnemyBattleNativeSpecies",
            lambda _: enemy_base_calls.append(True),
        )
        hook("GetBaseData", lambda _: legacy_calls.append(True))

        count = 0
        for native, species, form in cases:
            setup_case(native, species, form)
            context = (native, species, form)

            invoke("BattleIntro")

            assert intro_calls == [True], ("BattleIntro count", context, intro_calls)
            assert wild_fixture_calls == [True], ("wild fixture count", context)
            assert enemy_sendin_calls == [True], ("enemy send-in count", context, enemy_sendin_calls)
            assert read_native("wEnemyMonNativeSpecies") == native, (
                "enemy shadow after BattleIntro", context,
                read_native("wEnemyMonNativeSpecies")
            )
            assert mem[addr("wBattleMode")] == 1, ("not WILD_BATTLE", context)
            assert not legacy_calls, ("BattleIntro used legacy GetBaseData", context)

            enemy_base_before = len(enemy_base_calls)
            active_base_before = len(active_base_calls)

            invoke("DoBattle")

            assert do_battle_calls == [True], ("DoBattle count", context, do_battle_calls)
            assert battle_turn_calls == [True], (
                "first BattleTurn entry count", context, battle_turn_calls
            )
            assert battle_turn_shadows == [native], (
                "enemy shadow at BattleTurn entry", context, battle_turn_shadows
            )
            assert read_native("wEnemyMonNativeSpecies") == native, (
                "enemy shadow changed during DoBattle setup", context,
                read_native("wEnemyMonNativeSpecies")
            )

            # The player send-in remains real and must publish its own native
            # identity without touching the enemy word.
            assert player_sendin_calls == [True], (
                "player SendInUserPkmn count", context, player_sendin_calls
            )
            assert read_native("wBattleMonNativeSpecies") == 25, (
                "player native shadow not published", context,
                read_native("wBattleMonNativeSpecies")
            )

            assert len(active_base_calls) > active_base_before, (
                "DoBattle player send-in skipped active-native base lookup",
                context, len(active_base_calls), active_base_before
            )
            assert len(enemy_base_calls) >= enemy_base_before, context
            assert not legacy_calls, ("first-turn setup used legacy GetBaseData", context)

            assert ai_choose_calls == [True], (
                "enemy AI choose boundary count", context, ai_choose_calls
            )
            assert ai_switch_calls == [True], (
                "enemy AI switch boundary count", context, ai_switch_calls
            )
            assert enemy_flee_calls == [True], (
                "enemy flee boundary count", context, enemy_flee_calls
            )
            assert battle_menu_calls == [True], (
                "BattleMenu call count", context, battle_menu_calls
            )
            assert battle_menu_snapshots == [
                (25, native, 0, 1, 1, 1),
            ], ("native/turn state at player menu", context, battle_menu_snapshots)

            assert parse_action_calls == [True], (
                "ParsePlayerAction count", context, parse_action_calls
            )
            assert parse_action_snapshots == [(25, native, 0, 0)], (
                "native/action state at ParsePlayerAction",
                context, parse_action_snapshots
            )
            assert move_selection_calls == [True], (
                "MoveSelectionScreen count", context, move_selection_calls
            )
            assert move_selection_snapshots == [(25, native, 0, 0, 0, 1)], (
                "native/move-selection setup state",
                context, move_selection_snapshots
            )
            assert len(update_move_data_calls) >= 1, (
                "selected move did not reach real UpdateMoveData",
                context, update_move_data_calls
            )
            assert parse_enemy_calls == [True], (
                "ParseEnemyAction boundary count", context, parse_enemy_calls
            )
            assert determine_order_calls == [True], (
                "DetermineMoveOrder boundary count", context, determine_order_calls
            )
            assert determine_order_snapshots == [(25, native, 0, 33, 0, 1)], (
                "native/selected-move state at DetermineMoveOrder",
                context, determine_order_snapshots
            )
            assert not perform_move_calls, (
                "PerformMove reached past terminal boundary", context, perform_move_calls
            )
            assert read_native("wBattleMonNativeSpecies") == 25, context
            assert read_native("wEnemyMonNativeSpecies") == native, context
            assert mem[addr("wTotalBattleTurns")] == 1, context
            assert mem[addr("hBattleTurn")] == 0, context
            assert mem[addr("wBattlePlayerAction")] == 0, context
            assert mem[addr("wPlayerSwitchTarget")] == 0, context
            assert mem[addr("wEnemySwitchTarget")] == 0, context
            assert mem[addr("wBattleEnded")] == 0, context
            assert mem[addr("wCurPlayerMove")] == 33, context
            assert mem[addr("wCurMoveNum")] == 0, context

            count += 1

        print(
            f"PASS: {count} native selected-move/move-order boundary cases; "
            "Fight -> valid move -> real ParsePlayerAction setup -> "
            "DetermineMoveOrder, with PerformMove not reached"
        )
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
