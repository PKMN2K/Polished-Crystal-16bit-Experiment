"""Tenth real move-script command / STAB native-identity regression.

Drive the validated wild BattleIntro -> DoBattle -> first BattleTurn path
through deterministic move ordering, PerformMove, DoTurn, CheckTurn,
UpdateMoveData, InitializeMove, Tackle's real checkobedience, usedmovetext,
doturn/PP-consumption, hastarget, checkhit, checkpriority, critical,
damagestats and damagecalc commands, then execute real BattleCommand_stab.

Immediately before STAB the fixture gives the active attacker and target
NORMAL/NORMAL types, with neutral weather/items/abilities. This deliberately
exercises real 1.5x same-type attack bonus on Tackle: validated base damage 14
must become 21 while the type-effectiveness byte remains neutral.

The following damagevariation script byte is replaced with endturn_command, so
STAB/type-matchup handling completes while random damage variation, animation
and HP application remain outside this checkpoint.
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
    priority_compare_calls = []
    perform_move_calls = []
    perform_move_snapshots = []
    do_turn_calls = []
    do_turn_snapshots = []
    check_turn_calls = []
    initialize_move_calls = []
    read_script_calls = []
    read_script_snapshots = []
    checkobedience_calls = []
    checkobedience_snapshots = []
    usedmovetext_calls = []
    usedmovetext_snapshots = []
    usedmovetext_result_snapshots = []
    display_used_move_calls = []
    display_used_move_snapshots = []
    doturn_calls = []
    doturn_snapshots = []
    consume_pp_calls = []
    consume_pp_snapshots = []
    hastarget_calls = []
    hastarget_snapshots = []
    target_fainted_checks = []
    target_fainted_snapshots = []
    target_ability_checks = []
    target_ability_snapshots = []
    hastarget_active = [False]
    checkhit_active = [False]
    checkhit_calls = []
    checkhit_snapshots = []
    checkhit_result_snapshots = []
    affection_checks = []
    stat_change_mod_calls = []
    stat_change_mod_snapshots = []
    accuracy_ability_calls = []
    accuracy_ability_snapshots = []
    accuracy_user_ability_checks = []
    accuracy_user_ability_snapshots = []
    accuracy_opp_ability_checks = []
    accuracy_opp_ability_snapshots = []
    accuracy_random_calls = []
    priority_active = [False]
    checkpriority_calls = []
    checkpriority_snapshots = []
    priority_fainted_checks = []
    priority_fainted_snapshots = []
    move_priority_calls = []
    move_priority_snapshots = []
    priority_user_ability_checks = []
    priority_user_ability_snapshots = []
    priority_opp_ability_checks = []
    priority_opp_ability_snapshots = []
    critical_active = [False]
    critical_calls = []
    critical_snapshots = []
    reset_crit_calls = []
    reset_crit_snapshots = []
    critical_opp_ability_checks = []
    critical_opp_ability_snapshots = []
    future_sight_calls = []
    future_sight_snapshots = []
    user_item_after_unnerve_calls = []
    user_item_after_unnerve_snapshots = []
    user_item_calls = []
    user_item_snapshots = []
    critical_user_ability_checks = []
    critical_user_ability_snapshots = []
    critical_affection_calls = []
    critical_random_calls = []
    user_valid_item_calls = []
    damagestats_active = [False]
    damagestats_calls = []
    damagestats_snapshots = []
    damage_reset_calls = []
    damage_reset_snapshots = []
    damage_opponent_attr_calls = []
    damage_opponent_attr_snapshots = []
    damage_user_attr_calls = []
    damage_user_attr_snapshots = []
    damagestats_future_sight_calls = []
    damagestats_future_sight_snapshots = []
    damage_screen_calls = []
    damage_screen_snapshots = []
    true_user_party_attr_calls = []
    true_user_party_attr_snapshots = []
    damagestats_result_snapshots = []
    damagecalc_active = [False]
    damagecalc_calls = []
    damagecalc_snapshots = []
    damagecalc_result_snapshots = []
    stab_active = [False]
    stab_calls = []
    stab_snapshots = []
    stab_type_matchup_calls = []
    stab_type_matchup_snapshots = []
    stab_weather_calls = []
    stab_weather_snapshots = []
    stab_result_snapshots = []
    applydamage_calls = []
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

    def advance_script_pointer(snapshot, delta):
        value = (snapshot[5] | (snapshot[6] << 8)) + delta
        value &= 0xffff
        return value & 0xff, value >> 8

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
        # Seed a sentinel immediately before ordering returns; real
        # PerformMove must clear it before the DoTurn boundary.
        mem[addr("wDamageTaken"):addr("wDamageTaken") + 2] = [0xA5, 0x5A]

    def observe_perform_move(_):
        perform_move_calls.append(True)
        perform_move_snapshots.append((
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
            mem[addr("wCurPlayerMove")],
        ))

    def observe_do_turn(_):
        do_turn_calls.append(True)
        do_turn_snapshots.append((
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
            mem[addr("wCurPlayerMove")],
            mem[addr("wDamageTaken")],
            mem[addr("wDamageTaken") + 1],
        ))

    def observe_check_turn(_):
        check_turn_calls.append(True)

    def observe_initialize_move(_):
        initialize_move_calls.append(True)

    def observe_read_script(_):
        read_script_calls.append(True)
        read_script_snapshots.append((
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
            mem[addr("wCurPlayerMove")],
            mem[addr("wMoveHitState")],
            mem[addr("wBattleScriptBufferLoc")],
            mem[addr("wBattleScriptBufferLoc") + 1],
        ))
        # The fifth read is the real checkhit boundary; the sixth is the real
        # checkpriority boundary; the seventh is the real critical boundary;
        # the eighth is the real damagestats boundary; the ninth is the real
        # damagecalc boundary; and the tenth is the real STAB boundary. The
        # eleventh real script-byte read sees the test-only endturn byte in
        # place of damagevariation and ends the outer battle loop.
        if len(read_script_calls) == 3:
            usedmovetext_result_snapshots.append(mem[addr("wMoveGrammar")])
        if len(read_script_calls) == 5:
            hastarget_active[0] = False
        if len(read_script_calls) == 6:
            checkhit_result_snapshots.append(tuple(
                mem[addr("hMultiplicand"):addr("hMultiplicand") + 3]
            ))
            checkhit_active[0] = False
        if len(read_script_calls) == 7:
            priority_active[0] = False
        if len(read_script_calls) == 8:
            critical_active[0] = False
        if len(read_script_calls) == 9:
            damagestats_result_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                regs.B, regs.C, regs.D, regs.E,
            ))
            damagestats_active[0] = False
        if len(read_script_calls) == 10:
            damagecalc_result_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
                mem[addr("wCurDamage")],
                mem[addr("wCurDamage") + 1],
            ))
            damagecalc_active[0] = False
        if len(read_script_calls) == 11:
            stab_result_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
                mem[addr("wTypeModifier")],
                mem[addr("wTypeMatchup")],
                mem[addr("wCurDamage")],
                mem[addr("wCurDamage") + 1],
            ))
            stab_active[0] = False
            mem[addr("wBattleEnded")] = 1

    def observe_checkobedience(_):
        checkobedience_calls.append(True)
        checkobedience_snapshots.append((
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
            mem[addr("wCurPlayerMove")],
            mem[addr("wBattleScriptBufferLoc")],
            mem[addr("wBattleScriptBufferLoc") + 1],
        ))

    def observe_usedmovetext(_):
        usedmovetext_calls.append(True)
        usedmovetext_snapshots.append((
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
            mem[addr("wCurPlayerMove")],
            mem[addr("wBattleScriptBufferLoc")],
            mem[addr("wBattleScriptBufferLoc") + 1],
        ))

    def observe_display_used_move(_):
        display_used_move_calls.append(True)
        display_used_move_snapshots.append((
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
            mem[addr("wCurPlayerMove")],
        ))

    def observe_doturn(_):
        doturn_calls.append(True)
        doturn_snapshots.append((
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
            mem[addr("wCurPlayerMove")],
            mem[addr("wPartyMon1PP")],
            mem[addr("wBattleMonPP")],
            mem[addr("wBattleScriptBufferLoc")],
            mem[addr("wBattleScriptBufferLoc") + 1],
        ))

    def observe_consume_pp(_):
        consume_pp_calls.append(True)
        consume_pp_snapshots.append((
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
            mem[addr("wCurPlayerMove")],
            mem[addr("wPartyMon1PP")],
            mem[addr("wBattleMonPP")],
        ))

    def observe_hastarget(_):
        hastarget_active[0] = True
        hastarget_calls.append(True)
        hastarget_snapshots.append((
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
            mem[addr("wCurPlayerMove")],
            mem[addr("wEnemyMonHP")],
            mem[addr("wEnemyMonHP") + 1],
            mem[addr("wPartyMon1PP")],
            mem[addr("wBattleMonPP")],
            mem[addr("wBattleScriptBufferLoc")],
            mem[addr("wBattleScriptBufferLoc") + 1],
        ))

    def observe_target_fainted(_):
        snapshot = (
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
            mem[addr("wEnemyMonHP")],
            mem[addr("wEnemyMonHP") + 1],
        )
        if hastarget_active[0]:
            target_fainted_checks.append(True)
            target_fainted_snapshots.append(snapshot)
        if priority_active[0]:
            priority_fainted_checks.append(True)
            priority_fainted_snapshots.append(snapshot)

    def observe_target_ability(_):
        snapshot = (
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
            mem[addr("wCurPlayerMove")],
        )
        if hastarget_active[0]:
            target_ability_checks.append(True)
            target_ability_snapshots.append(snapshot)
        if checkhit_active[0]:
            accuracy_opp_ability_checks.append(True)
            accuracy_opp_ability_snapshots.append(snapshot)
        if priority_active[0]:
            priority_opp_ability_checks.append(True)
            priority_opp_ability_snapshots.append(snapshot)
        if critical_active[0]:
            critical_opp_ability_checks.append(True)
            critical_opp_ability_snapshots.append(snapshot)

    def observe_checkhit(_):
        checkhit_active[0] = True

        # Force only the ordinary accuracy path inputs. The handler and all
        # accuracy math/ability lookups remain real.
        for label in (
            "wPlayerSubStatus1", "wPlayerSubStatus2",
            "wPlayerSubStatus3", "wPlayerSubStatus4",
            "wEnemySubStatus1", "wEnemySubStatus2",
            "wEnemySubStatus3", "wEnemySubStatus4",
        ):
            mem[addr(label)] = 0
        mem[addr("wPlayerAbility")] = 0
        mem[addr("wEnemyAbility")] = 0
        mem[addr("wBattleMonItem")] = 0
        mem[addr("wEnemyMonItem")] = 0
        mem[addr("wBattleWeather")] = 0
        mem[addr("wMoveState")] = 0
        mem[addr("wTypeModifier")] = 0x10
        mem[addr("wAttackMissed")] = 0
        mem[addr("wPlayerAccLevel")] = 7
        mem[addr("wPlayerEvaLevel")] = 7
        mem[addr("wEnemyAccLevel")] = 7
        mem[addr("wEnemyEvaLevel")] = 7

        checkhit_calls.append(True)
        checkhit_snapshots.append((
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
            mem[addr("wCurPlayerMove")],
            mem[addr("wPartyMon1PP")],
            mem[addr("wBattleMonPP")],
            mem[addr("wBattleScriptBufferLoc")],
            mem[addr("wBattleScriptBufferLoc") + 1],
        ))

    def observe_stat_change_mod(_):
        if checkhit_active[0]:
            stat_change_mod_calls.append(True)
            stat_change_mod_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("wPlayerAccLevel")],
                mem[addr("wEnemyEvaLevel")],
            ))

    def observe_accuracy_abilities(_):
        if checkhit_active[0]:
            accuracy_ability_calls.append(True)
            accuracy_ability_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
            ))

    def observe_user_ability(_):
        snapshot = (
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
            mem[addr("wCurPlayerMove")],
        )
        if checkhit_active[0]:
            accuracy_user_ability_checks.append(True)
            accuracy_user_ability_snapshots.append(snapshot)
        if priority_active[0]:
            priority_user_ability_checks.append(True)
            priority_user_ability_snapshots.append(snapshot)
        if critical_active[0]:
            critical_user_ability_checks.append(True)
            critical_user_ability_snapshots.append(snapshot)

    def observe_move_priority(_):
        if priority_active[0]:
            move_priority_calls.append(True)
            move_priority_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
            ))

    def observe_checkpriority(_):
        priority_active[0] = True
        checkpriority_calls.append(True)
        checkpriority_snapshots.append((
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
            mem[addr("wCurPlayerMove")],
            mem[addr("wEnemyMonHP")],
            mem[addr("wEnemyMonHP") + 1],
            mem[addr("wPartyMon1PP")],
            mem[addr("wBattleMonPP")],
            mem[addr("wAttackMissed")],
            mem[addr("wBattleScriptBufferLoc")],
            mem[addr("wBattleScriptBufferLoc") + 1],
        ))

    def observe_critical(_):
        critical_active[0] = True
        mem[addr("wPlayerAbility")] = 0
        mem[addr("wEnemyAbility")] = 0
        mem[addr("wBattleMonItem")] = 0
        mem[addr("wEnemyMonItem")] = 0
        mem[addr("wPlayerSubStatus4")] = 0
        mem[addr("wPlayerFutureSightCount")] = 0

        critical_calls.append(True)
        critical_snapshots.append((
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
            mem[addr("wCurPlayerMove")],
            mem[addr("wMoveHitState")],
            mem[addr("wPartyMon1PP")],
            mem[addr("wBattleMonPP")],
            mem[addr("wBattleScriptBufferLoc")],
            mem[addr("wBattleScriptBufferLoc") + 1],
        ))

    def observe_reset_crit(_):
        if critical_active[0]:
            reset_crit_calls.append(True)
            reset_crit_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("wMoveHitState")],
            ))

    def observe_future_sight(_):
        if critical_active[0]:
            future_sight_calls.append(True)
            future_sight_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wPlayerFutureSightCount")],
            ))
        if damagestats_active[0]:
            damagestats_future_sight_calls.append(True)
            damagestats_future_sight_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wPlayerFutureSightCount")],
            ))

    def observe_user_item_after_unnerve(_):
        if critical_active[0]:
            user_item_after_unnerve_calls.append(True)
            user_item_after_unnerve_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("wBattleMonItem")],
            ))

    def observe_user_item(_):
        if critical_active[0]:
            user_item_calls.append(True)
            user_item_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("wBattleMonItem")],
            ))

    def observe_critical_affection(_):
        if critical_active[0]:
            critical_affection_calls.append(True)

    def observe_user_valid_item(_):
        if critical_active[0]:
            user_valid_item_calls.append(True)

    def observe_accuracy_random(_):
        # BattleRandomRange receives the exclusive upper bound in A.
        if checkhit_active[0]:
            accuracy_random_calls.append(regs.A)
        if critical_active[0]:
            critical_random_calls.append(regs.A)

    def observe_damagestats(_):
        damagestats_active[0] = True
        # Earlier boundary fixtures only need HP/level, so their synthetic
        # party records leave combat stats at zero. Seed meaningful active
        # stats here, immediately before the real damagestats command, without
        # changing any gameplay/migration code or earlier battle behavior.
        mem[addr("wBattleMonAttack"):addr("wBattleMonAttack") + 2] = [0, 90]
        mem[addr("wEnemyMonDefense"):addr("wEnemyMonDefense") + 2] = [0, 80]
        damagestats_calls.append(True)
        damagestats_snapshots.append((
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
            mem[addr("wCurPlayerMove")],
            mem[addr("wMoveHitState")],
            mem[addr("wPartyMon1PP")],
            mem[addr("wBattleMonPP")],
            mem[addr("wBattleScriptBufferLoc")],
            mem[addr("wBattleScriptBufferLoc") + 1],
        ))

    def observe_damagecalc(_):
        damagecalc_active[0] = True
        damagecalc_calls.append(True)
        damagecalc_snapshots.append((
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
            mem[addr("wCurPlayerMove")],
            mem[addr("wMoveHitState")],
            regs.B, regs.C, regs.D, regs.E,
            mem[addr("wBattleScriptBufferLoc")],
            mem[addr("wBattleScriptBufferLoc") + 1],
        ))

    def observe_stab(_):
        stab_active[0] = True
        # Make this command exercise real neutral type matchup + 1.5x STAB
        # deterministically, independent of the identity cases under test.
        # NORMAL is type $00 in the current battle type table.
        mem[addr("wBattleMonType1")] = 0
        mem[addr("wBattleMonType2")] = 0
        mem[addr("wEnemyMonType1")] = 0
        mem[addr("wEnemyMonType2")] = 0
        mem[addr("wBattleWeather")] = 0
        mem[addr("wPlayerSubStatus2")] = 0
        mem[addr("wEnemySubStatus2")] = 0
        mem[addr("wBattleMonItem")] = 0
        mem[addr("wEnemyMonItem")] = 0
        mem[addr("wPlayerAbility")] = 0
        mem[addr("wEnemyAbility")] = 0
        mem[addr("wAttackMissed")] = 0
        mem[addr("wTypeModifier")] = 0x10
        mem[addr("wTypeMatchup")] = 0x10
        stab_calls.append(True)
        stab_snapshots.append((
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
            mem[addr("wCurPlayerMove")],
            mem[addr("wCurDamage")],
            mem[addr("wCurDamage") + 1],
            mem[addr("wBattleScriptBufferLoc")],
            mem[addr("wBattleScriptBufferLoc") + 1],
        ))

    def observe_stab_type_matchup(_):
        if stab_active[0]:
            stab_type_matchup_calls.append(True)
            stab_type_matchup_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
            ))

    def observe_stab_weather(_):
        if stab_active[0]:
            stab_weather_calls.append(True)
            stab_weather_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wBattleWeather")],
            ))

    def observe_damage_reset(_):
        if damagestats_active[0]:
            damage_reset_calls.append(True)
            damage_reset_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
            ))

    def observe_damage_opponent_attr(_):
        if damagestats_active[0]:
            damage_opponent_attr_calls.append(True)
            damage_opponent_attr_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                regs.HL,
            ))

    def observe_damage_user_attr(_):
        if damagestats_active[0]:
            damage_user_attr_calls.append(True)
            damage_user_attr_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                regs.HL,
            ))

    def observe_damage_screens(_):
        if damagestats_active[0]:
            damage_screen_calls.append(True)
            damage_screen_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
            ))

    def observe_true_user_party_attr(_):
        if damagestats_active[0]:
            true_user_party_attr_calls.append(True)
            true_user_party_attr_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                regs.A,
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
        mem[addr("wPartyMon1Moves")] = 33
        mem[addr("wPartyMon1PP")] = 35
        # Make the first real checkobedience command deterministic: the active
        # party Pokémon is owned by the player, so the command returns through
        # its normal matching-ID path without any badge/random disobedience.
        mem[addr("wPlayerID"):addr("wPlayerID") + 2] = [0, 0]
        mem[addr("wPartyMon1ID"):addr("wPartyMon1ID") + 2] = [0, 0]

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
        hastarget_active[0] = False
        checkhit_active[0] = False
        priority_active[0] = False
        critical_active[0] = False
        damagestats_active[0] = False
        damagecalc_active[0] = False
        stab_active[0] = False

        mem[addr("wOtherTrainerClass")] = 0
        mem[addr("wBattleType")] = 0
        mem[addr("wWildMonForm")] = form
        mem[addr("wTempWildMonSpecies")] = species
        mem[addr("wLinkMode")] = 0
        mem[addr("wInBattleTowerBattle")] = 0
        mem[addr("wDeferredSwitch")] = 0
        mem[addr("wEnemySubStatus4")] = 0

        mem[base_start:base_end] = [0xA5] * base_len
        mem[addr("wDamageTaken"):addr("wDamageTaken") + 2] = [0xA5, 0x5A]

        for calls in (
            intro_calls, do_battle_calls, wild_fixture_calls,
            enemy_sendin_calls, player_sendin_calls, battle_turn_calls,
            battle_turn_shadows, ai_choose_calls, ai_switch_calls,
            enemy_flee_calls, battle_menu_calls, battle_menu_snapshots,
            parse_action_calls, parse_action_snapshots,
            move_selection_calls, move_selection_snapshots,
            update_move_data_calls, parse_enemy_calls,
            determine_order_calls, determine_order_snapshots,
            priority_compare_calls, perform_move_calls,
            perform_move_snapshots, do_turn_calls, do_turn_snapshots,
            check_turn_calls, initialize_move_calls,
            read_script_calls, read_script_snapshots,
            checkobedience_calls, checkobedience_snapshots,
            usedmovetext_calls, usedmovetext_snapshots,
            usedmovetext_result_snapshots,
            display_used_move_calls, display_used_move_snapshots,
            doturn_calls, doturn_snapshots,
            consume_pp_calls, consume_pp_snapshots,
            hastarget_calls, hastarget_snapshots,
            target_fainted_checks, target_fainted_snapshots,
            target_ability_checks, target_ability_snapshots,
            checkhit_calls, checkhit_snapshots, checkhit_result_snapshots,
            affection_checks,
            stat_change_mod_calls, stat_change_mod_snapshots,
            accuracy_ability_calls, accuracy_ability_snapshots,
            accuracy_user_ability_checks, accuracy_user_ability_snapshots,
            accuracy_opp_ability_checks, accuracy_opp_ability_snapshots,
            accuracy_random_calls, checkpriority_calls, checkpriority_snapshots,
            priority_fainted_checks, priority_fainted_snapshots,
            move_priority_calls, move_priority_snapshots,
            priority_user_ability_checks, priority_user_ability_snapshots,
            priority_opp_ability_checks, priority_opp_ability_snapshots,
            critical_calls, critical_snapshots,
            reset_crit_calls, reset_crit_snapshots,
            critical_opp_ability_checks, critical_opp_ability_snapshots,
            future_sight_calls, future_sight_snapshots,
            user_item_after_unnerve_calls, user_item_after_unnerve_snapshots,
            user_item_calls, user_item_snapshots,
            critical_user_ability_checks, critical_user_ability_snapshots,
            critical_affection_calls, critical_random_calls,
            user_valid_item_calls, damagestats_calls, damagestats_snapshots,
            damage_reset_calls, damage_reset_snapshots,
            damage_opponent_attr_calls, damage_opponent_attr_snapshots,
            damage_user_attr_calls, damage_user_attr_snapshots,
            damagestats_future_sight_calls, damagestats_future_sight_snapshots,
            damage_screen_calls, damage_screen_snapshots,
            true_user_party_attr_calls, true_user_party_attr_snapshots,
            damagestats_result_snapshots,
            damagecalc_calls, damagecalc_snapshots,
            damagecalc_result_snapshots,
            stab_calls, stab_snapshots,
            stab_type_matchup_calls, stab_type_matchup_snapshots,
            stab_weather_calls, stab_weather_snapshots,
            stab_result_snapshots, applydamage_calls,
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

        # Keep DetermineMoveOrder real but make priority comparison
        # deterministic: carry set means the player goes first.
        install_stub(
            "CompareMovePriority",
            # ld a, 1; or a (Z clear, C clear); scf; ret
            [0x3E, 0x01, 0xB7, 0x37, 0xC9],
            lambda _: priority_compare_calls.append(True),
        )

        # Keep DoTurn, CheckTurn, UpdateMoveData, InitializeMove,
        # ReadMoveScriptByte, checkobedience, usedmovetext, DisplayUsedMoveText,
        # doturn/BattleConsumePP, hastarget, checkhit, checkpriority, critical,
        # damagestats, damagecalc and STAB real. Replace only the following
        # damagevariation command with endturn_command ($fe), so STAB/type
        # handling completes and the eleventh real script read terminates
        # before random damage variation.
        normal_bank, normal_addr = symbols["NormalHit"]
        assert mem[normal_bank, normal_addr] == 2, (
            "NormalHit no longer begins with checkobedience",
            mem[normal_bank, normal_addr],
        )
        assert mem[normal_bank, normal_addr + 1] == 3, (
            "NormalHit second command is no longer usedmovetext",
            mem[normal_bank, normal_addr + 1],
        )
        assert mem[normal_bank, normal_addr + 2] == 4, (
            "NormalHit third command is no longer doturn",
            mem[normal_bank, normal_addr + 2],
        )
        # Battle-command IDs are not globally sequential; hastarget is
        # command $3f in the current command table.
        assert mem[normal_bank, normal_addr + 3] == 0x3F, (
            "NormalHit fourth command is no longer hastarget",
            mem[normal_bank, normal_addr + 3],
        )
        assert mem[normal_bank, normal_addr + 4] == 9, (
            "NormalHit fifth command is no longer checkhit",
            mem[normal_bank, normal_addr + 4],
        )
        assert mem[normal_bank, normal_addr + 5] == 10, (
            "NormalHit sixth command is no longer checkpriority",
            mem[normal_bank, normal_addr + 5],
        )
        assert mem[normal_bank, normal_addr + 6] == 5, (
            "NormalHit seventh command is no longer critical",
            mem[normal_bank, normal_addr + 6],
        )
        assert mem[normal_bank, normal_addr + 7] == 6, (
            "NormalHit eighth command is no longer damagestats",
            mem[normal_bank, normal_addr + 7],
        )
        # Battle-command IDs are not globally sequential; damagecalc is
        # command $50 in the current command table.
        assert mem[normal_bank, normal_addr + 8] == 0x50, (
            "NormalHit ninth command is no longer damagecalc",
            mem[normal_bank, normal_addr + 8],
        )
        assert mem[normal_bank, normal_addr + 9] == 7, (
            "NormalHit tenth command is no longer stab",
            mem[normal_bank, normal_addr + 9],
        )
        assert mem[normal_bank, normal_addr + 10] == 8, (
            "NormalHit eleventh command is no longer damagevariation",
            mem[normal_bank, normal_addr + 10],
        )
        mem[normal_bank, normal_addr + 10] = 0xFE

        for label in (
            "CheckEndMoveEffects",
            "CheckThroatSpray",
            "CheckPowerHerb",
            # Presentation-only tail of DisplayUsedMoveText. Its move-history,
            # grammar, last-move and text-selection state logic remains real.
            "ApplyTilemapInVBlank",
        ):
            install_stub(label, [0xC9])

        # Affection is outside native battle identity and can inject a random
        # evasion event before ordinary accuracy math. Force "below threshold"
        # while leaving the rest of BattleCommand_checkhit real.
        install_stub(
            "CheckOpponentAffection", [0xAF, 0xC9],
            lambda _: affection_checks.append(True),
        )
        install_stub(
            "CheckAffection", [0xAF, 0xC9], observe_critical_affection
        )

        # Deterministic randomness boundary for this deeper checkpoint.
        # Input 100 (checkhit) returns 0, preserving the guaranteed hit.
        # Input 24 (critical) returns 23, guaranteeing non-critical at 1/24.
        # cp 24; jr nz,+3; ld a,23; ret; xor a; ret
        install_stub(
            "BattleRandomRange",
            [0xFE, 24, 0x20, 0x03, 0x3E, 23, 0xC9, 0xAF, 0xC9],
            observe_accuracy_random,
        )

        # When DoTurn returns, immediately return from PerformMove instead of
        # running post-move/faint resolution. wBattleEnded set at the script
        # boundary then makes BattleTurn exit after this first move setup.
        end_bank, end_addr = symbols["PerformMove.end_protect"]
        mem[end_bank, end_addr] = 0xC9

        hook("BattleIntro", lambda _: intro_calls.append(True))
        hook("DoBattle", lambda _: do_battle_calls.append(True))
        hook("BattleTurn", observe_battle_turn)
        hook("ParsePlayerAction", observe_parse_action)
        hook("UpdateMoveData", lambda _: update_move_data_calls.append(True))
        hook("DetermineMoveOrder", observe_determine_order)
        hook("PerformMove", observe_perform_move)
        hook("DoTurn", observe_do_turn)
        hook("CheckTurn", observe_check_turn)
        hook("InitializeMove", observe_initialize_move)
        hook("ReadMoveScriptByte", observe_read_script)
        hook("BattleCommand_checkobedience", observe_checkobedience)
        hook("BattleCommand_usedmovetext", observe_usedmovetext)
        hook("DisplayUsedMoveText", observe_display_used_move)
        hook("BattleCommand_doturn", observe_doturn)
        hook("BattleConsumePP", observe_consume_pp)
        hook("BattleCommand_hastarget", observe_hastarget)
        hook("HasOpponentFainted", observe_target_fainted)
        hook("GetOpponentIgnorableAbility", observe_target_ability)
        hook("GetTrueUserIgnorableAbility", observe_user_ability)
        hook("BattleCommand_checkhit", observe_checkhit)
        hook("DoStatChangeMod", observe_stat_change_mod)
        hook("ApplyAccuracyAbilities", observe_accuracy_abilities)
        hook("BattleCommand_checkpriority", observe_checkpriority)
        hook("GetMovePriority", observe_move_priority)
        hook("BattleCommand_critical", observe_critical)
        hook("ResetCrit", observe_reset_crit)
        hook("GetFutureSightUser", observe_future_sight)
        hook("GetUserItemAfterUnnerve", observe_user_item_after_unnerve)
        hook("GetUserItem", observe_user_item)
        hook("UserValidBattleItem", observe_user_valid_item)
        hook("BattleCommand_damagestats", observe_damagestats)
        hook("ResetDamage", observe_damage_reset)
        hook("GetOpponentMonAttr", observe_damage_opponent_attr)
        hook("GetUserMonAttr", observe_damage_user_attr)
        hook("GetOpponentActiveScreens", observe_damage_screens)
        hook("TrueUserPartyAttr", observe_true_user_party_attr)
        hook("BattleCommand_damagecalc", observe_damagecalc)
        hook("BattleCommand_stab", observe_stab)
        hook("BattleCheckTypeMatchup", observe_stab_type_matchup)
        hook("DoWeatherModifiers", observe_stab_weather)
        hook("BattleCommand_applydamage", lambda _: applydamage_calls.append(True))
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
                "DetermineMoveOrder count", context, determine_order_calls
            )
            assert determine_order_snapshots == [(25, native, 0, 33, 0, 1)], (
                "native/selected-move state at DetermineMoveOrder",
                context, determine_order_snapshots
            )
            assert priority_compare_calls == [True], (
                "deterministic priority boundary count", context,
                priority_compare_calls
            )
            assert perform_move_calls == [True], (
                "first PerformMove entry count", context, perform_move_calls
            )
            assert perform_move_snapshots == [(25, native, 0, 33)], (
                "acting native identity at PerformMove entry",
                context, perform_move_snapshots
            )
            assert do_turn_calls == [True], (
                "DoTurn entry count", context, do_turn_calls
            )
            assert do_turn_snapshots == [(25, native, 0, 33, 0, 0)], (
                "real PerformMove setup did not reach DoTurn cleanly",
                context, do_turn_snapshots
            )
            assert check_turn_calls == [True], (
                "real CheckTurn count", context, check_turn_calls
            )
            assert initialize_move_calls == [True], (
                "real InitializeMove count", context, initialize_move_calls
            )
            assert len(update_move_data_calls) >= 2, (
                "DoTurn did not perform its real UpdateMoveData refresh",
                context, update_move_data_calls
            )
            assert read_script_calls == [
                True, True, True, True, True, True, True, True, True, True, True
            ], (
                "real move-script read count around first ten commands", context,
                read_script_calls
            )
            assert read_script_snapshots[0][:5] == (25, native, 0, 33, 0), (
                "native/move state at first real script read",
                context, read_script_snapshots
            )
            assert read_script_snapshots[0][5:] != (0, 0), (
                "InitializeMove did not publish a move-script pointer",
                context, read_script_snapshots
            )
            assert checkobedience_calls == [True], (
                "first real battle-command dispatch count", context,
                checkobedience_calls
            )
            assert checkobedience_snapshots == [
                (25, native, 0, 33, *advance_script_pointer(read_script_snapshots[0], 1)),
            ], (
                "native identity/script pointer at checkobedience dispatch",
                context, checkobedience_snapshots, read_script_snapshots
            )
            assert read_script_snapshots[1][:5] == (25, native, 0, 33, 0), (
                "native/move state changed after checkobedience",
                context, read_script_snapshots
            )
            assert usedmovetext_calls == [True], (
                "second real battle-command dispatch count", context,
                usedmovetext_calls
            )
            assert usedmovetext_snapshots == [
                (25, native, 0, 33, *advance_script_pointer(read_script_snapshots[0], 2)),
            ], (
                "native identity/script pointer at usedmovetext dispatch",
                context, usedmovetext_snapshots, read_script_snapshots
            )
            assert display_used_move_calls == [True], (
                "usedmovetext did not enter real DisplayUsedMoveText", context,
                display_used_move_calls
            )
            assert display_used_move_snapshots == [(25, native, 0, 33)], (
                "native identity changed inside DisplayUsedMoveText",
                context, display_used_move_snapshots
            )
            assert read_script_snapshots[2][:5] == (25, native, 0, 33, 0), (
                "native/move state changed after usedmovetext",
                context, read_script_snapshots
            )
            assert read_script_snapshots[2][5:] == advance_script_pointer(
                read_script_snapshots[0], 2
            ), (
                "script pointer did not advance through two real commands",
                context, read_script_snapshots
            )
            assert doturn_calls == [True], (
                "third real battle-command dispatch count", context, doturn_calls
            )
            assert doturn_snapshots == [
                (
                    25, native, 0, 33, 35, 35,
                    *advance_script_pointer(read_script_snapshots[0], 3),
                ),
            ], (
                "native identity/PP/script pointer at doturn dispatch",
                context, doturn_snapshots, read_script_snapshots
            )
            assert consume_pp_calls == [True], (
                "real BattleConsumePP call count", context, consume_pp_calls
            )
            assert consume_pp_snapshots == [(25, native, 0, 33, 35, 35)], (
                "native identity/PP changed before BattleConsumePP",
                context, consume_pp_snapshots
            )
            assert read_script_snapshots[3][:5] == (25, native, 0, 33, 0), (
                "native/move state changed after doturn",
                context, read_script_snapshots
            )
            assert read_script_snapshots[3][5:] == advance_script_pointer(
                read_script_snapshots[0], 3
            ), (
                "script pointer did not advance through three real commands",
                context, read_script_snapshots
            )
            assert hastarget_calls == [True], (
                "fourth real battle-command dispatch count", context,
                hastarget_calls
            )
            assert hastarget_snapshots == [
                (
                    25, native, 0, 33, 0, 100, 34, 34,
                    *advance_script_pointer(read_script_snapshots[0], 4),
                ),
            ], (
                "native identity/HP/PP/script pointer at hastarget dispatch",
                context, hastarget_snapshots, read_script_snapshots
            )
            assert target_fainted_checks == [True], (
                "hastarget did not run its living-target check",
                context, target_fainted_checks
            )
            assert target_fainted_snapshots == [(25, native, 0, 0, 100)], (
                "native identity/HP changed during target-faint check",
                context, target_fainted_snapshots
            )
            assert target_ability_checks == [True], (
                "hastarget did not run opponent ability lookup",
                context, target_ability_checks
            )
            assert target_ability_snapshots == [(25, native, 0, 33)], (
                "native identity changed during opponent ability lookup",
                context, target_ability_snapshots
            )
            assert read_script_snapshots[4][:5] == (25, native, 0, 33, 0), (
                "native/move state changed after hastarget",
                context, read_script_snapshots
            )
            assert read_script_snapshots[4][5:] == advance_script_pointer(
                read_script_snapshots[0], 4
            ), (
                "script pointer did not advance through four real commands",
                context, read_script_snapshots
            )
            assert checkhit_calls == [True], (
                "fifth real battle-command dispatch count", context,
                checkhit_calls
            )
            assert checkhit_snapshots == [
                (
                    25, native, 0, 33, 34, 34,
                    *advance_script_pointer(read_script_snapshots[0], 5),
                ),
            ], (
                "native identity/PP/script pointer at checkhit dispatch",
                context, checkhit_snapshots, read_script_snapshots
            )
            assert affection_checks == [True], (
                "checkhit affection boundary count", context, affection_checks
            )
            assert stat_change_mod_calls == [True], (
                "checkhit did not reach ordinary stat-modifier accuracy math",
                context, stat_change_mod_calls
            )
            assert stat_change_mod_snapshots == [(25, native, 7, 7)], (
                "native identity or neutral accuracy/evasion stages changed",
                context, stat_change_mod_snapshots
            )
            assert accuracy_ability_calls == [True], (
                "checkhit did not run real accuracy ability processing",
                context, accuracy_ability_calls
            )
            assert accuracy_ability_snapshots == [(25, native, 0, 33)], (
                "native identity changed in ApplyAccuracyAbilities",
                context, accuracy_ability_snapshots
            )
            assert accuracy_user_ability_checks, (
                "checkhit skipped user ability checks", context
            )
            assert all(
                snap == (25, native, 0, 33)
                for snap in accuracy_user_ability_snapshots
            ), (
                "native identity changed during user ability checks",
                context, accuracy_user_ability_snapshots
            )
            assert accuracy_opp_ability_checks, (
                "checkhit skipped opponent ability checks", context
            )
            assert all(
                snap[0:2] == (25, native)
                and snap[2] in (0, 1)
                and snap[3] == 33
                for snap in accuracy_opp_ability_snapshots
            ), (
                "native identity/move changed during opponent ability checks",
                context, accuracy_opp_ability_snapshots
            )
            assert any(
                snap[2] == 1 for snap in accuracy_opp_ability_snapshots
            ), (
                "accuracy ability processing did not exercise opponent-turn "
                "perspective", context, accuracy_opp_ability_snapshots
            )
            assert accuracy_random_calls == [100], (
                "100%-accuracy Tackle did not use the guaranteed 0-99 < 100 "
                "hit roll", context, accuracy_random_calls
            )
            assert read_script_snapshots[5][:5] == (25, native, 0, 33, 0), (
                "native/move state changed after checkhit",
                context, read_script_snapshots
            )
            assert read_script_snapshots[5][5:] == advance_script_pointer(
                read_script_snapshots[0], 5
            ), (
                "script pointer did not advance through five real commands",
                context, read_script_snapshots
            )
            assert mem[addr("wAttackMissed")] == 0, (
                "deterministic Tackle accuracy path marked a miss",
                context, mem[addr("wAttackMissed")]
            )
            assert checkhit_result_snapshots == [(0, 0, 100)], (
                "real accuracy math did not resolve Tackle to 100% at the "
                "checkhit boundary",
                context, checkhit_result_snapshots
            )
            assert checkpriority_calls == [True], (
                "sixth real battle-command dispatch count", context,
                checkpriority_calls
            )
            assert checkpriority_snapshots == [
                (
                    25, native, 0, 33, 0, 100, 34, 34, 0,
                    *advance_script_pointer(read_script_snapshots[0], 6),
                ),
            ], (
                "native identity/HP/PP/hit/script pointer at checkpriority",
                context, checkpriority_snapshots, read_script_snapshots
            )
            assert priority_fainted_checks == [True], (
                "checkpriority did not run living-target check",
                context, priority_fainted_checks
            )
            assert priority_fainted_snapshots == [(25, native, 0, 0, 100)], (
                "native identity/HP changed during priority target check",
                context, priority_fainted_snapshots
            )
            assert move_priority_calls == [True], (
                "checkpriority did not call real GetMovePriority",
                context, move_priority_calls
            )
            assert move_priority_snapshots == [(25, native, 0, 33)], (
                "native identity/move changed entering GetMovePriority",
                context, move_priority_snapshots
            )
            assert priority_user_ability_checks == [True, True], (
                "normal-priority path did not run GetMovePriority and "
                "Prankster user-ability checks",
                context, priority_user_ability_checks
            )
            assert all(
                snap == (25, native, 0, 33)
                for snap in priority_user_ability_snapshots
            ), (
                "native identity changed during priority user-ability checks",
                context, priority_user_ability_snapshots
            )
            assert priority_opp_ability_checks == [True], (
                "normal-priority path did not run exactly the Soundproof "
                "opponent-ability check", context, priority_opp_ability_checks
            )
            assert priority_opp_ability_snapshots == [(25, native, 0, 33)], (
                "native identity changed during priority opponent-ability check",
                context, priority_opp_ability_snapshots
            )
            assert read_script_snapshots[6][:5] == (25, native, 0, 33, 0), (
                "native/move state changed after checkpriority",
                context, read_script_snapshots
            )
            assert read_script_snapshots[6][5:] == advance_script_pointer(
                read_script_snapshots[0], 6
            ), (
                "script pointer did not advance through six real commands",
                context, read_script_snapshots
            )
            assert critical_calls == [True], (
                "seventh real battle-command dispatch count", context,
                critical_calls
            )
            assert critical_snapshots == [
                (
                    25, native, 0, 33, 0, 34, 34,
                    *advance_script_pointer(read_script_snapshots[0], 7),
                ),
            ], (
                "native identity/hit/PP/script pointer at critical dispatch",
                context, critical_snapshots, read_script_snapshots
            )
            assert reset_crit_calls == [True], (
                "critical handler did not reset prior critical state",
                context, reset_crit_calls
            )
            assert reset_crit_snapshots == [(25, native, 0)], (
                "native identity changed entering ResetCrit",
                context, reset_crit_snapshots
            )
            assert critical_opp_ability_checks == [True, True], (
                "critical path did not run anti-crit and Unnerve opponent "
                "ability checks", context, critical_opp_ability_checks
            )
            assert all(
                snap == (25, native, 0, 33)
                for snap in critical_opp_ability_snapshots
            ), (
                "native identity changed during critical opponent ability checks",
                context, critical_opp_ability_snapshots
            )
            # Four real checks occur: the handler's direct check, one
            # inside each of the two GetUserItem calls, and one inside
            # GetTrueUserAbility for the Super Luck lookup.
            assert future_sight_calls == [True, True, True, True], (
                "critical path Future Sight user-check count",
                context, future_sight_calls
            )
            assert all(
                snap == (25, native, 0, 0)
                for snap in future_sight_snapshots
            ), (
                "native identity/Future Sight state changed unexpectedly",
                context, future_sight_snapshots
            )
            assert user_item_after_unnerve_calls == [True], (
                "critical path skipped held-item-after-Unnerve check",
                context, user_item_after_unnerve_calls
            )
            assert user_item_after_unnerve_snapshots == [(25, native, 0)], (
                "native identity/item changed entering item check",
                context, user_item_after_unnerve_snapshots
            )
            assert user_item_calls == [True, True], (
                "critical path did not perform both held-item reads",
                context, user_item_calls
            )
            assert all(
                snap == (25, native, 0) for snap in user_item_snapshots
            ), (
                "native identity/item changed during critical item reads",
                context, user_item_snapshots
            )
            assert user_valid_item_calls == [], (
                "zero held item unexpectedly entered species-valid item path",
                context, user_valid_item_calls
            )
            assert critical_user_ability_checks == [True], (
                "critical path skipped Super Luck user ability check",
                context, critical_user_ability_checks
            )
            assert critical_user_ability_snapshots == [(25, native, 0, 33)], (
                "native identity changed during critical user ability check",
                context, critical_user_ability_snapshots
            )
            assert critical_affection_calls == [True], (
                "critical path skipped affection check",
                context, critical_affection_calls
            )
            assert critical_random_calls == [24], (
                "critical path did not request the base 0-23 roll",
                context, critical_random_calls
            )
            assert read_script_snapshots[7][:5] == (25, native, 0, 33, 0), (
                "native/move/hit state changed after non-critical calculation",
                context, read_script_snapshots
            )
            assert read_script_snapshots[7][5:] == advance_script_pointer(
                read_script_snapshots[0], 7
            ), (
                "script pointer did not advance through seven real commands",
                context, read_script_snapshots
            )
            assert mem[addr("wMoveHitState")] & 1 == 0, (
                "deterministic critical path unexpectedly set critical bit",
                context, mem[addr("wMoveHitState")]
            )
            assert mem[addr("wPlayerUsedMoves")] == 33, (
                "DisplayUsedMoveText did not record Tackle as used", context,
                mem[addr("wPlayerUsedMoves")]
            )
            assert usedmovetext_result_snapshots == [33], (
                "DisplayUsedMoveText did not publish Tackle move grammar at "
                "the usedmovetext boundary",
                context, usedmovetext_result_snapshots
            )
            assert mem[addr("wPartyMon1PP")] == 34, (
                "doturn did not decrement persistent Tackle PP", context,
                mem[addr("wPartyMon1PP")]
            )
            assert mem[addr("wBattleMonPP")] == 34, (
                "doturn did not synchronize active Tackle PP", context,
                mem[addr("wBattleMonPP")]
            )
            assert damagestats_calls == [True], (
                "eighth real battle-command dispatch count", context,
                damagestats_calls
            )
            assert damagestats_snapshots == [
                (
                    25, native, 0, 33, 0, 34, 34,
                    *advance_script_pointer(read_script_snapshots[0], 8),
                ),
            ], (
                "native identity/hit/PP/script pointer at damagestats dispatch",
                context, damagestats_snapshots, read_script_snapshots
            )
            assert damage_reset_calls == [True], (
                "damagestats did not reset damage state", context,
                damage_reset_calls
            )
            assert damage_reset_snapshots == [(25, native, 0)], (
                "native identity changed during ResetDamage", context,
                damage_reset_snapshots
            )
            assert damage_opponent_attr_calls, (
                "physical damagestats did not read an opponent attribute",
                context, damage_opponent_attr_calls
            )
            assert (25, native, 0, addr("wBattleMonDefense")) in (
                damage_opponent_attr_snapshots
            ), (
                "physical damagestats never selected opponent Defense",
                context, damage_opponent_attr_snapshots
            )
            assert all(
                snap[:3] == (25, native, 0)
                for snap in damage_opponent_attr_snapshots
            ), (
                "native identity changed during opponent attribute reads",
                context, damage_opponent_attr_snapshots
            )
            assert damage_user_attr_calls, (
                "physical damagestats did not read a user attribute",
                context, damage_user_attr_calls
            )
            assert (25, native, 0, addr("wBattleMonAttack")) in (
                damage_user_attr_snapshots
            ), (
                "physical damagestats never selected user Attack",
                context, damage_user_attr_snapshots
            )
            # GetOpponentMonAttr temporarily flips hBattleTurn while
            # resolving the opponent's stat through the shared user-attribute
            # helper. The important invariant here is that neither native
            # identity changes across either perspective.
            assert all(
                snap[:2] == (25, native)
                for snap in damage_user_attr_snapshots
            ), (
                "native identity changed during user attribute reads",
                context, damage_user_attr_snapshots
            )
            assert damagestats_future_sight_calls, (
                "damagestats skipped Future Sight user resolution", context,
                damagestats_future_sight_calls
            )
            assert all(
                snap[0] == 25 and snap[1] == native and snap[3] == 0
                for snap in damagestats_future_sight_snapshots
            ), (
                "native identity changed in damagestats Future Sight checks",
                context, damagestats_future_sight_snapshots
            )
            assert any(
                snap[2] == 0 for snap in damagestats_future_sight_snapshots
            ), (
                "damagestats never resolved the player-side Future Sight user",
                context, damagestats_future_sight_snapshots
            )
            assert damage_screen_calls == [True], (
                "physical damagestats skipped opponent screen handling", context,
                damage_screen_calls
            )
            assert damage_screen_snapshots == [(25, native, 0)], (
                "native identity changed entering screen handling", context,
                damage_screen_snapshots
            )
            assert len(true_user_party_attr_calls) >= 3, (
                "damagestats did not perform its item and level party reads",
                context, true_user_party_attr_calls
            )
            assert all(
                snap[:3] == (25, native, 0)
                for snap in true_user_party_attr_snapshots
            ), (
                "native identity changed during true-user level lookup",
                context, true_user_party_attr_snapshots
            )
            assert damagestats_result_snapshots, (
                "missing damagestats result at ninth script read", context
            )
            result = damagestats_result_snapshots[0]
            assert result[:2] == (25, native), (
                "native identity changed after damagestats", context, result
            )
            assert result[2] > 0 and result[3] > 0, (
                "damagestats returned zero Attack/Defense", context, result
            )
            assert result[4:] == (40, 30), (
                "damagestats returned wrong Tackle power/player level",
                context, result
            )
            assert read_script_snapshots[8][:5] == (25, native, 0, 33, 0), (
                "native/move/hit state changed after damagestats",
                context, read_script_snapshots
            )
            assert read_script_snapshots[8][5:] == advance_script_pointer(
                read_script_snapshots[0], 8
            ), (
                "script pointer did not advance through eight real commands",
                context, read_script_snapshots
            )
            assert damagecalc_calls == [True], (
                "ninth real battle-command dispatch count", context,
                damagecalc_calls
            )
            assert damagecalc_snapshots == [
                (
                    25, native, 0, 33, 0,
                    result[2], result[3], 40, 30,
                    *advance_script_pointer(read_script_snapshots[0], 9),
                ),
            ], (
                "native identity or damagestats inputs changed entering damagecalc",
                context, damagecalc_snapshots, result
            )
            assert damagecalc_result_snapshots == [
                (25, native, 0, 33, 0, 14),
            ], (
                "real base damage formula did not produce expected neutral "
                "Tackle damage or changed native identity",
                context, damagecalc_result_snapshots
            )
            assert read_script_snapshots[9][:5] == (25, native, 0, 33, 0), (
                "native/move/hit state changed after damagecalc",
                context, read_script_snapshots
            )
            assert read_script_snapshots[9][5:] == advance_script_pointer(
                read_script_snapshots[0], 9
            ), (
                "script pointer did not advance through nine real commands",
                context, read_script_snapshots
            )
            assert stab_calls == [True], (
                "tenth real battle-command dispatch count", context, stab_calls
            )
            assert stab_snapshots == [
                (
                    25, native, 0, 33, 0, 14,
                    *advance_script_pointer(read_script_snapshots[0], 10),
                ),
            ], (
                "native identity/base damage changed entering STAB",
                context, stab_snapshots
            )
            assert stab_type_matchup_calls == [True], (
                "STAB command skipped real type-matchup calculation",
                context, stab_type_matchup_calls
            )
            assert stab_type_matchup_snapshots == [(25, native, 0, 33)], (
                "native identity changed entering type-matchup calculation",
                context, stab_type_matchup_snapshots
            )
            assert stab_weather_calls == [True], (
                "STAB command skipped real weather modifier path",
                context, stab_weather_calls
            )
            assert stab_weather_snapshots == [(25, native, 0, 0)], (
                "native identity/weather changed entering weather modifiers",
                context, stab_weather_snapshots
            )
            assert stab_result_snapshots == [
                (25, native, 0, 33, 0x10, 0x18, 0, 21),
            ], (
                "real STAB/type handling did not produce neutral 1.5x Tackle "
                "damage or changed native identity",
                context, stab_result_snapshots
            )
            assert bytes(
                mem[addr("wCurDamage"):addr("wCurDamage") + 2]
            ) == bytes([0, 21]), (
                "STAB did not publish expected 21 damage", context,
                bytes(mem[addr("wCurDamage"):addr("wCurDamage") + 2])
            )
            assert read_script_snapshots[10][:5] == (25, native, 0, 33, 0), (
                "native/move/hit state changed after STAB",
                context, read_script_snapshots
            )
            assert read_script_snapshots[10][5:] == advance_script_pointer(
                read_script_snapshots[0], 10
            ), (
                "script pointer did not advance through ten real commands",
                context, read_script_snapshots
            )
            assert not applydamage_calls, (
                "HP application executed past terminal boundary", context
            )
            assert bytes(
                mem[addr("wBattleMonHP"):addr("wBattleMonHP") + 2]
            ) == bytes([0, 100]), ("player HP changed", context)
            assert bytes(
                mem[addr("wEnemyMonHP"):addr("wEnemyMonHP") + 2]
            ) == bytes([0, 100]), ("enemy HP changed", context)
            assert read_native("wBattleMonNativeSpecies") == 25, context
            assert read_native("wEnemyMonNativeSpecies") == native, context
            assert mem[addr("wTotalBattleTurns")] == 1, context
            assert mem[addr("hBattleTurn")] == 0, context
            assert mem[addr("wBattlePlayerAction")] == 0, context
            assert mem[addr("wPlayerSwitchTarget")] == 0, context
            assert mem[addr("wEnemySwitchTarget")] == 0, context
            assert mem[addr("wBattleEnded")] == 1, context
            assert mem[addr("wCurPlayerMove")] == 33, context
            assert mem[addr("wCurMoveNum")] == 0, context

            count += 1

        print(
            f"PASS: {count} native STAB cases; real checkobedience -> "
            "usedmovetext -> doturn/BattleConsumePP -> hastarget -> checkhit -> "
            "checkpriority -> critical -> damagestats -> damagecalc (14) -> "
            "real neutral type matchup + 1.5x STAB (21) -> eleventh "
            "script-byte terminal boundary before damagevariation or HP change"
        )
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
