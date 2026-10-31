"""Native enemy checkpriority -> critical boundary regression.

Execute the validated player-first wild Tackle path through the enemy's real
checkobedience, usedmovetext, doturn, hastarget, and checkhit commands. Then
dispatch the enemy's real BattleCommand_checkpriority through the ordinary
living-target, normal-priority Tackle path with the player's validated Pressure
state intact. Verify native identities, enemy Tackle/PP state, priority and
ability lookups, and the prior hit result survive. Finally execute the seventh
real enemy ReadMoveScriptByte and stop after it returns critical ($05), before
enemy critical-hit logic executes.
"""
import argparse
from pathlib import Path

from pyboy import PyBoy


PRESSURE = 43


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
    perform_move_bank, perform_move_addr = symbols["PerformMove"]
    perform_move_original = data[offset("PerformMove"):offset("PerformMove") + 6]
    read_dispatch_bank, read_dispatch_addr = symbols["DoMove.ReadMoveEffectCommand"]
    # The first instruction at ReadMoveEffectCommand is a 3-byte CALL to
    # ReadMoveScriptByte. Save the following dispatch bytes so each case can
    # install a post-read stop without modifying the read itself.
    read_dispatch_original = data[
        offset("DoMove.ReadMoveEffectCommand") + 3:
        offset("DoMove.ReadMoveEffectCommand") + 12
    ]
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
    enemy_check_turn_snapshots = []
    enemy_update_move_data_snapshots = []
    initialize_move_calls = []
    enemy_initialize_move_snapshots = []
    read_script_calls = []
    enemy_read_snapshots = []
    read_script_snapshots = []
    checkobedience_calls = []
    checkobedience_snapshots = []
    enemy_checkobedience_snapshots = []
    usedmovetext_calls = []
    usedmovetext_snapshots = []
    usedmovetext_result_snapshots = []
    enemy_usedmovetext_snapshots = []
    enemy_usedmovetext_result_snapshots = []
    enemy_usedmovetext_text_snapshots = []
    display_used_move_calls = []
    display_used_move_snapshots = []
    enemy_display_used_move_snapshots = []
    used_move_tilemap_calls = []
    usedmovetext_active = [False]
    doturn_calls = []
    doturn_snapshots = []
    enemy_doturn_snapshots = []
    enemy_doturn_result_snapshots = []
    consume_pp_calls = []
    consume_pp_snapshots = []
    enemy_consume_pp_snapshots = []
    hastarget_calls = []
    hastarget_snapshots = []
    enemy_hastarget_snapshots = []
    enemy_hastarget_result_snapshots = []
    target_fainted_checks = []
    target_fainted_snapshots = []
    enemy_target_fainted_snapshots = []
    target_ability_checks = []
    target_ability_snapshots = []
    enemy_target_ability_snapshots = []
    hastarget_active = [False]
    checkhit_active = [False]
    enemy_checkhit_active = [False]
    checkhit_calls = []
    checkhit_snapshots = []
    checkhit_result_snapshots = []
    enemy_checkhit_snapshots = []
    enemy_checkhit_result_snapshots = []
    affection_checks = []
    enemy_affection_checks = []
    stat_change_mod_calls = []
    stat_change_mod_snapshots = []
    enemy_stat_change_mod_snapshots = []
    accuracy_ability_calls = []
    accuracy_ability_snapshots = []
    enemy_accuracy_ability_snapshots = []
    accuracy_user_ability_checks = []
    accuracy_user_ability_snapshots = []
    enemy_accuracy_user_ability_snapshots = []
    accuracy_opp_ability_checks = []
    accuracy_opp_ability_snapshots = []
    enemy_accuracy_opp_ability_snapshots = []
    accuracy_random_calls = []
    enemy_accuracy_random_calls = []
    priority_active = [False]
    enemy_priority_active = [False]
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
    enemy_checkpriority_snapshots = []
    enemy_priority_fainted_snapshots = []
    enemy_move_priority_snapshots = []
    enemy_priority_user_ability_snapshots = []
    enemy_priority_opp_ability_snapshots = []
    enemy_priority_result_snapshots = []
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
    damagevariation_active = [False]
    damagevariation_calls = []
    damagevariation_snapshots = []
    damagevariation_random_calls = []
    damagevariation_result_snapshots = []
    moveanim_active = [False]
    moveanim_calls = []
    moveanim_snapshots = []
    moveanim_lowersub_calls = []
    moveanim_nosub_calls = []
    moveanim_raisesub_calls = []
    moveanim_fx_calls = []
    moveanim_fx_snapshots = []
    moveanim_result_snapshots = []
    failuretext_active = [False]
    failuretext_calls = []
    failuretext_snapshots = []
    failure_result_text_calls = []
    failuretext_result_snapshots = []
    applydamage_active = [False]
    applydamage_calls = []
    applydamage_snapshots = []
    applydamage_affection_calls = []
    applydamage_item_calls = []
    applydamage_ability_calls = []
    applydamage_reset_subhit_calls = []
    applydamage_check_sub_calls = []
    applydamage_take_damage_calls = []
    applydamage_deal_damage_calls = []
    applydamage_subtract_hp_calls = []
    applydamage_hud_calls = []
    applydamage_refresh_huds_calls = []
    applydamage_result_snapshots = []
    criticaltext_active = [False]
    criticaltext_calls = []
    criticaltext_snapshots = []
    criticaltext_checkcrit_calls = []
    criticaltext_checkcrit_snapshots = []
    criticaltext_delay_calls = []
    criticaltext_delay_snapshots = []
    criticaltext_result_snapshots = []
    supereffectivetext_active = [False]
    supereffectivetext_calls = []
    supereffectivetext_snapshots = []
    supereffectivetext_text_calls = []
    supereffectivetext_item_calls = []
    supereffectivetext_result_snapshots = []
    postfainteffects_active = [False]
    postfainteffects_calls = []
    postfainteffects_snapshots = []
    postfaint_fainted_calls = []
    postfainteffects_result_snapshots = []
    posthiteffects_active = [False]
    posthiteffects_calls = []
    posthiteffects_snapshots = []
    posthiteffects_result_snapshots = []
    endmove_effect_calls = []
    endmove_throat_spray_calls = []
    endmove_power_herb_calls = []
    cleanup_active = [False]
    cleanup_tick_calls = []
    cleanup_tilemap_calls = []
    resolve_active = [False]
    resolve_faints_calls = []
    resolve_player_writeback_calls = []
    resolve_enemy_writeback_calls = []
    resolve_enemy_fainted_calls = []
    resolve_fit_party_calls = []
    resolve_faint_animation_calls = []
    resolve_give_experience_calls = []
    resolve_victory_music_calls = []
    deferred_switch_calls = []
    force_deferred_switch_calls = []
    reset_ability_ignorance_calls = []
    second_perform_move_calls = []
    enemy_move_read_calls = []
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
            label, hex(regs.PC), hex(regs.SP),
            "reads", len(read_script_calls),
            "apply", len(applydamage_calls),
            "take", len(applydamage_take_damage_calls),
            "deal", len(applydamage_deal_damage_calls),
            "subtract", len(applydamage_subtract_hp_calls),
            "hp_hud", len(applydamage_hud_calls),
            "refresh", len(applydamage_refresh_huds_calls),
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

    def observe_enemy_action(_):
        parse_enemy_calls.append(True)
        # Deterministic wild-opponent move selection. Keep the player move
        # distinct later so hBattleTurn=1 must select this enemy-side Tackle.
        mem[addr("wCurEnemyMoveNum")] = 0
        mem[addr("wCurEnemyMove")] = 33
        # Seed the ordinary enemy PP path only. doturn/BattleConsumePP remain
        # real and must decrement both active and OT-party slot 0 from 35.
        mem[addr("wEnemyMonPP")] = 35
        mem[addr("wOTPartyMon1PP")] = 35
        mem[addr("wEnemyCharging")] = 0
        mem[addr("wEnemySubStatus3")] = 0

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

    def observe_perform_move_boundary(_):
        perform_move_calls.append(True)
        snapshot = (
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
            mem[addr("wCurPlayerMove")],
        )
        perform_move_snapshots.append(snapshot)
        if len(perform_move_calls) == 2:
            second_perform_move_calls.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wEnemyGoesFirst")],
                mem[addr("wCurPlayerMove")],
                mem[addr("wCurEnemyMove")],
                mem[addr("wCurEnemyMoveNum")],
                mem[addr("wDamageTaken")],
                mem[addr("wDamageTaken") + 1],
                mem[addr("wDeferredSwitch")],
                mem[addr("wMoveState")],
                mem[addr("wBattleEnded")],
            ))

    def observe_enemy_move_read(_):
        if len(perform_move_calls) == 2:
            enemy_move_read_calls.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                regs.A,
                mem[addr("wCurPlayerMove")],
                mem[addr("wCurEnemyMove")],
                mem[addr("wCurEnemyMoveNum")],
                mem[addr("wDamageTaken")],
                mem[addr("wDamageTaken") + 1],
            ))

    def observe_update_move_data(_):
        update_move_data_calls.append(True)
        if len(perform_move_calls) == 2 and (mem[addr("hBattleTurn")] & 1):
            enemy_update_move_data_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
                mem[addr("wCurEnemyMove")],
                mem[addr("wCurEnemyMoveNum")],
                mem[addr("wMoveHitState")],
            ))

    def observe_check_turn(_):
        check_turn_calls.append(True)
        if len(perform_move_calls) == 2 and (mem[addr("hBattleTurn")] & 1):
            enemy_check_turn_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
                mem[addr("wCurEnemyMove")],
                mem[addr("wCurEnemyMoveNum")],
                mem[addr("wMoveHitState")],
                mem[addr("wMoveState")],
            ))

    def observe_initialize_move(_):
        initialize_move_calls.append(True)
        if len(perform_move_calls) == 2 and (mem[addr("hBattleTurn")] & 1):
            enemy_initialize_move_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
                mem[addr("wCurEnemyMove")],
                mem[addr("wCurEnemyMoveNum")],
                mem[addr("wMoveHitState")],
            ))

    def observe_read_script(_):
        read_script_calls.append(True)
        snapshot = (
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
            mem[addr("wCurPlayerMove")],
            mem[addr("wMoveHitState")],
            mem[addr("wBattleScriptBufferLoc")],
            mem[addr("wBattleScriptBufferLoc") + 1],
        )
        read_script_snapshots.append(snapshot)
        if len(perform_move_calls) == 2 and (mem[addr("hBattleTurn")] & 1):
            enemy_read_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
                mem[addr("wCurEnemyMove")],
                mem[addr("wCurEnemyMoveNum")],
                mem[addr("wMoveHitState")],
                mem[addr("wMoveState")],
                mem[addr("wBattleScriptBufferLoc")],
                mem[addr("wBattleScriptBufferLoc") + 1],
            ))
        # The fifth read is the real checkhit boundary; the sixth is the real
        # checkpriority boundary; the seventh is the real critical boundary;
        # the eighth is the real damagestats boundary; the ninth is the real
        # damagecalc boundary; the tenth is the real STAB boundary; and the
        # eleventh is the real damagevariation boundary; and the twelfth is
        # the real moveanim boundary; the thirteenth is the real failuretext
        # boundary; and the fourteenth is the real applydamage boundary. The
        # fifteenth real script-byte read sees the test-only endturn byte in
        # place of criticaltext and ends the outer battle loop.
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
        if len(read_script_calls) == 12:
            damagevariation_result_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
                mem[addr("wCurDamage")],
                mem[addr("wCurDamage") + 1],
            ))
            damagevariation_active[0] = False
        if len(read_script_calls) == 13:
            moveanim_result_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
                mem[addr("wCurDamage")],
                mem[addr("wCurDamage") + 1],
                mem[addr("wBattleAnimParam")],
            ))
            moveanim_active[0] = False
        if len(read_script_calls) == 14:
            failuretext_result_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
                mem[addr("wAttackMissed")],
                mem[addr("wCurDamage")],
                mem[addr("wCurDamage") + 1],
            ))
            failuretext_active[0] = False
        if len(read_script_calls) == 15:
            applydamage_result_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
                mem[addr("wAttackMissed")],
                mem[addr("wCurDamage")],
                mem[addr("wCurDamage") + 1],
                mem[addr("wEnemyMonHP")],
                mem[addr("wEnemyMonHP") + 1],
                mem[addr("wDamageTaken")],
                mem[addr("wDamageTaken") + 1],
            ))
            applydamage_active[0] = False
        if len(read_script_calls) == 16:
            criticaltext_result_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
                mem[addr("wMoveHitState")],
                mem[addr("wEnemyMonHP")],
                mem[addr("wEnemyMonHP") + 1],
                mem[addr("wDamageTaken")],
                mem[addr("wDamageTaken") + 1],
            ))
            criticaltext_active[0] = False
        if len(read_script_calls) == 17:
            supereffectivetext_result_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
                mem[addr("wTypeModifier")],
                mem[addr("wEnemyMonHP")],
                mem[addr("wEnemyMonHP") + 1],
                mem[addr("wDamageTaken")],
                mem[addr("wDamageTaken") + 1],
            ))
            supereffectivetext_active[0] = False
        if len(read_script_calls) == 18:
            postfainteffects_result_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("wEnemyMonHP")],
                mem[addr("wEnemyMonHP") + 1],
                mem[addr("wDamageTaken")],
                mem[addr("wDamageTaken") + 1],
            ))
            postfainteffects_active[0] = False
        if len(read_script_calls) == 19:
            posthiteffects_result_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wEnemyMonHP")],
                mem[addr("wEnemyMonHP") + 1],
                mem[addr("wDamageTaken")],
                mem[addr("wDamageTaken") + 1],
                mem[addr("wAttackMissed")],
            ))
            posthiteffects_active[0] = False
        if len(read_script_calls) == 22:
            enemy_usedmovetext_result_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
                mem[addr("wCurEnemyMove")],
                mem[addr("wCurEnemyMoveNum")],
                mem[addr("wMoveGrammar")],
                mem[addr("wLastEnemyMove")],
                mem[addr("wLastEnemyCounterMove")],
                mem[addr("wAlreadyDisobeyed")],
                tuple(mem[addr("wPlayerUsedMoves"):addr("wPlayerUsedMoves") + 4]),
            ))
        if len(read_script_calls) == 23:
            enemy_doturn_result_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
                mem[addr("wCurEnemyMove")],
                mem[addr("wCurEnemyMoveNum")],
                mem[addr("wPartyMon1PP")],
                mem[addr("wBattleMonPP")],
                mem[addr("wOTPartyMon1PP")],
                mem[addr("wEnemyMonPP")],
                mem[addr("wBattleScriptBufferLoc")],
                mem[addr("wBattleScriptBufferLoc") + 1],
            ))

        if len(read_script_calls) == 24:
            enemy_hastarget_result_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
                mem[addr("wCurEnemyMove")],
                mem[addr("wCurEnemyMoveNum")],
                mem[addr("wPartyMon1PP")],
                mem[addr("wBattleMonPP")],
                mem[addr("wOTPartyMon1PP")],
                mem[addr("wEnemyMonPP")],
                mem[addr("wPlayerAbility")],
                mem[addr("wBattleScriptBufferLoc")],
                mem[addr("wBattleScriptBufferLoc") + 1],
            ))
            hastarget_active[0] = False
        if len(read_script_calls) == 25:
            enemy_checkhit_result_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
                mem[addr("wCurEnemyMove")],
                mem[addr("wCurEnemyMoveNum")],
                mem[addr("wPartyMon1PP")],
                mem[addr("wBattleMonPP")],
                mem[addr("wOTPartyMon1PP")],
                mem[addr("wEnemyMonPP")],
                mem[addr("wPlayerAbility")],
                mem[addr("wAttackMissed")],
                tuple(mem[addr("hMultiplicand"):addr("hMultiplicand") + 3]),
                mem[addr("wBattleScriptBufferLoc")],
                mem[addr("wBattleScriptBufferLoc") + 1],
            ))
            enemy_checkhit_active[0] = False
        if len(read_script_calls) == 26:
            enemy_priority_result_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
                mem[addr("wCurEnemyMove")],
                mem[addr("wCurEnemyMoveNum")],
                mem[addr("wPartyMon1PP")],
                mem[addr("wBattleMonPP")],
                mem[addr("wOTPartyMon1PP")],
                mem[addr("wEnemyMonPP")],
                mem[addr("wPlayerAbility")],
                mem[addr("wAttackMissed")],
                mem[addr("wTypeMatchup")],
                mem[addr("wTypeModifier")],
                mem[addr("wBattleScriptBufferLoc")],
                mem[addr("wBattleScriptBufferLoc") + 1],
            ))
            enemy_priority_active[0] = False

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
        if len(perform_move_calls) == 2 and (mem[addr("hBattleTurn")] & 1):
            enemy_checkobedience_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
                mem[addr("wCurEnemyMove")],
                mem[addr("wCurEnemyMoveNum")],
                mem[addr("wMoveState")],
                mem[addr("wBattleScriptBufferLoc")],
                mem[addr("wBattleScriptBufferLoc") + 1],
                mem[addr("wBattleEnded")],
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
        usedmovetext_active[0] = True
        if len(perform_move_calls) == 2 and (mem[addr("hBattleTurn")] & 1):
            enemy_usedmovetext_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
                mem[addr("wCurEnemyMove")],
                mem[addr("wCurEnemyMoveNum")],
                mem[addr("wMoveState")],
                mem[addr("wBattleScriptBufferLoc")],
                mem[addr("wBattleScriptBufferLoc") + 1],
                tuple(mem[addr("wPlayerUsedMoves"):addr("wPlayerUsedMoves") + 4]),
            ))

    def observe_display_used_move(_):
        display_used_move_calls.append(True)
        display_used_move_snapshots.append((
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
            mem[addr("wCurPlayerMove")],
        ))
        if len(perform_move_calls) == 2 and (mem[addr("hBattleTurn")] & 1):
            enemy_display_used_move_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
                mem[addr("wCurEnemyMove")],
                mem[addr("wMoveState")],
            ))

    def observe_used_move_tilemap(_):
        if usedmovetext_active[0]:
            used_move_tilemap_calls.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wMoveGrammar")],
                mem[addr("wLastPlayerMove")],
                mem[addr("wLastEnemyMove")],
                mem[addr("wLastPlayerCounterMove")],
                mem[addr("wLastEnemyCounterMove")],
            ))
            usedmovetext_active[0] = False

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
        if len(perform_move_calls) == 2 and (mem[addr("hBattleTurn")] & 1):
            enemy_doturn_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
                mem[addr("wCurEnemyMove")],
                mem[addr("wCurEnemyMoveNum")],
                mem[addr("wPartyMon1PP")],
                mem[addr("wBattleMonPP")],
                mem[addr("wOTPartyMon1PP")],
                mem[addr("wEnemyMonPP")],
                mem[addr("wEnemyCharging")],
                mem[addr("wEnemySubStatus3")],
                mem[addr("wBattleScriptBufferLoc")],
                mem[addr("wBattleScriptBufferLoc") + 1],
                mem[addr("wBattleEnded")],
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
        if len(perform_move_calls) == 2 and (mem[addr("hBattleTurn")] & 1):
            enemy_consume_pp_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
                mem[addr("wCurEnemyMove")],
                mem[addr("wCurEnemyMoveNum")],
                mem[addr("wPartyMon1PP")],
                mem[addr("wBattleMonPP")],
                mem[addr("wOTPartyMon1PP")],
                mem[addr("wEnemyMonPP")],
            ))

    def observe_hastarget(_):
        hastarget_active[0] = True
        if len(perform_move_calls) == 2 and (mem[addr("hBattleTurn")] & 1):
            # Exercise the real Pressure fallthrough on the enemy turn.
            mem[addr("wPlayerAbility")] = PRESSURE
            enemy_hastarget_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
                mem[addr("wCurEnemyMove")],
                mem[addr("wCurEnemyMoveNum")],
                mem[addr("wBattleMonHP")],
                mem[addr("wBattleMonHP") + 1],
                mem[addr("wEnemyMonHP")],
                mem[addr("wEnemyMonHP") + 1],
                mem[addr("wPartyMon1PP")],
                mem[addr("wBattleMonPP")],
                mem[addr("wOTPartyMon1PP")],
                mem[addr("wEnemyMonPP")],
                mem[addr("wPlayerAbility")],
                mem[addr("wBattleScriptBufferLoc")],
                mem[addr("wBattleScriptBufferLoc") + 1],
                mem[addr("wBattleEnded")],
            ))
            # Unlike the previous checkpoint, do not install a post-read
            # stop here: let the fifth enemy command dispatch checkhit for real.
        else:
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
            if len(perform_move_calls) == 2 and (mem[addr("hBattleTurn")] & 1):
                enemy_target_fainted_snapshots.append((
                    read_native("wBattleMonNativeSpecies"),
                    read_native("wEnemyMonNativeSpecies"),
                    mem[addr("hBattleTurn")],
                    mem[addr("wBattleMonHP")],
                    mem[addr("wBattleMonHP") + 1],
                    mem[addr("wEnemyMonHP")],
                    mem[addr("wEnemyMonHP") + 1],
                ))
            else:
                target_fainted_checks.append(True)
                target_fainted_snapshots.append(snapshot)
        if enemy_priority_active[0]:
            enemy_priority_fainted_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wBattleMonHP")],
                mem[addr("wBattleMonHP") + 1],
                mem[addr("wEnemyMonHP")],
                mem[addr("wEnemyMonHP") + 1],
            ))
        elif priority_active[0]:
            priority_fainted_checks.append(True)
            priority_fainted_snapshots.append(snapshot)
        if postfainteffects_active[0]:
            postfaint_fainted_calls.append(snapshot)

    def observe_target_ability(_):
        if applydamage_active[0]:
            applydamage_ability_calls.append(True)
        snapshot = (
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
            mem[addr("wCurPlayerMove")],
        )
        if hastarget_active[0]:
            if len(perform_move_calls) == 2 and (mem[addr("hBattleTurn")] & 1):
                enemy_target_ability_snapshots.append((
                    read_native("wBattleMonNativeSpecies"),
                    read_native("wEnemyMonNativeSpecies"),
                    mem[addr("hBattleTurn")],
                    mem[addr("wCurPlayerMove")],
                    mem[addr("wCurEnemyMove")],
                    mem[addr("wPlayerAbility")],
                ))
            else:
                target_ability_checks.append(True)
                target_ability_snapshots.append(snapshot)
        if enemy_checkhit_active[0]:
            enemy_accuracy_opp_ability_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
                mem[addr("wCurEnemyMove")],
                mem[addr("wPlayerAbility")],
                mem[addr("wEnemyAbility")],
            ))
        elif checkhit_active[0]:
            accuracy_opp_ability_checks.append(True)
            accuracy_opp_ability_snapshots.append(snapshot)
        if enemy_priority_active[0]:
            enemy_priority_opp_ability_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
                mem[addr("wCurEnemyMove")],
                mem[addr("wPlayerAbility")],
                mem[addr("wEnemyAbility")],
            ))
        elif priority_active[0]:
            priority_opp_ability_checks.append(True)
            priority_opp_ability_snapshots.append(snapshot)
        if critical_active[0]:
            critical_opp_ability_checks.append(True)
            critical_opp_ability_snapshots.append(snapshot)

    def observe_checkhit(_):
        enemy = len(perform_move_calls) == 2 and (mem[addr("hBattleTurn")] & 1)
        if enemy:
            enemy_checkhit_active[0] = True
            enemy_checkhit_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
                mem[addr("wCurEnemyMove")],
                mem[addr("wCurEnemyMoveNum")],
                mem[addr("wPartyMon1PP")],
                mem[addr("wBattleMonPP")],
                mem[addr("wOTPartyMon1PP")],
                mem[addr("wEnemyMonPP")],
                mem[addr("wPlayerAbility")],
                mem[addr("wBattleScriptBufferLoc")],
                mem[addr("wBattleScriptBufferLoc") + 1],
                mem[addr("wBattleEnded")],
            ))
        else:
            checkhit_active[0] = True

        # Force only the ordinary accuracy path inputs. The handler and all
        # accuracy math/ability lookups remain real. On the enemy path, retain
        # the player's Pressure state validated by hastarget; Pressure is not
        # an accuracy modifier and should survive this command unchanged.
        for label in (
            "wPlayerSubStatus1", "wPlayerSubStatus2",
            "wPlayerSubStatus3", "wPlayerSubStatus4",
            "wEnemySubStatus1", "wEnemySubStatus2",
            "wEnemySubStatus3", "wEnemySubStatus4",
        ):
            mem[addr(label)] = 0
        if enemy:
            mem[addr("wPlayerAbility")] = PRESSURE
            mem[addr("wEnemyAbility")] = 0
        else:
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

        if enemy:
            # Unlike the previous checkpoint, do not stop after checkhit.
            # Let the sixth enemy command dispatch checkpriority for real.
            pass
        else:
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
        if enemy_checkhit_active[0]:
            enemy_stat_change_mod_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
                mem[addr("wCurEnemyMove")],
                regs.B, regs.C,
                mem[addr("wEnemyAccLevel")],
                mem[addr("wPlayerEvaLevel")],
            ))
        elif checkhit_active[0]:
            stat_change_mod_calls.append(True)
            stat_change_mod_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("wPlayerAccLevel")],
                mem[addr("wEnemyEvaLevel")],
            ))

    def observe_accuracy_abilities(_):
        if enemy_checkhit_active[0]:
            enemy_accuracy_ability_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
                mem[addr("wCurEnemyMove")],
                mem[addr("wPlayerAbility")],
                mem[addr("wEnemyAbility")],
            ))
        elif checkhit_active[0]:
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
        if enemy_checkhit_active[0]:
            enemy_accuracy_user_ability_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
                mem[addr("wCurEnemyMove")],
                mem[addr("wPlayerAbility")],
                mem[addr("wEnemyAbility")],
            ))
        elif checkhit_active[0]:
            accuracy_user_ability_checks.append(True)
            accuracy_user_ability_snapshots.append(snapshot)
        if enemy_priority_active[0]:
            enemy_priority_user_ability_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
                mem[addr("wCurEnemyMove")],
                mem[addr("wPlayerAbility")],
                mem[addr("wEnemyAbility")],
            ))
        elif priority_active[0]:
            priority_user_ability_checks.append(True)
            priority_user_ability_snapshots.append(snapshot)
        if critical_active[0]:
            critical_user_ability_checks.append(True)
            critical_user_ability_snapshots.append(snapshot)

    def observe_move_priority(_):
        if enemy_priority_active[0]:
            enemy_move_priority_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
                mem[addr("wCurEnemyMove")],
                mem[addr("wPlayerAbility")],
                mem[addr("wEnemyAbility")],
            ))
        elif priority_active[0]:
            move_priority_calls.append(True)
            move_priority_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
            ))

    def observe_checkpriority(_):
        enemy = len(perform_move_calls) == 2 and (mem[addr("hBattleTurn")] & 1)
        if enemy:
            enemy_priority_active[0] = True
            enemy_checkpriority_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
                mem[addr("wCurEnemyMove")],
                mem[addr("wCurEnemyMoveNum")],
                mem[addr("wBattleMonHP")],
                mem[addr("wBattleMonHP") + 1],
                mem[addr("wEnemyMonHP")],
                mem[addr("wEnemyMonHP") + 1],
                mem[addr("wPartyMon1PP")],
                mem[addr("wBattleMonPP")],
                mem[addr("wOTPartyMon1PP")],
                mem[addr("wEnemyMonPP")],
                mem[addr("wPlayerAbility")],
                mem[addr("wAttackMissed")],
                mem[addr("wTypeMatchup")],
                mem[addr("wTypeModifier")],
                mem[addr("wBattleScriptBufferLoc")],
                mem[addr("wBattleScriptBufferLoc") + 1],
                mem[addr("wBattleEnded")],
            ))
            # checkpriority has already been read and dispatched. Stop after
            # the next real read returns Tackle's critical command ($05), so
            # the enemy priority body is real but enemy critical logic is not.
            stop = [
                0xEA,
                addr("wBattleEnded") & 0xff,
                addr("wBattleEnded") >> 8,
                0xC9,
            ]
            for i, value in enumerate(stop):
                mem[read_dispatch_bank, read_dispatch_addr + 3 + i] = value
        else:
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

    def observe_opponent_affection(_):
        if enemy_checkhit_active[0]:
            enemy_affection_checks.append(True)
        elif checkhit_active[0]:
            affection_checks.append(True)
        if applydamage_active[0]:
            applydamage_affection_calls.append(True)

    def observe_user_valid_item(_):
        if critical_active[0]:
            user_valid_item_calls.append(True)

    def observe_accuracy_random(_):
        # BattleRandomRange receives the exclusive upper bound in A.
        if enemy_checkhit_active[0]:
            enemy_accuracy_random_calls.append(regs.A)
        elif checkhit_active[0]:
            accuracy_random_calls.append(regs.A)
        if critical_active[0]:
            critical_random_calls.append(regs.A)
        if damagevariation_active[0]:
            damagevariation_random_calls.append(regs.A)

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

    def observe_damagevariation(_):
        damagevariation_active[0] = True
        damagevariation_calls.append(True)
        damagevariation_snapshots.append((
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
            mem[addr("wCurPlayerMove")],
            mem[addr("wCurDamage")],
            mem[addr("wCurDamage") + 1],
            mem[addr("wBattleScriptBufferLoc")],
            mem[addr("wBattleScriptBufferLoc") + 1],
        ))

    def observe_moveanim(_):
        moveanim_active[0] = True
        moveanim_calls.append(True)
        moveanim_snapshots.append((
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
            mem[addr("wCurPlayerMove")],
            mem[addr("wCurDamage")],
            mem[addr("wCurDamage") + 1],
            mem[addr("wBattleScriptBufferLoc")],
            mem[addr("wBattleScriptBufferLoc") + 1],
        ))

    def observe_moveanim_lowersub(_):
        if moveanim_active[0]:
            moveanim_lowersub_calls.append(True)

    def observe_moveanim_nosub(_):
        if moveanim_active[0]:
            moveanim_nosub_calls.append(True)

    def observe_moveanim_raisesub(_):
        if moveanim_active[0]:
            moveanim_raisesub_calls.append(True)

    def observe_moveanim_fx(_):
        if moveanim_active[0]:
            moveanim_fx_calls.append(True)
            moveanim_fx_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
                (regs.D << 8) | regs.E,
            ))

    def observe_failuretext(_):
        failuretext_active[0] = True
        failuretext_calls.append(True)
        failuretext_snapshots.append((
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
            mem[addr("wCurPlayerMove")],
            mem[addr("wAttackMissed")],
            mem[addr("wCurDamage")],
            mem[addr("wCurDamage") + 1],
            mem[addr("wBattleScriptBufferLoc")],
            mem[addr("wBattleScriptBufferLoc") + 1],
        ))

    def observe_failure_result_text(_):
        if failuretext_active[0]:
            failure_result_text_calls.append(True)

    def observe_applydamage(_):
        applydamage_active[0] = True
        applydamage_calls.append(True)
        applydamage_snapshots.append((
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
            mem[addr("wCurPlayerMove")],
            mem[addr("wAttackMissed")],
            mem[addr("wCurDamage")],
            mem[addr("wCurDamage") + 1],
            mem[addr("wEnemyMonHP")],
            mem[addr("wEnemyMonHP") + 1],
            mem[addr("wDamageTaken")],
            mem[addr("wDamageTaken") + 1],
            mem[addr("wBattleScriptBufferLoc")],
            mem[addr("wBattleScriptBufferLoc") + 1],
        ))

    def observe_applydamage_item(_):
        if applydamage_active[0]:
            applydamage_item_calls.append(True)

    def observe_applydamage_ability(_):
        if applydamage_active[0]:
            applydamage_ability_calls.append(True)

    def observe_applydamage_reset_subhit(_):
        if applydamage_active[0]:
            applydamage_reset_subhit_calls.append(True)

    def observe_applydamage_check_sub(_):
        if applydamage_active[0]:
            applydamage_check_sub_calls.append(True)

    def observe_applydamage_take_damage(_):
        if applydamage_active[0]:
            applydamage_take_damage_calls.append(True)

    def observe_applydamage_deal_damage(_):
        if applydamage_active[0]:
            applydamage_deal_damage_calls.append(True)

    def observe_applydamage_subtract_hp(_):
        if applydamage_active[0]:
            applydamage_subtract_hp_calls.append(True)

    def observe_applydamage_hud(_):
        if applydamage_active[0]:
            applydamage_hud_calls.append(True)

    def observe_applydamage_refresh_huds(_):
        if applydamage_active[0]:
            applydamage_refresh_huds_calls.append(True)

    def observe_criticaltext(_):
        criticaltext_active[0] = True
        criticaltext_calls.append(True)
        criticaltext_snapshots.append((
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
            mem[addr("wCurPlayerMove")],
            mem[addr("wMoveHitState")],
            mem[addr("wEnemyMonHP")],
            mem[addr("wEnemyMonHP") + 1],
            mem[addr("wDamageTaken")],
            mem[addr("wDamageTaken") + 1],
            mem[addr("wBattleScriptBufferLoc")],
            mem[addr("wBattleScriptBufferLoc") + 1],
        ))

    def observe_criticaltext_checkcrit(_):
        if criticaltext_active[0]:
            criticaltext_checkcrit_calls.append(True)
            criticaltext_checkcrit_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wMoveHitState")],
            ))

    def observe_criticaltext_delay(_):
        if criticaltext_active[0]:
            criticaltext_delay_calls.append(True)
            criticaltext_delay_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                regs.C,
            ))

    def observe_supereffectivetext(_):
        supereffectivetext_active[0] = True
        supereffectivetext_calls.append(True)
        supereffectivetext_snapshots.append((
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
            mem[addr("wCurPlayerMove")],
            mem[addr("wTypeModifier")],
            mem[addr("wEnemyMonHP")],
            mem[addr("wEnemyMonHP") + 1],
            mem[addr("wDamageTaken")],
            mem[addr("wDamageTaken") + 1],
            mem[addr("wBattleScriptBufferLoc")],
            mem[addr("wBattleScriptBufferLoc") + 1],
        ))

    def observe_supereffective_textbox(_):
        if supereffectivetext_active[0]:
            supereffectivetext_text_calls.append(True)
        if (
            usedmovetext_active[0]
            and len(perform_move_calls) == 2
            and (mem[addr("hBattleTurn")] & 1)
        ):
            enemy_usedmovetext_text_snapshots.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wCurPlayerMove")],
                mem[addr("wCurEnemyMove")],
                mem[addr("wMoveGrammar")],
                mem[addr("wLastEnemyMove")],
                mem[addr("wLastEnemyCounterMove")],
                mem[addr("wAlreadyDisobeyed")],
                regs.HL,
                tuple(mem[addr("wPlayerUsedMoves"):addr("wPlayerUsedMoves") + 4]),
            ))

    def observe_supereffective_item(_):
        if supereffectivetext_active[0]:
            supereffectivetext_item_calls.append(True)

    def observe_postfainteffects(_):
        postfainteffects_active[0] = True
        postfainteffects_calls.append(True)
        postfainteffects_snapshots.append((
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("wEnemyMonHP")],
            mem[addr("wEnemyMonHP") + 1],
            mem[addr("wDamageTaken")],
            mem[addr("wDamageTaken") + 1],
        ))

    def observe_posthiteffects(_):
        posthiteffects_active[0] = True
        posthiteffects_calls.append(True)
        posthiteffects_snapshots.append((
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
            mem[addr("wEnemyMonHP")],
            mem[addr("wEnemyMonHP") + 1],
            mem[addr("wDamageTaken")],
            mem[addr("wDamageTaken") + 1],
            mem[addr("wAttackMissed")],
        ))
        # Keep this checkpoint on the ordinary successful-hit path. The
        # command itself and its control flow remain real; only unrelated
        # reactive ability/item state is neutralized at the boundary.
        mem[addr("wBattleMonAbility")] = 0
        mem[addr("wEnemyAbility")] = 0
        mem[addr("wBattleMonItem")] = 0
        mem[addr("wEnemyMonItem")] = 0

    def observe_endmove_effects(_):
        endmove_effect_calls.append((
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
            mem[addr("wEnemyMonHP")],
            mem[addr("wEnemyMonHP") + 1],
            mem[addr("wDamageTaken")],
            mem[addr("wDamageTaken") + 1],
        ))

    def observe_endmove_throat_spray(_):
        endmove_throat_spray_calls.append((
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
        ))

    def observe_endmove_power_herb(_):
        endmove_power_herb_calls.append((
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
        ))
        # Seed only the state consumed by PerformMove's immediate cleanup.
        # The cleanup code itself remains real.
        cleanup_active[0] = True
        mem[addr("wPlayerSubStatus2")] |= 1 << 3  # SUBSTATUS_IN_ABILITY
        mem[addr("wEnemySubStatus2")] |= 1 << 3   # SUBSTATUS_IN_ABILITY
        mem[addr("wEnemySubStatus1")] |= (1 << 2) | (1 << 5)  # Protect/Endure
        mem[addr("wPlayerDisableCount")] = 5
        mem[addr("wPlayerEncoreCount")] = 4
        mem[addr("wEnemyDisableCount")] = 7
        mem[addr("wEnemyEncoreCount")] = 6

    def observe_cleanup_tick(_):
        if cleanup_active[0]:
            cleanup_tick_calls.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wPlayerSubStatus2")],
                mem[addr("wEnemySubStatus2")],
                mem[addr("wEnemySubStatus1")],
                mem[addr("wPlayerDisableCount")],
                mem[addr("wPlayerEncoreCount")],
                mem[addr("wEnemyDisableCount")],
                mem[addr("wEnemyEncoreCount")],
            ))

    def observe_cleanup_tilemap(_):
        if cleanup_active[0]:
            cleanup_tilemap_calls.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wPlayerSubStatus2")],
                mem[addr("wEnemySubStatus2")],
                mem[addr("wEnemySubStatus1")],
                mem[addr("wPlayerDisableCount")],
                mem[addr("wPlayerEncoreCount")],
                mem[addr("wEnemyDisableCount")],
                mem[addr("wEnemyEncoreCount")],
            ))

    def observe_resolve_faints(_):
        resolve_active[0] = True
        resolve_faints_calls.append((
            read_native("wBattleMonNativeSpecies"),
            read_native("wEnemyMonNativeSpecies"),
            mem[addr("hBattleTurn")],
            mem[addr("wPlayerSubStatus2")],
            mem[addr("wEnemySubStatus2")],
            mem[addr("wEnemySubStatus1")],
            mem[addr("wPlayerDisableCount")],
            mem[addr("wPlayerEncoreCount")],
            mem[addr("wEnemyDisableCount")],
            mem[addr("wEnemyEncoreCount")],
            mem[addr("wEnemyMonHP")],
            mem[addr("wEnemyMonHP") + 1],
            mem[addr("wDamageTaken")],
            mem[addr("wDamageTaken") + 1],
        ))
        cleanup_active[0] = False

    def observe_resolve_player_writeback(_):
        if resolve_active[0]:
            resolve_player_writeback_calls.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wBattleMonHP")],
                mem[addr("wBattleMonHP") + 1],
                mem[addr("wPartyMon1HP")],
                mem[addr("wPartyMon1HP") + 1],
                mem[addr("wBattleMonPP")],
                mem[addr("wPartyMon1PP")],
            ))

    def observe_resolve_enemy_writeback(_):
        if resolve_active[0]:
            resolve_enemy_writeback_calls.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wEnemyMonHP")],
                mem[addr("wEnemyMonHP") + 1],
                mem[addr("wOTPartyMon1HP")],
                mem[addr("wOTPartyMon1HP") + 1],
                mem[addr("wOTPartyMon1Species")],
                mem[addr("wOTPartyMon1Form")],
            ))

    def observe_resolve_enemy_fainted(_):
        if resolve_active[0]:
            resolve_enemy_fainted_calls.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wEnemyMonHP")],
                mem[addr("wEnemyMonHP") + 1],
            ))

    def observe_resolve_fit_party(_):
        if resolve_active[0]:
            resolve_fit_party_calls.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wPartyCount")],
                mem[addr("wPartyMon1HP")],
                mem[addr("wPartyMon1HP") + 1],
            ))

    def observe_resolve_faint_animation(_):
        if resolve_active[0]:
            resolve_faint_animation_calls.append(True)

    def observe_resolve_give_experience(_):
        if resolve_active[0]:
            resolve_give_experience_calls.append(True)

    def observe_resolve_victory_music(_):
        if resolve_active[0]:
            resolve_victory_music_calls.append(True)

    def observe_deferred_switch(_):
        if resolve_active[0]:
            deferred_switch_calls.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wDeferredSwitch")],
                mem[addr("wBattleEnded")],
            ))
            # Bits 2 and 6 are MOVESTATE_IGNOREABIL and
            # MOVESTATE_OPP_IGNOREABIL. Preserve other sentinel bits.
            mem[addr("wMoveState")] = 0x55

    def observe_force_deferred_switch(_):
        if resolve_active[0]:
            force_deferred_switch_calls.append(True)

    def observe_reset_ability_ignorance(_):
        if resolve_active[0]:
            reset_ability_ignorance_calls.append((
                read_native("wBattleMonNativeSpecies"),
                read_native("wEnemyMonNativeSpecies"),
                mem[addr("hBattleTurn")],
                mem[addr("wDeferredSwitch")],
                mem[addr("wMoveState")],
                mem[addr("wBattleEnded")],
            ))
            # Distinguish player/enemy move storage before the opponent turn.
            # The real enemy-side PerformMove must operate with hBattleTurn=1
            # and carry wCurEnemyMove (Tackle=33) to the DoTurn boundary.
            mem[addr("wCurPlayerMove")] = 45

            # Leave the enemy DoTurn, first ReadMoveScriptByte, and first
            # command dispatch entirely real. The post-read stop is installed
            # dynamically only when enemy checkobedience is actually entered.
            resolve_active[0] = False

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
        enemy_checkhit_active[0] = False
        priority_active[0] = False
        enemy_priority_active[0] = False
        critical_active[0] = False
        damagestats_active[0] = False
        damagecalc_active[0] = False
        stab_active[0] = False
        damagevariation_active[0] = False
        moveanim_active[0] = False
        failuretext_active[0] = False
        applydamage_active[0] = False
        criticaltext_active[0] = False
        supereffectivetext_active[0] = False
        postfainteffects_active[0] = False
        posthiteffects_active[0] = False
        cleanup_active[0] = False
        resolve_active[0] = False
        usedmovetext_active[0] = False
        for i, value in enumerate(perform_move_original):
            mem[perform_move_bank, perform_move_addr + i] = value
        for i, value in enumerate(read_dispatch_original):
            mem[read_dispatch_bank, read_dispatch_addr + 3 + i] = value

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
            update_move_data_calls, enemy_update_move_data_snapshots,
            parse_enemy_calls, determine_order_calls, determine_order_snapshots,
            priority_compare_calls, perform_move_calls,
            perform_move_snapshots, do_turn_calls, do_turn_snapshots,
            check_turn_calls, enemy_check_turn_snapshots,
            initialize_move_calls, enemy_initialize_move_snapshots,
            read_script_calls, read_script_snapshots, enemy_read_snapshots,
            checkobedience_calls, checkobedience_snapshots,
            enemy_checkobedience_snapshots,
            usedmovetext_calls, usedmovetext_snapshots,
            usedmovetext_result_snapshots, enemy_usedmovetext_snapshots,
            enemy_usedmovetext_result_snapshots,
            enemy_usedmovetext_text_snapshots,
            display_used_move_calls, display_used_move_snapshots,
            enemy_display_used_move_snapshots, used_move_tilemap_calls,
            doturn_calls, doturn_snapshots, enemy_doturn_snapshots,
            enemy_doturn_result_snapshots,
            consume_pp_calls, consume_pp_snapshots,
            enemy_consume_pp_snapshots,
            hastarget_calls, hastarget_snapshots,
            enemy_hastarget_snapshots, enemy_hastarget_result_snapshots,
            target_fainted_checks, target_fainted_snapshots,
            enemy_target_fainted_snapshots,
            target_ability_checks, target_ability_snapshots,
            enemy_target_ability_snapshots,
            checkhit_calls, checkhit_snapshots, checkhit_result_snapshots,
            enemy_checkhit_snapshots, enemy_checkhit_result_snapshots,
            affection_checks, enemy_affection_checks,
            stat_change_mod_calls, stat_change_mod_snapshots,
            enemy_stat_change_mod_snapshots,
            accuracy_ability_calls, accuracy_ability_snapshots,
            enemy_accuracy_ability_snapshots,
            accuracy_user_ability_checks, accuracy_user_ability_snapshots,
            enemy_accuracy_user_ability_snapshots,
            accuracy_opp_ability_checks, accuracy_opp_ability_snapshots,
            enemy_accuracy_opp_ability_snapshots,
            accuracy_random_calls, enemy_accuracy_random_calls,
            checkpriority_calls, checkpriority_snapshots,
            priority_fainted_checks, priority_fainted_snapshots,
            move_priority_calls, move_priority_snapshots,
            priority_user_ability_checks, priority_user_ability_snapshots,
            priority_opp_ability_checks, priority_opp_ability_snapshots,
            enemy_checkpriority_snapshots, enemy_priority_fainted_snapshots,
            enemy_move_priority_snapshots,
            enemy_priority_user_ability_snapshots,
            enemy_priority_opp_ability_snapshots,
            enemy_priority_result_snapshots,
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
            stab_result_snapshots,
            damagevariation_calls, damagevariation_snapshots,
            damagevariation_random_calls, damagevariation_result_snapshots,
            moveanim_calls, moveanim_snapshots,
            moveanim_lowersub_calls, moveanim_nosub_calls,
            moveanim_raisesub_calls, moveanim_fx_calls,
            moveanim_fx_snapshots, moveanim_result_snapshots,
            failuretext_calls, failuretext_snapshots,
            failure_result_text_calls, failuretext_result_snapshots,
            applydamage_calls, applydamage_snapshots,
            applydamage_affection_calls, applydamage_item_calls,
            applydamage_ability_calls, applydamage_reset_subhit_calls,
            applydamage_check_sub_calls, applydamage_take_damage_calls,
            applydamage_deal_damage_calls, applydamage_subtract_hp_calls,
            applydamage_hud_calls, applydamage_refresh_huds_calls,
            applydamage_result_snapshots,
            criticaltext_calls, criticaltext_snapshots,
            criticaltext_checkcrit_calls, criticaltext_checkcrit_snapshots,
            criticaltext_delay_calls, criticaltext_delay_snapshots,
            criticaltext_result_snapshots,
            supereffectivetext_calls, supereffectivetext_snapshots,
            supereffectivetext_text_calls, supereffectivetext_item_calls,
            supereffectivetext_result_snapshots,
            postfainteffects_calls, postfainteffects_snapshots,
            postfaint_fainted_calls, postfainteffects_result_snapshots,
            posthiteffects_calls, posthiteffects_snapshots,
            posthiteffects_result_snapshots,
            endmove_effect_calls, endmove_throat_spray_calls,
            endmove_power_herb_calls,
            cleanup_tick_calls, cleanup_tilemap_calls, resolve_faints_calls,
            resolve_player_writeback_calls, resolve_enemy_writeback_calls,
            resolve_enemy_fainted_calls, resolve_fit_party_calls,
            resolve_faint_animation_calls, resolve_give_experience_calls,
            resolve_victory_music_calls, deferred_switch_calls,
            force_deferred_switch_calls, reset_ability_ignorance_calls,
            second_perform_move_calls, enemy_move_read_calls,
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

        # ParseEnemyAction's call site remains real. At this boundary seed a
        # deterministic wild-opponent Tackle in enemy-side move storage.
        install_stub("ParseEnemyAction", [0xC9], observe_enemy_action)

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
        # damagestats, damagecalc, STAB, damagevariation, moveanim,
        # failuretext, applydamage, criticaltext, supereffectivetext,
        # postfainteffects and posthiteffects real. Leave the following
        # endmove command ($ff) untouched; this checkpoint verifies its normal
        # terminal branch before PerformMove post-move/faint resolution.
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
        assert mem[normal_bank, normal_addr + 11] == 109, (
            "NormalHit twelfth command is no longer moveanim",
            mem[normal_bank, normal_addr + 11],
        )
        assert mem[normal_bank, normal_addr + 12] == 14, (
            "NormalHit thirteenth command is no longer failuretext",
            mem[normal_bank, normal_addr + 12],
        )
        assert mem[normal_bank, normal_addr + 13] == 15, (
            "NormalHit fourteenth command is no longer applydamage",
            mem[normal_bank, normal_addr + 13],
        )
        assert mem[normal_bank, normal_addr + 14] == 16, (
            "NormalHit fifteenth command is no longer criticaltext",
            mem[normal_bank, normal_addr + 14],
        )
        assert mem[normal_bank, normal_addr + 15] == 17, (
            "NormalHit sixteenth command is no longer supereffectivetext",
            mem[normal_bank, normal_addr + 15],
        )
        assert mem[normal_bank, normal_addr + 16] == 18, (
            "NormalHit seventeenth command is no longer postfainteffects",
            mem[normal_bank, normal_addr + 16],
        )
        assert mem[normal_bank, normal_addr + 17] == 19, (
            "NormalHit eighteenth command is no longer posthiteffects",
            mem[normal_bank, normal_addr + 17],
        )
        assert mem[normal_bank, normal_addr + 18] == 0xFF, (
            "NormalHit nineteenth command is no longer endmove",
            mem[normal_bank, normal_addr + 18],
        )

        install_stub(
            "CheckEndMoveEffects", [0xC9], observe_endmove_effects
        )
        install_stub(
            "CheckThroatSpray", [0xC9], observe_endmove_throat_spray
        )
        install_stub(
            "CheckPowerHerb", [0xC9], observe_endmove_power_herb
        )
        # Presentation-only tail of DisplayUsedMoveText. Its move-history,
        # grammar, last-move and text-selection state logic remains real.
        install_stub(
            "ApplyTilemapInVBlank", [0xC9], observe_used_move_tilemap
        )
        # The post-move cleanup call site is real; the tilemap copy itself is
        # presentation-only. Record only the cleanup-time invocation.
        install_stub(
            "LoadTileMapToTempTileMap", [0xC9], observe_cleanup_tilemap
        )
        # ResolveFaints, DeferredSwitch and ResetAbilityIgnorance remain real.
        # DeferredSwitch must take its natural no-op return because
        # wDeferredSwitch is zero. The stop occurs only on the second
        # PerformMove entry, before the opponent executes its move.

        # Affection is outside native battle identity and can inject a random
        # evasion event before ordinary accuracy math. Force "below threshold"
        # while leaving the rest of BattleCommand_checkhit real.
        install_stub(
            "CheckOpponentAffection", [0xAF, 0xC9],
            observe_opponent_affection,
        )
        install_stub(
            "CheckAffection", [0xAF, 0xC9], observe_critical_affection
        )

        # Deterministic randomness boundary for this deeper checkpoint.
        # Input 100 (checkhit) returns 0, preserving the guaranteed hit.
        # Input 24 (critical) returns 23, guaranteeing non-critical at 1/24.
        # Input 16 (damagevariation) returns 0, selecting the 85% floor.
        # cp 24; jr nz,+3; ld a,23; ret; xor a; ret
        install_stub(
            "BattleRandomRange",
            [0xFE, 24, 0x20, 0x03, 0x3E, 23, 0xC9, 0xAF, 0xC9],
            observe_accuracy_random,
        )

        # HP arithmetic and the applydamage survival checks remain real.
        # Stop only at post-subtraction HUD and held-item recovery boundaries;
        # those are downstream presentation/recovery behavior, not this HP
        # application checkpoint.
        install_stub("UpdateHPBarBattleHuds", [0xC9], observe_applydamage_hud)
        install_stub(
            "RefreshBattleHuds", [0xC9], observe_applydamage_refresh_huds
        )
        install_stub("HandleUserHealingItems", [0xC9])
        install_stub("CheckEnigmaBerry", [0xC9])

        # Keep real moveanim battle-state control flow but stop at the visual
        # renderer/timing boundary. The callback still verifies the requested
        # animation ID and native identities before the immediate return.
        install_stub("PlayFXAnimID", [0xC9], observe_moveanim_fx)

        hook("BattleIntro", lambda _: intro_calls.append(True))
        hook("DoBattle", lambda _: do_battle_calls.append(True))
        hook("BattleTurn", observe_battle_turn)
        hook("ParsePlayerAction", observe_parse_action)
        hook("UpdateMoveData", observe_update_move_data)
        hook("DetermineMoveOrder", observe_determine_order)
        hook("BattleTurn.do_move", observe_perform_move_boundary)
        hook("PerformMove.skip_destinybond_reset", observe_enemy_move_read)
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
        hook("BattleCommand_damagevariation", observe_damagevariation)
        hook("BattleCommand_moveanim", observe_moveanim)
        hook("BattleCommand_lowersub", observe_moveanim_lowersub)
        hook("BattleCommand_moveanimnosub", observe_moveanim_nosub)
        hook("BattleCommand_raisesub", observe_moveanim_raisesub)
        hook("BattleCommand_failuretext", observe_failuretext)
        hook("GetFailureResultText", observe_failure_result_text)
        hook("BattleCommand_applydamage", observe_applydamage)
        hook("ResetSubHit", observe_applydamage_reset_subhit)
        hook("CheckSubstituteOpp", observe_applydamage_check_sub)
        hook("GetOpponentItem", observe_applydamage_item)
        hook("TakeDamage", observe_applydamage_take_damage)
        hook("DealDamageToOpponent", observe_applydamage_deal_damage)
        hook("SubtractHPFromUser", observe_applydamage_subtract_hp)
        hook("BattleCommand_criticaltext", observe_criticaltext)
        hook("CheckCrit", observe_criticaltext_checkcrit)
        hook("DelayFrames", observe_criticaltext_delay)
        hook("BattleCommand_supereffectivetext", observe_supereffectivetext)
        hook("StdBattleTextbox", observe_supereffective_textbox)
        hook("GetOpponentItemAfterUnnerve", observe_supereffective_item)
        hook("BattleCommand_postfainteffects", observe_postfainteffects)
        hook("BattleCommand_posthiteffects", observe_posthiteffects)
        hook("TickDisableAndEncoreAfterMove", observe_cleanup_tick)
        hook("ResolveFaints", observe_resolve_faints)
        hook("UpdateBattleMonInParty", observe_resolve_player_writeback)
        hook("UpdateEnemyMonInParty", observe_resolve_enemy_writeback)
        hook("HasEnemyFainted", observe_resolve_enemy_fainted)
        hook("CheckPlayerPartyForFitPkmn", observe_resolve_fit_party)
        hook("FaintUserPokemon", observe_resolve_faint_animation)
        hook("GiveExperience", observe_resolve_give_experience)
        hook("PlayVictoryMusic", observe_resolve_victory_music)
        hook("DeferredSwitch", observe_deferred_switch)
        hook("ForceDeferredSwitch", observe_force_deferred_switch)
        hook("ResetAbilityIgnorance", observe_reset_ability_ignorance)
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

            invoke("DoBattle", max_frames=256)

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
            assert perform_move_calls == [True, True], (
                "two PerformMove boundaries were not reached",
                context, perform_move_calls
            )
            assert perform_move_snapshots == [
                (25, native, 0, 33),
                (25, native, 1, 45),
            ], (
                "native identity/turn state at PerformMove boundaries",
                context, perform_move_snapshots
            )
            assert enemy_move_read_calls == [
                (25, native, 1, 33, 45, 33, 0, 0, 0),
            ], (
                "real enemy PerformMove did not read enemy-side Tackle with "
                "hBattleTurn=1 after clearing damage bookkeeping",
                context, enemy_move_read_calls
            )
            assert check_turn_calls == [True, True], (
                "real player/enemy CheckTurn count", context, check_turn_calls
            )
            assert enemy_check_turn_snapshots == [
                (25, native, 1, 45, 33, 0, 0, 1),
            ], (
                "enemy DoTurn did not reach real CheckTurn with native "
                "identities and enemy Tackle intact",
                context, enemy_check_turn_snapshots
            )
            assert enemy_update_move_data_snapshots == [
                (25, native, 1, 45, 33, 0, 0),
            ], (
                "enemy DoTurn did not perform its real UpdateMoveData refresh",
                context, enemy_update_move_data_snapshots
            )
            assert initialize_move_calls == [True, True], (
                "real player/enemy InitializeMove count",
                context, initialize_move_calls
            )
            assert enemy_initialize_move_snapshots == [
                (25, native, 1, 45, 33, 0, 0),
            ], (
                "enemy DoTurn did not reach real InitializeMove with enemy "
                "Tackle/native identities intact",
                context, enemy_initialize_move_snapshots
            )
            assert len(update_move_data_calls) >= 3, (
                "enemy DoTurn did not add its real UpdateMoveData refresh",
                context, update_move_data_calls
            )
            assert read_script_calls == [True] * 26, (
                "expected the 19 validated player reads plus seven real enemy "
                "script-byte reads",
                context, read_script_calls
            )
            assert enemy_read_snapshots == [
                (
                    25, native, 1, 45, 33, 0, 0, 1,
                    read_script_snapshots[19][5],
                    read_script_snapshots[19][6],
                ),
                (
                    25, native, 1, 45, 33, 0, 0, 1,
                    read_script_snapshots[20][5],
                    read_script_snapshots[20][6],
                ),
                (
                    25, native, 1, 45, 33, 0, 0, 1,
                    read_script_snapshots[21][5],
                    read_script_snapshots[21][6],
                ),
                (
                    25, native, 1, 45, 33, 0, 0, 1,
                    read_script_snapshots[22][5],
                    read_script_snapshots[22][6],
                ),
                (
                    25, native, 1, 45, 33, 0, 0, 1,
                    read_script_snapshots[23][5],
                    read_script_snapshots[23][6],
                ),
                (
                    25, native, 1, 45, 33, 0, 0, 0,
                    read_script_snapshots[24][5],
                    read_script_snapshots[24][6],
                ),
                (
                    25, native, 1, 45, 33, 0, 0, 0,
                    read_script_snapshots[25][5],
                    read_script_snapshots[25][6],
                ),
            ], (
                "enemy script reads lost native identity, turn, move state, "
                "or script pointer",
                context, enemy_read_snapshots
            )
            assert read_script_snapshots[19][5:] != (0, 0), (
                "enemy InitializeMove did not publish a move-script pointer",
                context, read_script_snapshots[19]
            )
            assert read_script_snapshots[20][5:] == advance_script_pointer(
                read_script_snapshots[19], 1
            ), (
                "enemy checkobedience did not return to the second script read "
                "at exactly the next command byte",
                context, read_script_snapshots[19:21]
            )
            assert read_script_snapshots[21][5:] == advance_script_pointer(
                read_script_snapshots[19], 2
            ), (
                "enemy usedmovetext did not return to the third script read "
                "at exactly the doturn command byte",
                context, read_script_snapshots[19:22]
            )
            assert read_script_snapshots[22][5:] == advance_script_pointer(
                read_script_snapshots[19], 3
            ), (
                "enemy doturn did not return to the fourth script read at "
                "exactly the hastarget command byte",
                context, read_script_snapshots[19:23]
            )
            assert read_script_snapshots[23][5:] == advance_script_pointer(
                read_script_snapshots[19], 4
            ), (
                "enemy hastarget did not return to the fifth script read at "
                "exactly the checkhit command byte",
                context, read_script_snapshots[19:24]
            )
            assert read_script_snapshots[24][5:] == advance_script_pointer(
                read_script_snapshots[19], 5
            ), (
                "enemy checkhit did not return to the sixth script read at "
                "exactly the checkpriority command byte",
                context, read_script_snapshots[19:25]
            )
            assert read_script_snapshots[25][5:] == advance_script_pointer(
                read_script_snapshots[19], 6
            ), (
                "enemy checkpriority did not return to the seventh script read "
                "at exactly the critical command byte",
                context, read_script_snapshots[19:26]
            )
            assert read_script_snapshots[0][:5] == (25, native, 0, 33, 0), (
                "native/move state at first real script read",
                context, read_script_snapshots
            )
            assert read_script_snapshots[0][5:] != (0, 0), (
                "InitializeMove did not publish a move-script pointer",
                context, read_script_snapshots
            )
            assert checkobedience_calls == [True, True], (
                "player/enemy real checkobedience dispatch count", context,
                checkobedience_calls
            )
            assert checkobedience_snapshots == [
                (25, native, 0, 33, *advance_script_pointer(read_script_snapshots[0], 1)),
                (25, native, 1, 45, *advance_script_pointer(read_script_snapshots[19], 1)),
            ], (
                "native identity/script pointer at player/enemy "
                "checkobedience dispatch",
                context, checkobedience_snapshots, read_script_snapshots
            )
            assert enemy_checkobedience_snapshots == [
                (
                    25, native, 1, 45, 33, 0, 1,
                    *advance_script_pointer(read_script_snapshots[19], 1),
                    0,
                ),
            ], (
                "enemy checkobedience entry did not preserve native identity, "
                "enemy Tackle, move state, script pointer, or unended battle",
                context, enemy_checkobedience_snapshots
            )
            assert read_script_snapshots[1][:5] == (25, native, 0, 33, 0), (
                "native/move state changed after checkobedience",
                context, read_script_snapshots
            )
            assert usedmovetext_calls == [True, True], (
                "player/enemy real usedmovetext dispatch count", context,
                usedmovetext_calls
            )
            assert usedmovetext_snapshots == [
                (25, native, 0, 33, *advance_script_pointer(read_script_snapshots[0], 2)),
                (25, native, 1, 45, *advance_script_pointer(read_script_snapshots[19], 2)),
            ], (
                "native identity/script pointer at player/enemy "
                "usedmovetext dispatch",
                context, usedmovetext_snapshots, read_script_snapshots
            )
            assert len(enemy_usedmovetext_snapshots) == 1, (
                "enemy usedmovetext entry count", context,
                enemy_usedmovetext_snapshots
            )
            assert enemy_usedmovetext_snapshots[0][:9] == (
                25, native, 1, 45, 33, 0, 1,
                *advance_script_pointer(read_script_snapshots[19], 2),
            ), (
                "enemy usedmovetext entry lost native identity, Tackle, "
                "move state, or script pointer",
                context, enemy_usedmovetext_snapshots
            )
            assert display_used_move_calls == [True, True], (
                "player/enemy DisplayUsedMoveText count", context,
                display_used_move_calls
            )
            assert display_used_move_snapshots == [
                (25, native, 0, 33),
                (25, native, 1, 45),
            ], (
                "native identity/turn state changed inside DisplayUsedMoveText",
                context, display_used_move_snapshots
            )
            assert enemy_display_used_move_snapshots == [
                (25, native, 1, 45, 33, 1),
            ], (
                "enemy DisplayUsedMoveText entry lost native/Tackle state",
                context, enemy_display_used_move_snapshots
            )
            assert len(enemy_usedmovetext_text_snapshots) == 1, (
                "enemy usedmovetext text-selection count",
                context, enemy_usedmovetext_text_snapshots
            )
            assert enemy_usedmovetext_text_snapshots[0][:10] == (
                25, native, 1, 45, 33, 33, 33, 33, 0, addr("UsedMoveText"),
            ), (
                "enemy usedmovetext grammar/last-move/text selection changed",
                context, enemy_usedmovetext_text_snapshots
            )
            assert enemy_usedmovetext_text_snapshots[0][10] == (
                enemy_usedmovetext_snapshots[0][9]
            ), (
                "enemy usedmovetext unexpectedly changed player used-move "
                "history before text selection",
                context, enemy_usedmovetext_text_snapshots,
                enemy_usedmovetext_snapshots
            )
            assert enemy_usedmovetext_result_snapshots == [
                (
                    25, native, 1, 45, 33, 0, 33, 33, 33, 0,
                    enemy_usedmovetext_snapshots[0][9],
                ),
            ], (
                "enemy usedmovetext did not preserve native/Tackle state or "
                "publish grammar/last-move history correctly",
                context, enemy_usedmovetext_result_snapshots
            )
            assert used_move_tilemap_calls[-1] == (
                25, native, 1, 33,
                mem[addr("wLastPlayerMove")], 33,
                mem[addr("wLastPlayerCounterMove")], 33,
            ), (
                "enemy usedmovetext did not reach the presentation-only "
                "ApplyTilemapInVBlank boundary with expected state",
                context, used_move_tilemap_calls
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
            assert doturn_calls == [True, True], (
                "player/enemy real doturn dispatch count", context, doturn_calls
            )
            assert doturn_snapshots == [
                (
                    25, native, 0, 33, 35, 35,
                    *advance_script_pointer(read_script_snapshots[0], 3),
                ),
                (
                    25, native, 1, 45, 34, 34,
                    *advance_script_pointer(read_script_snapshots[19], 3),
                ),
            ], (
                "native identity/player PP/script pointer at player/enemy "
                "doturn dispatch",
                context, doturn_snapshots, read_script_snapshots
            )
            assert enemy_doturn_snapshots == [
                (
                    25, native, 1, 45, 33, 0, 34, 34, 35, 35, 0, 0,
                    *advance_script_pointer(read_script_snapshots[19], 3),
                    0,
                ),
            ], (
                "enemy doturn entry lost native identity, enemy Tackle, "
                "ordinary turn state, or seeded PP",
                context, enemy_doturn_snapshots
            )
            assert consume_pp_calls == [True, True, True], (
                "player/enemy doturn plus enemy Pressure BattleConsumePP count",
                context, consume_pp_calls
            )
            assert consume_pp_snapshots == [
                (25, native, 0, 33, 35, 35),
                (25, native, 1, 45, 34, 34),
                (25, native, 1, 45, 34, 34),
            ], (
                "native identity or player PP changed before BattleConsumePP",
                context, consume_pp_snapshots
            )
            assert enemy_consume_pp_snapshots == [
                (25, native, 1, 45, 33, 0, 34, 34, 35, 35),
                (25, native, 1, 45, 33, 0, 34, 34, 34, 34),
            ], (
                "enemy doturn/Pressure BattleConsumePP entries did not preserve "
                "isolated player/enemy PP state",
                context, enemy_consume_pp_snapshots
            )
            assert enemy_doturn_result_snapshots == [
                (
                    25, native, 1, 45, 33, 0, 34, 34, 34, 34,
                    *advance_script_pointer(read_script_snapshots[19], 3),
                ),
            ], (
                "enemy doturn did not consume exactly one PP from active and "
                "OT-party enemy state while preserving player PP/native IDs",
                context, enemy_doturn_result_snapshots
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
            assert enemy_hastarget_snapshots == [
                (
                    25, native, 1, 45, 33, 0, 0, 100, 0, 83,
                    34, 34, 34, 34, PRESSURE,
                    *advance_script_pointer(read_script_snapshots[19], 4),
                    0,
                ),
            ], (
                "enemy hastarget entry lost native IDs, living player target, "
                "enemy PP, Pressure seed, or script pointer",
                context, enemy_hastarget_snapshots
            )
            assert enemy_target_fainted_snapshots == [
                (25, native, 1, 0, 100, 0, 83),
            ], (
                "enemy hastarget living-target check did not inspect preserved "
                "player/enemy HP under hBattleTurn=1",
                context, enemy_target_fainted_snapshots
            )
            assert enemy_target_ability_snapshots == [
                (25, native, 1, 45, 33, PRESSURE),
            ], (
                "enemy hastarget did not reach the opponent ability lookup "
                "with player Pressure and preserved native/move state",
                context, enemy_target_ability_snapshots
            )
            assert enemy_hastarget_result_snapshots == [
                (
                    25, native, 1, 45, 33, 0, 34, 34, 33, 33, PRESSURE,
                    *advance_script_pointer(read_script_snapshots[19], 4),
                ),
            ], (
                "enemy hastarget Pressure path did not consume exactly one "
                "additional enemy PP before the checkhit read",
                context, enemy_hastarget_result_snapshots
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
            assert enemy_checkhit_snapshots == [
                (
                    25, native, 1, 45, 33, 0,
                    34, 34, 33, 33, PRESSURE,
                    *advance_script_pointer(read_script_snapshots[19], 5),
                    0,
                ),
            ], (
                "enemy checkhit entry lost native IDs, Tackle/PP state, "
                "Pressure, script pointer, or unended battle",
                context, enemy_checkhit_snapshots
            )
            assert enemy_affection_checks == [True], (
                "enemy checkhit did not traverse the affection boundary once",
                context, enemy_affection_checks
            )
            assert enemy_stat_change_mod_snapshots == [
                (25, native, 1, 45, 33, 7, 7, 7, 7),
            ], (
                "enemy checkhit did not use neutral enemy accuracy/player "
                "evasion stages in real DoStatChangeMod",
                context, enemy_stat_change_mod_snapshots
            )
            assert enemy_accuracy_ability_snapshots == [
                (25, native, 1, 45, 33, PRESSURE, 0),
            ], (
                "enemy checkhit did not run real accuracy ability processing "
                "with preserved native IDs/Pressure",
                context, enemy_accuracy_ability_snapshots
            )
            assert enemy_accuracy_user_ability_snapshots, (
                "enemy checkhit skipped user ability checks", context
            )
            assert all(
                snap[0:2] == (25, native)
                and snap[2] == 1
                and snap[3:5] == (45, 33)
                and snap[5:] == (PRESSURE, 0)
                for snap in enemy_accuracy_user_ability_snapshots
            ), (
                "enemy checkhit user ability checks changed native/move/"
                "ability state",
                context, enemy_accuracy_user_ability_snapshots
            )
            assert enemy_accuracy_opp_ability_snapshots, (
                "enemy checkhit skipped opponent ability checks", context
            )
            assert all(
                snap[0:2] == (25, native)
                and snap[2] in (0, 1)
                and snap[3:5] == (45, 33)
                and snap[5:] == (PRESSURE, 0)
                for snap in enemy_accuracy_opp_ability_snapshots
            ), (
                "enemy checkhit opponent ability checks changed native/move/"
                "ability state",
                context, enemy_accuracy_opp_ability_snapshots
            )
            assert enemy_accuracy_random_calls == [100], (
                "enemy 100%-accuracy Tackle did not use the deterministic "
                "0-99 < 100 hit roll",
                context, enemy_accuracy_random_calls
            )
            assert enemy_checkhit_result_snapshots == [
                (
                    25, native, 1, 45, 33, 0,
                    34, 34, 33, 33, PRESSURE, 0, (0, 0, 100),
                    *advance_script_pointer(read_script_snapshots[19], 5),
                ),
            ], (
                "enemy checkhit did not resolve a 100% Tackle hit with "
                "preserved native IDs, PP, Pressure, and script pointer",
                context, enemy_checkhit_result_snapshots
            )
            assert enemy_checkpriority_snapshots == [
                (
                    25, native, 1, 45, 33, 0,
                    0, 100, 0, 83,
                    34, 34, 33, 33, PRESSURE, 0, 33, 0x10,
                    *advance_script_pointer(read_script_snapshots[19], 6),
                    0,
                ),
            ], (
                "enemy checkpriority entry lost native IDs, Tackle/PP, HP, "
                "Pressure, hit state, preserved matchup scratch, or script pointer",
                context, enemy_checkpriority_snapshots
            )
            assert enemy_priority_fainted_snapshots == [
                (25, native, 1, 0, 100, 0, 83),
            ], (
                "enemy checkpriority did not run the living player-target "
                "check with preserved native IDs/HP",
                context, enemy_priority_fainted_snapshots
            )
            assert enemy_move_priority_snapshots == [
                (25, native, 1, 45, 33, PRESSURE, 0),
            ], (
                "enemy checkpriority did not call real GetMovePriority with "
                "preserved enemy Tackle/native/ability state",
                context, enemy_move_priority_snapshots
            )
            assert len(enemy_priority_user_ability_snapshots) == 2, (
                "enemy normal-priority path did not run GetMovePriority and "
                "Prankster user-ability checks",
                context, enemy_priority_user_ability_snapshots
            )
            assert all(
                snap[0:2] == (25, native)
                and snap[2] == 1
                and snap[3:5] == (45, 33)
                and snap[5:] == (PRESSURE, 0)
                for snap in enemy_priority_user_ability_snapshots
            ), (
                "enemy priority user-ability checks changed native/move/"
                "ability state",
                context, enemy_priority_user_ability_snapshots
            )
            assert len(enemy_priority_opp_ability_snapshots) == 1, (
                "enemy normal-priority path did not run exactly one "
                "Soundproof opponent-ability check",
                context, enemy_priority_opp_ability_snapshots
            )
            assert all(
                snap[0:2] == (25, native)
                and snap[2] == 1
                and snap[3:5] == (45, 33)
                and snap[5:] == (PRESSURE, 0)
                for snap in enemy_priority_opp_ability_snapshots
            ), (
                "enemy priority opponent-ability check changed native/move/"
                "ability state",
                context, enemy_priority_opp_ability_snapshots
            )
            assert enemy_priority_result_snapshots == [
                (
                    25, native, 1, 45, 33, 0,
                    34, 34, 33, 33, PRESSURE, 0, 33, 0x10,
                    *advance_script_pointer(read_script_snapshots[19], 6),
                ),
            ], (
                "enemy checkpriority did not return normally with preserved "
                "native IDs, Tackle/PP, Pressure, hit/matchup scratch state, and "
                "pre-critical-read script pointer",
                context, enemy_priority_result_snapshots
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
            assert damagevariation_calls == [True], (
                "eleventh real battle-command dispatch count", context,
                damagevariation_calls
            )
            assert damagevariation_snapshots == [
                (
                    25, native, 0, 33, 0, 21,
                    *advance_script_pointer(read_script_snapshots[0], 11),
                ),
            ], (
                "native identity/STAB damage changed entering damagevariation",
                context, damagevariation_snapshots
            )
            assert damagevariation_random_calls == [16], (
                "damagevariation did not request its real 0-15 random roll",
                context, damagevariation_random_calls
            )
            assert damagevariation_result_snapshots == [
                (25, native, 0, 33, 0, 17),
            ], (
                "real 85% damage variation did not produce 17 damage or "
                "changed native identity",
                context, damagevariation_result_snapshots
            )
            assert read_script_snapshots[11][:5] == (25, native, 0, 33, 0), (
                "native/move/hit state changed after damagevariation",
                context, read_script_snapshots
            )
            assert read_script_snapshots[11][5:] == advance_script_pointer(
                read_script_snapshots[0], 11
            ), (
                "script pointer did not advance through eleven real commands",
                context, read_script_snapshots
            )
            assert moveanim_calls == [True], (
                "twelfth real battle-command dispatch count", context,
                moveanim_calls
            )
            assert moveanim_snapshots == [
                (
                    25, native, 0, 33, 0, 17,
                    *advance_script_pointer(read_script_snapshots[0], 12),
                ),
            ], (
                "native identity/varied damage changed entering moveanim",
                context, moveanim_snapshots
            )
            assert moveanim_lowersub_calls == [True], (
                "moveanim skipped lowersub control flow", context,
                moveanim_lowersub_calls
            )
            assert moveanim_nosub_calls == [True], (
                "moveanim skipped moveanimnosub control flow", context,
                moveanim_nosub_calls
            )
            assert moveanim_raisesub_calls == [True], (
                "moveanim skipped raisesub control flow", context,
                moveanim_raisesub_calls
            )
            assert moveanim_fx_calls == [True], (
                "moveanim did not reach the visual animation boundary", context,
                moveanim_fx_calls
            )
            assert moveanim_fx_snapshots == [(25, native, 0, 33, 33)], (
                "moveanim requested the wrong animation or changed native "
                "identity at PlayFXAnimID",
                context, moveanim_fx_snapshots
            )
            assert moveanim_result_snapshots == [
                (25, native, 0, 33, 0, 17, 0),
            ], (
                "moveanim changed damage/native identity or left an unexpected "
                "animation parameter",
                context, moveanim_result_snapshots
            )
            assert bytes(
                mem[addr("wCurDamage"):addr("wCurDamage") + 2]
            ) == bytes([0, 17]), (
                "moveanim changed varied damage", context,
                bytes(mem[addr("wCurDamage"):addr("wCurDamage") + 2])
            )
            assert read_script_snapshots[12][:5] == (25, native, 0, 33, 0), (
                "native/move/hit state changed after moveanim",
                context, read_script_snapshots
            )
            assert read_script_snapshots[12][5:] == advance_script_pointer(
                read_script_snapshots[0], 12
            ), (
                "script pointer did not advance through twelve real commands",
                context, read_script_snapshots
            )
            assert failuretext_calls == [True], (
                "thirteenth real battle-command dispatch count", context,
                failuretext_calls
            )
            assert failuretext_snapshots == [
                (
                    25, native, 0, 33, 0, 0, 17,
                    *advance_script_pointer(read_script_snapshots[0], 13),
                ),
            ], (
                "native identity/success state/damage changed entering failuretext",
                context, failuretext_snapshots
            )
            assert not failure_result_text_calls, (
                "successful Tackle entered failure-result text handling",
                context, failure_result_text_calls
            )
            assert failuretext_result_snapshots == [
                (25, native, 0, 33, 0, 0, 17),
            ], (
                "failuretext no-failure return changed native identity, miss "
                "state, or damage",
                context, failuretext_result_snapshots
            )
            assert read_script_snapshots[13][:5] == (25, native, 0, 33, 0), (
                "native/move/hit state changed after failuretext",
                context, read_script_snapshots
            )
            assert read_script_snapshots[13][5:] == advance_script_pointer(
                read_script_snapshots[0], 13
            ), (
                "script pointer did not advance through thirteen real commands",
                context, read_script_snapshots
            )
            assert applydamage_calls == [True], (
                "fourteenth real battle-command dispatch count", context,
                applydamage_calls
            )
            assert applydamage_snapshots == [
                (
                    25, native, 0, 33, 0, 0, 17, 0, 100, 0, 0,
                    *advance_script_pointer(read_script_snapshots[0], 14),
                ),
            ], (
                "native identity/damage/HP state changed entering applydamage",
                context, applydamage_snapshots
            )
            assert applydamage_reset_subhit_calls == [True], (
                "applydamage skipped ResetSubHit", context,
                applydamage_reset_subhit_calls
            )
            assert applydamage_check_sub_calls, (
                "applydamage skipped substitute check", context
            )
            assert applydamage_affection_calls == [True], (
                "applydamage skipped affection endure check", context,
                applydamage_affection_calls
            )
            assert applydamage_item_calls == [True], (
                "applydamage skipped opponent held-item check", context,
                applydamage_item_calls
            )
            assert applydamage_ability_calls, (
                "applydamage skipped opponent ability checks", context,
                applydamage_ability_calls
            )
            assert applydamage_take_damage_calls == [True], (
                "applydamage skipped TakeDamage", context,
                applydamage_take_damage_calls
            )
            assert applydamage_deal_damage_calls == [True], (
                "applydamage skipped DealDamageToOpponent", context,
                applydamage_deal_damage_calls
            )
            assert applydamage_subtract_hp_calls == [True], (
                "applydamage skipped SubtractHPFromUser", context,
                applydamage_subtract_hp_calls
            )
            assert applydamage_hud_calls == [True], (
                "real HP subtraction did not reach HP-bar update boundary",
                context, applydamage_hud_calls
            )
            assert applydamage_refresh_huds_calls == [True], (
                "TakeDamage did not reach final HUD refresh boundary",
                context, applydamage_refresh_huds_calls
            )
            assert applydamage_result_snapshots == [
                (25, native, 0, 33, 0, 0, 17, 0, 83, 0, 17),
            ], (
                "real applydamage did not subtract 17 HP or preserve native "
                "identity/damage state",
                context, applydamage_result_snapshots
            )
            assert read_script_snapshots[14][:5] == (25, native, 0, 33, 0), (
                "native/move/hit state changed after applydamage",
                context, read_script_snapshots
            )
            assert read_script_snapshots[14][5:] == advance_script_pointer(
                read_script_snapshots[0], 14
            ), (
                "script pointer did not advance through fourteen real commands",
                context, read_script_snapshots
            )
            assert criticaltext_calls == [True], (
                "fifteenth real battle-command dispatch count",
                context, criticaltext_calls
            )
            assert criticaltext_snapshots == [
                (
                    25, native, 0, 33, 0, 0, 83, 0, 17,
                    *advance_script_pointer(read_script_snapshots[0], 15),
                ),
            ], (
                "native identity/non-critical state/HP changed entering "
                "criticaltext",
                context, criticaltext_snapshots
            )
            assert criticaltext_checkcrit_calls == [True], (
                "criticaltext skipped CheckCrit",
                context, criticaltext_checkcrit_calls
            )
            assert criticaltext_checkcrit_snapshots == [(25, native, 0, 0)], (
                "CheckCrit saw changed identity or hit state",
                context, criticaltext_checkcrit_snapshots
            )
            assert criticaltext_delay_calls == [True], (
                "non-critical criticaltext skipped its wait",
                context, criticaltext_delay_calls
            )
            assert criticaltext_delay_snapshots == [(25, native, 0, 20)], (
                "criticaltext did not request DelayFrames(20)",
                context, criticaltext_delay_snapshots
            )
            assert criticaltext_result_snapshots == [
                (25, native, 0, 33, 0, 0, 83, 0, 17),
            ], (
                "criticaltext changed identity/hit state/HP/damage bookkeeping",
                context, criticaltext_result_snapshots
            )
            assert read_script_snapshots[15][:5] == (25, native, 0, 33, 0), (
                "native/move/hit state changed after criticaltext",
                context, read_script_snapshots
            )
            assert read_script_snapshots[15][5:] == advance_script_pointer(
                read_script_snapshots[0], 15
            ), (
                "script pointer did not advance through fifteen real commands",
                context, read_script_snapshots
            )
            assert supereffectivetext_calls == [True], (
                "sixteenth real battle-command dispatch count",
                context, supereffectivetext_calls
            )
            assert supereffectivetext_snapshots == [
                (
                    25, native, 0, 33, 0x10, 0, 83, 0, 17,
                    *advance_script_pointer(read_script_snapshots[0], 16),
                ),
            ], (
                "native identity/neutral modifier/HP changed entering "
                "supereffectivetext",
                context, supereffectivetext_snapshots
            )
            assert not supereffectivetext_text_calls, (
                "neutral effectiveness path printed effectiveness text",
                context, supereffectivetext_text_calls
            )
            assert not supereffectivetext_item_calls, (
                "neutral effectiveness path entered Weakness Policy handling",
                context, supereffectivetext_item_calls
            )
            assert supereffectivetext_result_snapshots == [
                (25, native, 0, 33, 0x10, 0, 83, 0, 17),
            ], (
                "supereffectivetext changed identity/modifier/HP/damage",
                context, supereffectivetext_result_snapshots
            )
            assert read_script_snapshots[16][:5] == (25, native, 0, 33, 0), (
                "native/move/hit state changed after supereffectivetext",
                context, read_script_snapshots
            )
            assert read_script_snapshots[16][5:] == advance_script_pointer(
                read_script_snapshots[0], 16
            ), (
                "script pointer did not advance through sixteen real commands",
                context, read_script_snapshots
            )
            assert postfainteffects_calls == [True], (
                "seventeenth real battle-command dispatch count",
                context, postfainteffects_calls
            )
            assert postfainteffects_snapshots == [(25, native, 0, 83, 0, 17)], (
                "postfainteffects entry state changed",
                context, postfainteffects_snapshots
            )
            assert postfaint_fainted_calls == [(25, native, 0, 0, 83)], (
                "postfainteffects skipped or failed non-faint check",
                context, postfaint_fainted_calls
            )
            assert postfainteffects_result_snapshots == [
                (25, native, 0, 83, 0, 17),
            ], (
                "postfainteffects changed native identity/HP/damage",
                context, postfainteffects_result_snapshots
            )
            assert read_script_snapshots[17][:5] == (25, native, 0, 33, 0), (
                "native/move/hit state changed after postfainteffects",
                context, read_script_snapshots
            )
            assert read_script_snapshots[17][5:] == advance_script_pointer(
                read_script_snapshots[0], 17
            ), (
                "script pointer did not advance through seventeen real commands",
                context, read_script_snapshots
            )
            assert posthiteffects_calls == [True], (
                "eighteenth real battle-command dispatch count",
                context, posthiteffects_calls
            )
            assert posthiteffects_snapshots == [
                (25, native, 0, 0, 83, 0, 17, 0),
            ], (
                "posthiteffects entry state changed",
                context, posthiteffects_snapshots
            )
            assert posthiteffects_result_snapshots == [
                (25, native, 0, 0, 83, 0, 17, 0),
            ], (
                "posthiteffects changed native identity/HP/damage/hit state",
                context, posthiteffects_result_snapshots
            )
            assert len(read_script_calls) == 26, (
                "expected the validated 19 player reads plus seven enemy reads",
                context, len(read_script_calls)
            )
            assert read_script_snapshots[18][:5] == (25, native, 0, 33, 0), (
                "native/move/hit state changed before endmove",
                context, read_script_snapshots
            )
            assert read_script_snapshots[18][5:] == advance_script_pointer(
                read_script_snapshots[0], 18
            ), (
                "script pointer did not reach the nineteenth endmove byte",
                context, read_script_snapshots
            )
            assert mem[normal_bank, normal_addr + 18] == 0xFF, (
                "endmove byte was modified by the regression harness",
                context, mem[normal_bank, normal_addr + 18]
            )
            assert endmove_effect_calls == [
                (25, native, 0, 0, 83, 0, 17),
            ], (
                "endmove did not enter CheckEndMoveEffects with preserved state",
                context, endmove_effect_calls
            )
            assert endmove_throat_spray_calls == [(25, native, 0)], (
                "endmove did not continue to CheckThroatSpray",
                context, endmove_throat_spray_calls
            )
            assert endmove_power_herb_calls == [(25, native, 0)], (
                "endmove did not continue to CheckPowerHerb",
                context, endmove_power_herb_calls
            )
            assert cleanup_tick_calls == [
                (25, native, 0, 0, 0, (1 << 2) | (1 << 5), 5, 4, 7, 6),
            ], (
                "PerformMove did not clear both IN_ABILITY bits before the "
                "real disable/encore tick, or cleanup state changed early",
                context, cleanup_tick_calls
            )
            assert cleanup_tilemap_calls == [
                (25, native, 0, 0, 0, 0, 4, 3, 7, 6),
            ], (
                "real TickDisableAndEncoreAfterMove or Protect/Endure cleanup "
                "did not produce the expected state before tilemap refresh",
                context, cleanup_tilemap_calls
            )
            assert resolve_faints_calls == [
                (25, native, 0, 0, 0, 0, 4, 3, 7, 6, 0, 83, 0, 17),
                (25, native, 1, 0, 0, 0, 4, 3, 7, 6, 0, 83, 0, 0),
            ], (
                "PerformMove cleanup did not reach real ResolveFaints with "
                "preserved native identity, HP, damage, and cleanup state",
                context, resolve_faints_calls
            )
            assert resolve_player_writeback_calls == [
                (25, native, 0, 0, 100, 0, 100, 34, 34),
                (25, native, 1, 0, 100, 0, 100, 34, 34),
            ], (
                "real player party write-back boundary changed identity/HP/PP",
                context, resolve_player_writeback_calls
            )
            assert resolve_enemy_writeback_calls == [
                (25, native, 0, 0, 83, 0, 100, species, form),
                (25, native, 1, 0, 83, 0, 83, species, form),
            ], (
                "real enemy party write-back boundary changed identity/layout",
                context, resolve_enemy_writeback_calls
            )
            assert resolve_enemy_fainted_calls == [
                (25, native, 0, 0, 83),
                (25, native, 0, 0, 83),
                (25, native, 0, 0, 83),
                (25, native, 1, 0, 83),
                (25, native, 1, 0, 83),
                (25, native, 1, 0, 83),
            ], (
                "non-fainting ResolveFaints did not perform all three alive-"
                "opponent checks",
                context, resolve_enemy_fainted_calls
            )
            assert resolve_fit_party_calls == [
                (25, native, 0, 1, 0, 100),
                (25, native, 1, 1, 0, 100),
            ], (
                "ResolveFaints did not verify the player still has a fit mon",
                context, resolve_fit_party_calls
            )
            assert resolve_faint_animation_calls == [], (
                "non-fainting ResolveFaints entered faint animation handling",
                context, resolve_faint_animation_calls
            )
            assert resolve_give_experience_calls == [], (
                "non-fainting ResolveFaints incorrectly awarded experience",
                context, resolve_give_experience_calls
            )
            assert resolve_victory_music_calls == [], (
                "non-fainting ResolveFaints incorrectly played victory music",
                context, resolve_victory_music_calls
            )
            assert deferred_switch_calls == [
                (25, native, 0, 0, 0),
            ], (
                "ResolveFaints did not return into real no-op DeferredSwitch "
                "with preserved native/battle state",
                context, deferred_switch_calls
            )
            assert force_deferred_switch_calls == [], (
                "zero wDeferredSwitch unexpectedly entered ForceDeferredSwitch",
                context, force_deferred_switch_calls
            )
            assert reset_ability_ignorance_calls == [
                (25, native, 0, 0, 0x55, 0),
            ], (
                "real no-op DeferredSwitch did not reach "
                "ResetAbilityIgnorance with the seeded move-state sentinel",
                context, reset_ability_ignorance_calls
            )
            assert second_perform_move_calls == [
                (25, native, 1, 0, 45, 33, 0, 0, 17, 0, 0x11, 0),
            ], (
                "BattleTurn did not reach the real opponent PerformMove entry "
                "with the enemy-side Tackle and preserved native state",
                context, second_perform_move_calls
            )
            assert bytes(
                mem[addr("wBattleMonHP"):addr("wBattleMonHP") + 2]
            ) == bytes([0, 100]), ("player HP changed", context)
            assert bytes(
                mem[addr("wEnemyMonHP"):addr("wEnemyMonHP") + 2]
            ) == bytes([0, 83]), ("enemy HP did not fall to 83", context)
            assert bytes(
                mem[addr("wDamageTaken"):addr("wDamageTaken") + 2]
            ) == bytes([0, 0]), (
                "enemy PerformMove did not clear damage bookkeeping before "
                "the DoTurn boundary", context
            )
            assert read_native("wBattleMonNativeSpecies") == 25, context
            assert read_native("wEnemyMonNativeSpecies") == native, context
            assert mem[addr("wTotalBattleTurns")] == 1, context
            assert mem[addr("hBattleTurn")] == 1, context
            assert mem[addr("wBattlePlayerAction")] == 0, context
            assert mem[addr("wPlayerSwitchTarget")] == 0, context
            assert mem[addr("wEnemySwitchTarget")] == 0, context
            assert mem[addr("wBattleEnded")] == 0x05, (
                "post-read boundary did not capture Tackle's seventh "
                "critical command byte", context,
                mem[addr("wBattleEnded")]
            )
            assert bytes(
                mem[addr("wPartyMon1HP"):addr("wPartyMon1HP") + 2]
            ) == bytes([0, 100]), ("player party write-back HP changed", context)
            assert bytes(
                mem[addr("wOTPartyMon1HP"):addr("wOTPartyMon1HP") + 2]
            ) == bytes([0, 83]), ("enemy party HP was not written back", context)
            assert mem[addr("wPartyMon1PP")] == 34, (
                "player party PP changed during enemy doturn", context,
                mem[addr("wPartyMon1PP")]
            )
            assert mem[addr("wBattleMonPP")] == 34, (
                "player active PP changed during enemy doturn", context,
                mem[addr("wBattleMonPP")]
            )
            assert mem[addr("wOTPartyMon1PP")] == 33, (
                "enemy OT-party PP was not decremented by doturn + Pressure",
                context, mem[addr("wOTPartyMon1PP")]
            )
            assert mem[addr("wEnemyMonPP")] == 33, (
                "enemy active PP was not decremented by doturn + Pressure",
                context, mem[addr("wEnemyMonPP")]
            )
            assert mem[addr("wPlayerAbility")] == PRESSURE, (
                "player Pressure state changed before the checkhit boundary",
                context, mem[addr("wPlayerAbility")]
            )
            assert perform_move_calls == [True, True], (
                "did not reach exactly two BattleTurn PerformMove boundaries",
                context, perform_move_calls
            )
            assert perform_move_snapshots == [
                (25, native, 0, 33),
                (25, native, 1, 45),
            ], (
                "native identity/turn state changed across PerformMove entries",
                context, perform_move_snapshots
            )
            assert (
                mem[addr("wBattleScriptBufferLoc")],
                mem[addr("wBattleScriptBufferLoc") + 1],
            ) == advance_script_pointer(read_script_snapshots[19], 7), (
                "enemy seventh script read did not advance the script pointer "
                "by exactly seven bytes",
                context,
                (
                    mem[addr("wBattleScriptBufferLoc")],
                    mem[addr("wBattleScriptBufferLoc") + 1],
                ),
                read_script_snapshots[19],
            )
            assert mem[addr("wCurPlayerMove")] == 45, context
            assert mem[addr("wCurEnemyMove")] == 33, context
            assert mem[addr("wCurEnemyMoveNum")] == 0, context
            assert mem[addr("wCurMoveNum")] == 0, context

            count += 1

        print(
            f"PASS: {count} native enemy checkpriority -> critical cases; "
            "real enemy normal-priority Tackle checkpriority preserved native "
            "IDs, PP, Pressure and hit state -> seventh real "
            "ReadMoveScriptByte -> stop before enemy critical logic"
        )
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
