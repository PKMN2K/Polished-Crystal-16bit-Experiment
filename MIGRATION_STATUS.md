## Latest checkpoint: native damagecalc regression (2026-09-24)

- Added `tests/test_native_damagecalc_boundary.py` and wired it into normal/debug CI.
- The first nine original Tackle `NormalHit` commands now execute for real through:
  `checkobedience -> usedmovetext -> doturn/BattleConsumePP -> hastarget -> checkhit -> checkpriority -> critical -> damagestats -> damagecalc`.
- The test replaces only the following `stab` script byte with `endturn_command`, so real `BattleCommand_damagecalc` completes while STAB, damage variation, animation, later modifiers and HP application remain outside this checkpoint.
- The validated `damagestats` fixture supplies player Attack 90, enemy Defense 80, Tackle power 40 and player level 30. The real neutral base-damage calculation publishes `wCurDamage = 14`.
- Native player identity 25 and all six enemy native-identity cases remain intact across the full base-damage formula, including extended/native-variant cases.
- The test confirms `damagecalc` receives the real Attack/Defense/power/level outputs from `damagestats`, produces the expected neutral base damage, and leaves both battlers at 100 HP because `applydamage` is not reached.
- One intermediate failure was a test-lifetime issue only: the older checkhit assertion inspected `hMultiplicand` after `damagecalc` had legitimately reused that scratch buffer. The test now snapshots the 100%-accuracy result at the actual checkhit boundary.
- Final validation: GitHub Actions CI run **#206** (`36060731353`) passed on commit `529897cf36099f1c5d5f67f60a7f5054b6384908`.
  - native damagecalc boundary: 6/6 cases passed on normal ROM
  - native damagecalc boundary: 6/6 cases passed on debug ROM
  - all eight configured ROM build variants passed
  - artifact upload steps were skipped by the existing repository-owner guard as intended
- This checkpoint changes tests/CI only; no gameplay/migration source code was required.

**Next recommended step:** add a focused `BattleCommand_stab` regression that lets Tackle execute real STAB/type-modifier handling from the validated base damage, then stops before `damagevariation`.

## Latest checkpoint: native damagestats regression (2026-09-24)

- Added `tests/test_native_damagestats_boundary.py` and wired it into normal/debug CI.
- The first eight original Tackle `NormalHit` commands now execute for real through:
  `checkobedience -> usedmovetext -> doturn/BattleConsumePP -> hastarget -> checkhit -> checkpriority -> critical -> damagestats`.
- The test replaces only the following `damagecalc` script byte with `endturn_command`, so real `BattleCommand_damagestats` completes while later damage calculation and HP application remain outside this checkpoint.
- The physical Tackle path executes real damage reset, opponent Defense selection, player Attack selection, Future Sight user resolution, screen/modifier handling, held-item checks, true-user level lookup, and stat truncation.
- The synthetic boundary fixture seeds nonzero active Attack/Defense immediately before `damagestats`; no gameplay or migration source behavior is changed by the fixture.
- Native player identity 25 and all six enemy native-identity cases remain intact through the complete damage-stat path, including the extended/native-variant cases. Tackle remains move 33, the deterministic non-critical path remains clear, and PP remains 34/34.
- `damagecalc` and `applydamage` are not entered in this checkpoint; HP remains unchanged.
- Several intermediate failures were test-harness assumptions only: the non-sequential `damagecalc` command ID is $50, PyBoy exposes HL as a combined register, shared attribute helpers can temporarily flip battle perspective, and helper call counts are implementation details rather than identity invariants.
- Final validation: GitHub Actions CI run **#202** (`36059114401`) passed on commit `6eb5b5264282c747aa1119ec800ac66b66a7c4c4`.
  - native damagestats boundary: 6/6 cases passed on normal ROM
  - native damagestats boundary: 6/6 cases passed on debug ROM
  - all eight configured ROM build variants passed
  - artifact upload steps were skipped by the existing repository-owner guard as intended
- This checkpoint changes tests/CI only; no gameplay/migration source code was required.

**Next recommended step:** add a focused `BattleCommand_damagecalc` regression that lets Tackle execute real damage calculation from the validated Attack/Defense/power/level inputs, then stops before later damage modifiers/application.

# Polished Crystal to pokecrystal16 migration status

## Latest checkpoint: native critical-hit regression (2026-09-24)

- Added `tests/test_native_critical_boundary.py`. It extends the validated
  first-turn wild battle path through Tackle's real `checkobedience`,
  `usedmovetext`, `doturn` / `BattleConsumePP`, `hastarget`,
  `checkhit`, `checkpriority`, and then the real
  `BattleCommand_critical` path.
- Tackle's first seven original NormalHit commands remain real. The test
  terminates on the following script-byte read before
  `BattleCommand_damagestats`, damage calculation, or HP application.
- Only the two nondeterministic critical inputs are pinned for the fixture:
  affection remains below its critical threshold and the final
  `BattleRandomRange(24)` result is forced to a non-critical value. The real
  critical eligibility logic, `ResetCrit`, anti-critical opponent ability
  check, Unnerve-aware held-item reads, Future Sight user resolution, Super
  Luck lookup, affection check, and final 0-23 critical roll all execute.
- Player native ID 25 and the expected full 16-bit enemy native identity remain
  intact at `BattleCommand_critical`, through all opponent/user ability and
  held-item checks, and after the non-critical calculation returns to the
  move-script reader. Tackle remains move 33, `wAttackMissed` remains zero,
  and party/active PP remain synchronized at 34/34.
- The deterministic path leaves the critical bit clear. Player and enemy HP
  remain 100, `BattleCommand_damagestats`, `BattleCommand_damagecalc` and
  `BattleCommand_applydamage` are not reached, and legacy `GetBaseData`
  is not used.
- Coverage remains six cases: ordinary native roots, an extended root above
  `$00ff`, cosmetic presentations and two regional/mechanical variants.
- The first critical test attempt exposed only a fixture expectation: the real
  critical path performs four Future Sight user checks (directly, inside both
  held-item reads, and during the Super Luck lookup). Commit
  `7c9a3972c2fd484463dbcdbde4819e1e9f13c687` corrected that assertion
  without changing gameplay/migration source.
- Validation: GitHub Actions run #36042171429 **passed** on commit
  `7c9a3972c2fd484463dbcdbde4819e1e9f13c687`. The new regression passed
  all 6 cases on both normal and debug ROMs, and all eight ROM build
  configurations passed. The four artifact-upload steps were skipped only by
  the repository-owner guard, as intended.
- This checkpoint changes tests/CI/documentation only; no gameplay source,
  persistent Pokémon record or save format changed.
- Next recommended step: add a focused **`damagestats` regression** that
  lets Tackle execute the real `BattleCommand_damagestats` path, verifies
  both native identities survive its attack/defense-stat setup, then stops on
  the following script read before later damage processing.


## Latest checkpoint: native checkpriority regression (2026-09-24)

- Added `tests/test_native_checkpriority_boundary.py`. It extends the validated
  first-turn wild battle path through Tackle's real `checkobedience`,
  `usedmovetext`, `doturn` / `BattleConsumePP`, `hastarget`,
  `checkhit`, and then the real `BattleCommand_checkpriority`.
- Tackle's first six original NormalHit commands remain real. The test changes
  only the following `critical` command byte to `endturn_command` in
  emulator memory, so the seventh real `ReadMoveScriptByte` becomes the
  terminal boundary before critical-hit handling or damage.
- The real `checkpriority` path verifies the enemy is still alive,
  calls the real `GetMovePriority`, performs its user-ability check inside
  priority calculation, then performs the real Prankster and Soundproof
  ability checks for Tackle's normal-priority move.
- Player native ID 25 and the expected full 16-bit enemy native identity remain
  intact at `BattleCommand_checkpriority`, during the living-target check,
  entering `GetMovePriority`, and through all user/opponent ability checks.
  The move remains Tackle (33), `hBattleTurn` returns to the player side,
  `wAttackMissed` remains zero, and the preceding PP state remains 34/34.
- `BattleCommand_critical`, damage calculation and HP application are never
  reached; player and enemy HP remain 100 and legacy `GetBaseData` is not
  used.
- Coverage remains six cases: ordinary native roots, an extended root above
  `$00ff`, cosmetic presentations and two regional/mechanical variants.
- Validation: GitHub Actions run #36039494899 **passed** on CI commit
  `ef427fac8fbcee8fbc7ee6621ed87b90d216d4f5`. The new regression passed all
  6 cases on both normal and debug ROMs, and all eight ROM build configurations
  passed. Artifact-upload steps were skipped only by the repository-owner
  guard, as intended.
- This checkpoint changes tests/CI/documentation only; no gameplay source,
  persistent Pokémon record or save format changed.
- Next recommended step: add a focused **`critical` regression** that lets
  Tackle execute the real `BattleCommand_critical` path with deterministic
  non-critical conditions, verifies both native identities survive critical-
  hit eligibility/calculation, then stops on the following script read before
  `damagestats` or damage calculation.


## Latest checkpoint: native checkpriority regression (2026-09-24)

- Added `tests/test_native_checkpriority_boundary.py`. It extends the validated
  first-turn wild battle path through Tackle's real `checkobedience`,
  `usedmovetext`, `doturn` / `BattleConsumePP`, `hastarget`,
  `checkhit`, and then the real `BattleCommand_checkpriority`.
- Tackle's first six original NormalHit commands remain real. The test changes
  only the following `critical` command byte to `endturn_command` in
  emulator memory, so the seventh real `ReadMoveScriptByte` becomes the
  terminal boundary before critical-hit or damage processing.
- The priority handler runs its real living-target check and real
  `GetMovePriority`. Tackle follows the ordinary priority-0 encoding path,
  so it skips the Armor Tail-only positive-priority branch and proceeds through
  the real user Prankster check and opponent Soundproof check.
- The regression verifies the normal-priority path performs exactly the expected
  two user-ability lookups (one inside `GetMovePriority`, one for Prankster)
  and one opponent-ability lookup (Soundproof), while the enemy remains alive
  at 100 HP.
- Player native ID 25 and the expected full 16-bit enemy native identity remain
  intact at `BattleCommand_checkpriority`, through `HasOpponentFainted`,
  `GetMovePriority`, and all priority ability checks, and after control
  returns to the move-script reader.
- The preceding hit and PP state remain intact: Tackle has 34 PP in both the
  party and active battle record, `wAttackMissed` remains zero, and neither
  `BattleCommand_critical`, damage calculation nor HP application executes.
  Player and enemy HP remain 100 and legacy `GetBaseData` is not used.
- Coverage remains six cases: ordinary native roots, an extended root above
  `$00ff`, cosmetic presentations and two regional/mechanical variants.
- Validation: GitHub Actions run #36039494899 **passed** on CI commit
  `ef427fac8fbcee8fbc7ee6621ed87b90d216d4f5`. The new regression passed
  all 6 cases on both normal and debug ROMs, and all eight ROM build
  configurations passed. The four artifact-upload steps were skipped only by
  the repository-owner guard, as intended.
- This checkpoint changes tests/CI/documentation only; no gameplay source,
  persistent Pokémon record or save format changed.
- Next recommended step: add a focused **`critical` regression** that lets
  Tackle execute the real `BattleCommand_critical` path with deterministic
  non-critical conditions, verifies opponent ability, held-item, affection and
  critical-roll handling preserve both native identities, then stops on the
  following script read before `damagestats` or damage calculation.


## Latest checkpoint: native checkhit accuracy-resolution regression (2026-09-24)

- Added `tests/test_native_checkhit_boundary.py`. It extends the validated
  first-turn wild battle path through Tackle's real `checkobedience`,
  `usedmovetext` / `DisplayUsedMoveText`, `doturn` /
  `BattleConsumePP`, `hastarget`, and then the real
  `BattleCommand_checkhit` accuracy/evasion path.
- Tackle's first five original NormalHit commands remain real. The test changes
  only the following `checkpriority` command byte to `endturn_command` in
  emulator memory, so the sixth real `ReadMoveScriptByte` becomes the
  terminal boundary before priority blocking, critical-hit handling or damage.
- At `checkhit` entry the fixture pins only external shortcut inputs:
  neutral accuracy/evasion stages (7/7), no active ability/item/weather
  shortcut, no substitute/flying/minimized state, normal non-immune type
  modifier, and affection below its evasion threshold. The real
  `DoStatChangeMod`, `MultiplyAndDivide`, user/opponent ability lookups and
  `ApplyAccuracyAbilities` logic still execute.
- Tackle's real 100%-accuracy result resolves to `hMultiplicand = 100`.
  Polished Crystal still performs `BattleRandomRange(100)`; its possible
  result is 0-99, so the comparison is guaranteed to hit. The regression
  verifies that exact range call and that `wAttackMissed` remains zero.
- Player native ID 25 and the expected full 16-bit enemy native identity remain
  intact at `BattleCommand_checkhit`, throughout user/opponent ability
  checks, during the temporary opponent-turn perspective used by
  `ApplyAccuracyAbilities`, and after the handler returns to the script
  reader. The turn perspective is restored to the player afterward.
- The preceding PP behavior remains intact at 34/34. `BattleCommand_checkpriority`,
  `BattleCommand_critical`, damage calculation and HP application are never
  reached; player and enemy HP remain 100 and legacy `GetBaseData` is not
  used.
- Coverage remains six cases: ordinary native roots, an extended root above
  `$00ff`, cosmetic presentations and two regional/mechanical variants.
- Two initial CI attempts exposed only fixture assumptions, not migration
  failures: run #181 showed that `ApplyAccuracyAbilities` temporarily flips
  `hBattleTurn` while checking the opponent, and run #182 showed that exact
  100% accuracy still calls `BattleRandomRange(100)`. Commits
  `ca9420b0420635760ae8e7309f60c0ea081da3f1` and
  `7d2a1aefbe8889fcc9d3e95b23931b938ee091a9` corrected those assertions
  without changing gameplay/migration code.
- Validation: GitHub Actions run #36038044216 **passed** on commit
  `7d2a1aefbe8889fcc9d3e95b23931b938ee091a9`. The new regression passed all
  6 cases on both normal and debug ROMs, and all eight ROM build configurations
  passed. The four artifact-upload steps were skipped only by the
  repository-owner guard, as intended.
- This checkpoint changes tests/CI/documentation only; no gameplay source,
  persistent Pokémon record or save format changed.
- Next recommended step: add a focused **`checkpriority` regression** that
  lets Tackle's real `BattleCommand_checkpriority` execute at normal priority,
  verifies the living-target / move-priority / ability checks preserve both
  native identities, then stops on the following script read before
  `critical`, critical-hit calculation or damage.


## Latest checkpoint: native hastarget target-validation regression (2026-09-24)

- Added `tests/test_native_hastarget_boundary.py`. It extends the validated
  first-turn wild battle path through Tackle's real `checkobedience`,
  `usedmovetext` / `DisplayUsedMoveText`, `doturn` /
  `BattleConsumePP`, and then the real `BattleCommand_hastarget`.
- Tackle's first four original NormalHit commands remain real. The test changes
  only the following `checkhit` command byte to `endturn_command` in
  emulator memory, so the fifth real `ReadMoveScriptByte` becomes the
  terminal boundary before accuracy/evasion processing or damage.
- The enemy is alive at 100 HP. The regression verifies the real
  `HasOpponentFainted` living-target check and the real
  `GetOpponentIgnorableAbility` lookup both execute during `hastarget`.
- Player native ID 25 and the expected full 16-bit enemy native identity remain
  intact at `BattleCommand_hastarget`, during the target-faint check, during
  the opponent-ability lookup, and after the command returns to the script
  reader.
- The preceding PP behavior remains intact: Tackle starts at 35 PP and both
  `wPartyMon1PP` and `wBattleMonPP` are 34 when `hastarget` runs.
  `BattleCommand_checkhit`, damage calculation and HP application are never
  reached; player and enemy HP remain 100 and legacy `GetBaseData` is not
  used.
- Coverage remains six cases: ordinary native roots, an extended root above
  `$00ff`, cosmetic presentations and two regional/mechanical variants.
- Validation: GitHub Actions run #36022911810 **passed** on CI commit
  `a092bbbc215adbca2496c288099d346b8944df5a`. The new regression passed
  all 6 cases on both normal and debug ROMs, and all eight ROM build
  configurations passed. The four artifact-upload steps were skipped only by
  the repository-owner guard, as intended.
- This checkpoint changes tests/CI/documentation only; no gameplay source,
  persistent Pokémon record or save format changed.
- Next recommended step: add a focused **`checkhit` accuracy boundary
  regression** that lets Tackle enter the real `BattleCommand_checkhit`
  path with deterministic accuracy/evasion conditions, verifies both native
  identities survive the hit-resolution logic, then stops before
  `checkpriority`, critical-hit handling or damage calculation.


## Latest checkpoint: native doturn / PP-consumption regression (2026-09-24)

- Added `tests/test_native_doturn_pp_boundary.py`. It extends the validated
  first-turn wild battle path through Tackle's real `checkobedience`,
  `usedmovetext` / `DisplayUsedMoveText`, and then the real
  `BattleCommand_doturn` / `BattleConsumePP` path.
- Tackle's first three original NormalHit command bytes remain real. The test
  changes only the following `hastarget` command byte to
  `endturn_command` in emulator memory, so the fourth real
  `ReadMoveScriptByte` becomes the terminal boundary before target checks,
  hit checks or damage.
- The regression verifies native player ID 25 and the expected full 16-bit
  enemy native identity at `BattleCommand_doturn`, at `BattleConsumePP`,
  and after PP consumption returns to the move-script reader.
- Tackle begins with 35 PP. The real PP path decrements both
  `wPartyMon1PP` and `wBattleMonPP` to 34, proving the active battle PP
  state and the party record stay synchronized across the real third command.
- Coverage remains six cases: ordinary native roots, an extended root above
  `$00ff`, cosmetic presentations and two regional/mechanical variants.
  `BattleCommand_hastarget`, damage calculation and HP application are not
  reached; player and enemy HP remain 100 and legacy `GetBaseData` is not
  used.
- The first CI attempt exposed only a test-fixture assumption: battle-command
  IDs are not globally sequential, and `hastarget` is command `$3f` in the
  current table. Commit `7205cdfdb618aabbddeb172efd463ed737ff5555` fixes
  that assertion without changing migration/gameplay code.
- Validation: GitHub Actions run #36017423576 **passed** on commit
  `7205cdfdb618aabbddeb172efd463ed737ff5555`. The new regression passed all
  6 cases on both normal and debug ROMs, and all eight ROM build
  configurations passed. The four artifact-upload steps were skipped only by
  the repository-owner guard, as intended.
- This checkpoint changes tests/CI/documentation only; no gameplay source,
  persistent Pokémon record or save format changed.
- Next recommended step: add a focused **`hastarget` target-validation
  regression** that lets Tackle's real `BattleCommand_hastarget` execute
  against a living enemy, verifies both native identities survive target and
  ability checks, then stops on the following script read before
  `checkhit`, accuracy/evasion logic or damage.


## Latest checkpoint: native second move-script command dispatch regression (2026-09-24)

- Added `tests/test_native_second_effect_command_boundary.py`. It extends the
  validated first-turn wild battle path through Tackle's real
  `BattleCommand_checkobedience` and then its second real NormalHit command,
  `BattleCommand_usedmovetext`, including the live `DisplayUsedMoveText`
  state logic.
- The first two original NormalHit command bytes remain real. The test changes
  only the third byte (`doturn`) to `endturn_command` in emulator memory, so
  the third real `ReadMoveScriptByte` is the terminal boundary before PP
  consumption, target checks, hit checks or damage.
- Presentation-only work remains bounded: `StdBattleTextbox` is stubbed by
  the existing battle fixture and `ApplyTilemapInVBlank` is stubbed, while
  `UpdateUsedMoves`, move grammar and last-move state handling execute
  normally.
- Coverage remains six cases: ordinary native roots, an extended root above
  `$00ff`, cosmetic presentations and two regional/mechanical variants.
  Player native ID 25 and the expected full 16-bit enemy native identity remain
  unchanged at `usedmovetext`, inside `DisplayUsedMoveText`, and after the
  command returns to the script reader.
- The regression verifies Tackle (move ID 33) is recorded in
  `wPlayerUsedMoves`, `wMoveGrammar` becomes 33, and the script pointer
  advances across both real commands. `BattleCommand_doturn`,
  `BattleCommand_hastarget`, damage calculation and HP application are never
  reached; player and enemy HP remain 100 and legacy `GetBaseData` is not
  used.
- Validation: GitHub Actions run #36015091132 **passed** on CI commit
  `a0a85d7016b90c2aa79d1a2154efb7af18c9dc23`. The new regression passed
  all 6 cases on both normal and debug ROMs, and all eight ROM build
  configurations passed. The four artifact-upload steps were skipped only by
  the repository-owner guard, as intended.
- This checkpoint changes tests/CI/documentation only; no gameplay source,
  persistent Pokémon record or save format changed.
- Next recommended step: add a focused **third move-script command /
  `doturn` regression** that lets real `BattleCommand_doturn` perform its
  normal PP-consumption path, verifies native identities and the expected
  Tackle PP decrement, then stops on the following script read before
  `hastarget`, targeting, hit checks or damage.


## Latest checkpoint: native first move-script command dispatch regression (2026-09-24)

- Added `tests/test_native_first_effect_command_boundary.py`. It continues the
  validated wild `BattleIntro` -> `DoBattle` -> first-`BattleTurn` path
  through deterministic Fight selection, real move ordering, `PerformMove`,
  `DoTurn`, `CheckTurn`, `UpdateMoveData` and `InitializeMove`.
- Tackle's real `NormalHit` script now performs its first genuine script-byte
  read and dispatches the real `BattleCommand_checkobedience` handler. The
  regression verifies both active native 16-bit identity words at that command
  entry and again after the command returns.
- The test changes only the second `NormalHit` script byte in emulator memory
  to `endturn_command` for the test fixture. This makes the second
  `ReadMoveScriptByte` call the terminal boundary: `usedmovetext`,
  `damagecalc`, `applydamage` and all later Tackle commands remain
  unexecuted.
- Coverage remains six cases: ordinary native roots, an extended root above
  `$00ff`, cosmetic presentations and two regional/mechanical variants.
  Player native ID 25 and the expected full 16-bit enemy native identity remain
  unchanged through the first real battle-command dispatch.
- The regression also verifies the real command returns to the move-script
  reader, the move-script pointer advances correctly, neither player nor enemy
  HP changes from 100, and the legacy `GetBaseData` fallback is not used.
- Validation: GitHub Actions run #36012707661 **passed** on CI commit
  `42ef82ec7d76a5e35c0103186ce1140e53c2b031`. The new regression passed
  all 6 cases on both normal and debug ROMs, and all eight ROM build
  configurations passed. The four artifact-upload steps were skipped only by
  the repository-owner guard, as intended.
- This checkpoint changes tests/CI/documentation only; no gameplay source,
  persistent Pokémon record or save format changed.
- Next recommended step: add a focused **second move-script command dispatch
  regression** that lets Tackle's real `usedmovetext` command execute after
  `checkobedience`, verifies native identities still survive the return to the
  script reader, and stops before `doturn`, targeting, hit checks or damage.


## Latest checkpoint: native DoTurn initialization boundary regression (2026-09-24)

- Added `tests/test_native_do_turn_initialize_boundary.py`. It continues the
  validated wild `BattleIntro` -> `DoBattle` -> first-`BattleTurn` path
  through deterministic Fight selection, real move ordering and the first real
  `PerformMove`.
- Unlike the preceding `PerformMove` entry checkpoint, `DoTurn` now remains
  real through its pre-move state reset, `CheckTurn`, the in-turn
  `UpdateMoveData` refresh and `InitializeMove`.
- The terminal boundary is the first `ReadMoveScriptByte` call. The regression
  returns `endturn_command` there, so no Tackle battle command, move effect or
  damage routine executes.
- Coverage includes ordinary native roots, an extended root above `$00ff`,
  cosmetic presentations and two regional/mechanical variants. All six cases
  reach the first move-script read with player native ID 25 and the expected
  full 16-bit enemy identity unchanged.
- The test also verifies `PerformMove` clears the seeded damage sentinel,
  `CheckTurn` and `InitializeMove` each execute once, the real DoTurn
  move-data refresh runs, and `InitializeMove` publishes a non-null move-script
  pointer before the terminal boundary.
- Validation: GitHub Actions run #36010955185 **passed** on CI commit
  `11ab67857ddf55083c8daae303f54f98439807f4`. All eight ROM build
  configurations passed. The new regression passed 6 cases on both normal and
  debug ROMs.
- This checkpoint changes tests/CI/documentation only; no gameplay source,
  persistent Pokémon record or save format changed. It deliberately stops
  before executing the first move-effect command.
- Next recommended step: add a focused **first move-script command execution
  regression** that permits Tackle's initial deterministic command path to run
  far enough to verify native user/target identity through the first real
  effect-command dispatch, while still stopping before HP is modified.

## Latest checkpoint: native selected-move -> move-order boundary regression (2026-09-23)

- Added `tests/test_native_selected_move_order_boundary.py`. It continues the
  validated wild `BattleIntro` -> `DoBattle` -> first-`BattleTurn` ->
  player-action path with a deterministic valid Fight selection instead of
  canceling at `MoveSelectionScreen`.
- `MoveSelectionScreen` injects Tackle (move ID 33) in slot 0 and returns a
  successful selection. The remaining real player `ParsePlayerAction` path
  runs through its move-data update and housekeeping before reaching the real
  `DetermineMoveOrder` call site.
- `DetermineMoveOrder` is the terminal boundary for this checkpoint. The
  test snapshots player/enemy native identity, selected move, move slot and
  turn count there, then returns immediately from the caller so
  `PerformMove` cannot execute.
- Coverage includes ordinary native roots, an extended root above `$00ff`,
  cosmetic presentations and two regional/mechanical variants. Every case
  reaches move ordering with player native ID 25 and the expected full 16-bit
  enemy identity unchanged.
- The regression also verifies the selected move reaches the live
  `UpdateMoveData` call path, the enemy-action boundary is reached, no legacy
  `GetBaseData` fallback occurs, and `PerformMove` is never entered.
- Validation: GitHub Actions run #35946521799 **passed** on test/CI commit
  `450c4ab17fb9187b91d49002d451dbd7bfb949bc`. All eight ROM build
  configurations and all thirty focused regression steps succeeded with no CI
  errors. Normal **and** debug ROMs each passed 6 new selected-move /
  move-order boundary cases in addition to the previous 3,277 focused CPU
  cases, for **3,283 focused cases per ROM**.
- This checkpoint changes tests/CI/documentation only; no gameplay source,
  persistent Pokémon record or save format changed. It does not yet exercise
  real move-order calculation internals or execute either battler's move.
- Next recommended step: add a focused **move-order -> first `PerformMove`
  entry regression** that lets deterministic move ordering complete, enters
  the first real `PerformMove` setup far enough to prove the acting side's
  native identity is still correct, and stops before move effects/damage are
  applied.

## Previous checkpoint: native player-action / move-selection boundary regression (2026-09-23)

- Added `tests/test_native_player_action_move_selection_smoke.py`. It continues
  the validated wild `BattleIntro` -> `DoBattle` -> first-`BattleTurn`
  path past the first `BattleMenu` return with a deterministic Fight action.
- `ParsePlayerAction` remains real through its normal using-move branch. The
  regression reaches the real `MoveSelectionScreen` call site after
  `wMoveSelectionMenuType` and the move-selection animation ID are prepared,
  snapshots both active native identity words, then returns a deterministic
  canceled selection. A second `BattleMenu` pass terminates the smoke before
  move ordering.
- Coverage includes ordinary native roots, an extended root above `$00ff`,
  cosmetic presentations and two regional/mechanical variants. Every case
  reaches `ParsePlayerAction` and `MoveSelectionScreen` with player native ID
  25 and the expected full 16-bit enemy identity unchanged.
- The regression also verifies the first-turn AI/setup call boundaries still
  occur once, move-selection state is initialized as expected, legacy
  `GetBaseData` is not used, and neither `DetermineMoveOrder` nor
  `PerformMove` is reached.
- Validation: GitHub Actions run #35944687427 **passed** on test/CI commit
  `6816b2f9d6d808615e21cc4a1c25d84d4745249f`. All eight ROM build
  configurations and all twenty-eight focused regression steps succeeded with
  no CI errors. Normal **and** debug ROMs each passed 6 new player-action /
  move-selection boundary cases in addition to the previous 3,271 focused CPU
  cases, for **3,277 focused cases per ROM**.
- This checkpoint changes tests/CI/documentation only; no gameplay source,
  persistent Pokémon record or save format changed. It does not yet commit a
  selected move, run the full move-data update path, determine move order or
  execute either battler's move.
- Next recommended step: add a focused **selected-move -> move-order boundary
  regression** that makes `MoveSelectionScreen` return a deterministic valid
  move, lets the remaining real `ParsePlayerAction` setup complete, and
  reaches `DetermineMoveOrder` while stopping before `PerformMove`. Verify
  both active native identities remain stable through that transition.

## Previous checkpoint: native first-BattleTurn setup smoke regression (2026-09-23)

- Added `tests/test_native_first_battle_turn_smoke.py`. It keeps the real
  `BattleTurn` entry and core first-turn setup live after the validated
  `BattleIntro` -> `DoBattle` handoff, and runs until the first player
  `BattleMenu` boundary.
- The regression keeps real turn-counter increments, battle-action/reset state,
  `UpdateBattleMonInParty`, enemy/player turn selection,
  `IncrementTurnsTaken` and locked-in checks. Deep AI decision implementations
  and unrelated per-turn item/effect helpers are deterministic boundaries, but
  their real call sites are exercised and counted.
- Coverage includes ordinary native roots, an extended root above `$00ff`,
  cosmetic presentations and two regional/mechanical variants. Each case
  reaches `BattleMenu` with player native ID 25 and the expected full 16-bit
  enemy native identity unchanged, `hBattleTurn` on the player, total battle
  turns at 1, and both player/enemy turns-taken counters at 1.
- The test also verifies the enemy AI-choose, AI-switch and enemy-flee call
  boundaries are each reached once, no fallback through legacy `GetBaseData`
  occurs, and no player action/move execution happens beyond the menu boundary.
- Validation: GitHub Actions run #35943380328 **passed** on test/CI commit
  `a28b9439fa2fdfcdfb16dda054734f91de8d7c3b`. All eight ROM build
  configurations and all twenty-six focused regression steps succeeded with no
  CI errors. Normal **and** debug ROMs each passed 6 new first-`BattleTurn`
  setup smoke cases in addition to the previous 3,265 focused CPU cases, for
  **3,271 focused cases per ROM**.
- This checkpoint changes tests/CI/documentation only; no gameplay source,
  persistent Pokémon record or save format changed. It does not yet execute
  real AI decision internals, accept player menu input, choose a move, determine
  move order or execute a complete turn.
- Next recommended step: add a focused **player action / move-selection boundary
  regression** that continues past the first `BattleMenu` return with a
  deterministic selected action and reaches `ParsePlayerAction` /
  move-selection setup while verifying both active native identities remain
  intact before move-order and move-execution testing.

## Previous checkpoint: native DoBattle entry smoke regression (2026-09-23)

- Added `tests/test_native_do_battle_entry_smoke.py`. It runs the real wild
  `BattleIntro` first, then enters the real `DoBattle` setup and stops only
  at the first `BattleTurn` boundary.
- The regression keeps the enemy's native wild identity publication,
  picture/animation integration and the player-side `SendInUserPkmn` identity
  publication real. It verifies that the full 16-bit enemy shadow survives
  `DoBattle` initialization unchanged while the player's own native battle
  shadow is published independently.
- Coverage includes ordinary native roots, an extended root above `$00ff`,
  cosmetic presentations and two regional/mechanical variants. Each case
  reaches the real first-turn boundary with the expected enemy native word,
  a real player native word (Pikachu / native ID 25), and no fallback through
  legacy `GetBaseData`.
- Wild generation, UI/audio/transition work, entry hazards/weather/entry
  abilities and actual turn input/execution are deterministic fixture
  boundaries. `BattleTurn` itself is replaced with a `RET`, so no move
  selection or first-turn logic runs in this checkpoint.
- The first CI run (#35942594123) exposed a fixture omission rather than a
  migration failure: the new test forgot the preceding `BattleIntro` smoke
  test's terminating `TickPokeAnim` stub, leaving the real front-picture
  animation loop running. Restoring that boundary fixed the harness.
- Validation: GitHub Actions run #35942774688 **passed** on corrected test
  commit `6636cdfcf0d0c0c8890831c90a79399371d54e91`. All eight ROM build
  configurations and all twenty-four focused regression steps succeeded with
  no CI errors. Normal **and** debug ROMs each passed 6 new `DoBattle` entry
  smoke cases in addition to the previous 3,259 focused CPU cases, for
  **3,265 focused cases per ROM**.
- This checkpoint changes tests/CI/documentation only; no gameplay source,
  persistent Pokémon record or save format changed. It does not yet validate
  AI move selection, player menu input, move execution or a completed turn.
- Next recommended step: add a focused **first-`BattleTurn` setup smoke
  regression** that allows the real beginning of `BattleTurn` to run through
  enemy AI/setup and reaches the player `BattleMenu` boundary, verifying both
  active native identities remain intact before accepting input.

## Previous checkpoint: single-entry native wild BattleIntro smoke regression (2026-09-23)

- Added `tests/test_native_battle_intro_wild_smoke.py`. It enters the real
  `BattleIntro` once and keeps the outer wild sequencing live through
  `LoadTrainerOrWildMonPic`, `ClearBattleRAM`, `InitEnemy`,
  `SendInUserPkmn`, native enemy picture preparation/LZ decode/direct VRAM
  copies, `BattleStartMessage`, `BattleAnimateFrontpic` and native animation
  record setup.
- Wild-mon generation remains a deterministic fixture boundary, and
  transition/text/palette/HUD/audio/timing helpers are stubbed. The test still
  proves that the real outer battle-intro entry publishes the correct full
  16-bit enemy shadow, retains exact native base data, writes the expected
  front-picture and animated tiles to VBK0/VBK1, and records the expected
  presentation species/form and picture height.
- Coverage includes ordinary native roots, an extended root above `$00ff`,
  cosmetic presentations and two regional/mechanical variants. Each case also
  verifies the live `ClearBattleRAM` -> wild initialization handoff rather
  than calling `InitEnemy` and `BattleStartMessage` separately.
- The first CI run (#35938725099) exposed a test-fixture error: three guard
  stubs used a bare `RET`, so they inherited an arbitrary carry flag and could
  incorrectly enter the shiny/skip-animation branches. The corrected fixture
  explicitly returns carry clear for shininess, sleeping-tree and battle-effect
  guards and stubs the unrelated send-out animation playback.
- Validation: GitHub Actions run #35939051550 **passed** on corrected test
  commit `b6850f543b403aeef99be54a780f4db58cf95d01`. All eight ROM build
  configurations and all twenty-two focused regression steps succeeded with no
  CI errors. Normal **and** debug ROMs each passed 6 new single-entry
  `BattleIntro` smoke cases in addition to the previous 3,253 focused CPU
  cases, for **3,259 focused cases per ROM**.
- This checkpoint changes tests/CI/documentation only; no gameplay source,
  persistent Pokémon record or save format changed. It still does not validate
  real wild generation, the full transition/UI/palette/audio path, user input,
  turn selection, or an interactive battle loop.
- Next recommended step: add a focused **`DoBattle` entry smoke regression**
  that keeps the real `BattleIntro` handoff and verifies the native enemy
  identity survives into the first battle-loop boundary, while stubbing user
  input/turn execution before attempting full interactive battle automation.

## Previous checkpoint: native wild-battle introduction integration regression (2026-09-23)

- Added `tests/test_native_wild_battle_intro_integration.py`. It drives the
  live wild branches of `InitEnemy` and `BattleStartMessage` in sequence.
  Wild-mon generation is a deterministic fixture boundary, but the real
  `SendInUserPkmn` native-shadow publication, active-native base-data lookup,
  native enemy picture preparation, LZ decode, direct VBK0/VBK1 VRAM copies,
  `BattleAnimateFrontpic` dispatch and native animation-record setup execute.
- Coverage includes ordinary roots, an extended root above `$00ff`, cosmetic
  presentations and two regional/mechanical variants. The opponent begins with
  a different valid native shadow; the test proves the live wild send-in
  overwrites it from the legacy opponent record, then keeps that full 16-bit
  identity stable through picture and animation setup. It also verifies exact
  native base data, real front-picture/animated VRAM bytes, and the expected
  animation species/form, height and start tile.
- UI/text/audio helpers, wild generation and the final `TickPokeAnim` loop are
  stubbed intentionally. LCD remains off because the dedicated preceding
  regression already validates the real LCD-on Request2bpp/VBlank transfer
  scheduler.
- The first CI attempts exposed test-fixture assumptions rather than migration
  failures. A pre-switch shadow was changed from an arbitrary value to a
  different valid native ID because enemy ability reset occurs before the
  incoming shadow is republished. The failing assertion also incorrectly
  counted send-in, picture and animation base-data reads through one helper;
  the corrected test observes `GetBaseDataFromActiveBattleNativeSpecies` for
  send-in and `GetBaseDataFromEnemyBattleNativeSpecies` for picture/animation
  separately.
- Validation: GitHub Actions run #35937694123 **passed** on corrected test/CI
  commit `2099c7084747e2de5820e1a0b4a6cb47e398e7da`. All eight ROM build
  configurations and all twenty focused regression steps succeeded with no CI
  errors. Normal **and** debug ROMs each passed 6 new wild-introduction
  integration cases in addition to the previous 3,247 focused CPU cases, for
  **3,253 focused cases per ROM**.
- This checkpoint changes tests/CI/documentation only; no gameplay source,
  persistent Pokémon record or save format changed. It does not validate real
  wild-mon generation, palette/audio/text playback, full frontpic animation
  timing, user input or an interactive battle loop.
- Next recommended step: move one level outward with a focused **single-entry
  `BattleIntro` wild smoke regression**. Run the real outer battle-intro
  sequencing through initialization, wild picture preparation and start-message
  animation while keeping generation/UI transitions deterministic, before
  attempting `DoBattle` or full interactive battle automation.

## Previous checkpoint: native enemy trainer send-out picture/animation integration regression (2026-09-23)

- Added `tests/test_native_enemy_sendout_integration.py`. It enters the real
  `Function_SetEnemyPkmnAndSendOutAnimation` trainer send-out helper and keeps
  the native temporary-record bridge, enemy front-picture preparation, LZ
  decoding, direct VRAM tile copies, battle front-picture dispatch, native
  animation-record setup and native base-data/dimension lookup real.
- The regression deliberately stubs only unrelated presentation/audio work
  (Poké Ball send-out animation playback, shininess branch, music/HUD/effect
  helpers) plus the final `TickPokeAnim` loop so the test stops after the
  animation record is created. LCD is kept off here because the preceding
  checkpoint already validates the real LCD-on Request2bpp/VBlank scheduler.
- Coverage includes ordinary and extended native roots, cosmetic presentation
  forms, form normalization and two regional variants across two opponent party
  slots. A deliberately conflicting legacy opponent-party species/form guards
  native-shadow authority. The test verifies that the 16-bit enemy native
  shadow is unchanged, legacy `GetBaseData` is not used, native base data is
  exact, real VBK0/VBK1 front-picture tiles reach VRAM, and the animation record
  stores the expected presentation species/form, frontpic height and start tile.
- Validation: GitHub Actions run #35934058007 **passed** on corrected
  test/CI commit `356ecbf72ebc216b59d02910c99b7d2e5b6b1ba7`.
  All eight ROM build configurations and all eighteen focused regression steps
  succeeded with no CI errors. Normal **and** debug ROMs each passed 14 new
  send-out integration cases in addition to the previous 3,233 focused CPU
  cases, for **3,247 focused cases per ROM**.
- This checkpoint changes tests/CI/documentation only; no gameplay source,
  persistent Pokémon record or save format changed. It does not yet validate
  full Poké Ball/shiny/HUD/palette/audio playback, real frontpic animation tick
  timing, or a complete interactive battle. This regression specifically
  exercises the trainer enemy send-out helper; the live wild-battle
  introduction remains a separate integration boundary.
- Next recommended step: add a focused **wild-battle introduction integration
  regression** through the live wild intro path, checking that its native enemy
  shadow, real front-picture VRAM output and native animation record stay
  consistent before broadening into full interactive battle automation.

## Previous checkpoint: LCD-on native enemy front-picture VBlank transfer regression (2026-09-23)

- Added `tests/test_native_enemy_frontpic_vblank.py`. It runs the real
  native enemy front-picture preparation with the LCD enabled and forces
  each `Get2bpp` call to enter `Request2bpp` late enough in the
  scanline window that a pending transfer must be serviced through the
  real VBlank `Serve2bppRequest` path. The LZ decoder, padding,
  request scheduler, VBlank service and VRAM writes remain real.
- The regression compares native battle output against the generic
  renderer for the same presentation identity across ordinary and
  extended native roots, cosmetic presentations and two regional
  variants, under both battle-turn values. It verifies that the native
  route avoids legacy `GetBaseData`, retains exact native base data,
  executes pending scheduled 2bpp transfers, and produces byte-identical
  VRAM/dimension results to the generic presentation path.
- Validation: GitHub Actions run #35930670151 **passed** on CI/test
  commit `5823f6decf56bc399b438a48f9c0375835c3c490`.
  All eight ROM build configurations and all sixteen focused regression
  steps succeeded with no CI errors. Normal **and** debug ROMs each
  passed 14 LCD-on Request2bpp/VBlank cases in addition to the previous
  3,219 focused CPU cases, for **3,233 focused cases per ROM**.
  The LCD-on frame digests matched the previously validated native/generic
  tile data for the same presentation identities.
- This checkpoint changes tests/CI only; no gameplay source, persistent
  Pokémon record or save format changed. It validates scheduled LCD-on
  transfer servicing and resulting VRAM bytes, but not palette correctness,
  final on-screen pixels, human-visible animation timing or a complete
  interactive battle. Existing nonfatal unnecessary-farcall linker
  warnings remain.
- Next recommended step: move one level outward and add a focused
  **battle send-out integration test** that executes the real enemy
  picture preparation plus the battle animation entry in sequence,
  checking the native shadow, VRAM result and animation record together
  without yet attempting full interactive battle automation.

## Previous checkpoint: unstubbed native enemy front-picture VRAM regression (2026-09-23)

- Added `tests/test_native_enemy_frontpic_vram.py`. It executes the
  battle-only enemy front-picture entry with real LZ decompression,
  padding, direct 2bpp VRAM copying and animation-tile loading (LCD
  disabled in PyBoy); those low-level routines are **not stubbed**.
  It compares actual VRAM bank 0/1 tile bytes and sprite dimensions
  against the generic renderer with the same presentation species/form,
  while requiring exact native base data and no legacy lookup on the
  battle-only route.
- Covers ordinary and extended native roots, cosmetic presentations,
  two regional-variant identity-table entries, both battle turns and
  empty/reserved native enemy IDs. The generic comparison uses a
  deliberately conflicting enemy shadow to guard non-battle rendering.
  Normal/debug CI tests are wired in commit
  `81b2076068ab9380f0b5df639c486c865ffe5241`.
- Early runs exposed two **test-fixture** assumptions rather than a
  renderer mismatch. The first captured VBK1 before the real destination:
  the animated base frame is copied to `$9000` (the `vTiles5` address
  under VBK1), with additional animation tiles continuing above it. A later
  diagnostic stopped after a fixed four frames while
  `_Serve2bppRequest` was still legitimately using `SP` as its source
  pointer. The final fixture captures the correct VBK1 range through
  `rVBK` and advances until the CPU trampoline actually returns.
- Validation: GitHub Actions run #35929654099 **passed** on corrected
  test commit `629dac56590a65465fcff06ee8e61749aea9d6fb`.
  All eight ROM build configurations and all fourteen focused regression
  steps succeeded with no CI errors. Normal **and** debug ROMs each passed
  16 real native/generic decoder-and-VRAM-transfer cases in addition to
  108 animation-dimension, 107 frontpic-renderer, 72 enemy send-out,
  106 ghost-reveal, 106 Transform-picture and 2,704 move-animation-cry
  cases: **3,219 focused CPU cases per ROM**. The real-VRAM frame digests
  matched between native battle and generic presentation paths.
- This checkpoint changes tests/documentation only; no gameplay source,
  persistent Pokémon record or save-format activation changed. It proves
  real LZ decoding, padding and direct LCD-off 2bpp VRAM copies, but not
  the LCD-on VBlank/request-copy path, palette output, on-screen playback
  timing or a complete battle. Existing nonfatal linker farcall warnings
  remain.
- Next recommended step: exercise the **LCD-on Request2bpp/VBlank copy
  path** for the same native enemy roots/forms, so the actual scheduled
  transfer route is checked without yet broadening into full gameplay.

## Previous checkpoint: live battle front-picture animation call-site audit (2026-09-23)

- Inspected the live trainer send-out and wild-battle introduction
  paths, battle menu redraws, final-Pokémon slide-in, return-to-battle
  Poké Ball UI and no-animation substitute effect commands. Ordinary
  enemy frontpic redraws route through `GetMonFrontpic` /
  `GetFrontpicOrGhostpic`, with the battle-only native picture
  preparation; both trainer and wild encounter animations route through
  `BattleAnimateFrontpic` to
  `AnimateNativeEnemyBattleFrontpic` and the native dimension helper.
  Ghost and substitute branches remain intentional exceptions.
- Audited the inspected battle effect/move helpers and adjacent
  graphics/picture consumers for direct `AnimateFrontpic` and
  `LoadFrontpicAnim` calls. No additional direct generic frontpic
  animation invocation was found in those battle paths. The identified
  generic animation callers are trade, evolution, hatch, Hall of Fame
  and summary-screen flows; they should retain their non-battle
  legacy base-data side effects.
- This is a source-path audit; no runtime or test code, save layout or
  ROM build settings were changed. The last validated code checkpoint
  remains GitHub Actions run #35902373237 on
  `ada3437afd49db8a844525322f5dc279b9a41fe5`
  (eight ROM builds, twelve focused test steps passed). Source-path
  inspection does not validate actual pixels, animation timing or all
  indirect/script-triggered playback.
- Next recommended step: add a focused **unstubbed picture decode and
  VRAM tile-copy** CPU regression for native enemy root and regional-form
  front pictures. Compare native battle presentation to equivalent
  generic visual identities while verifying native base-data retention;
  retain separate ghost and substitute behavior.

## Previous checkpoint: native enemy battle front-picture animation dimensions (2026-09-23)

- `BattleAnimateFrontpic` now routes its normal, non-substituted enemy
  animation to `AnimateNativeEnemyBattleFrontpic`. That entry preserves
  the ambient species/form presentation globals, resolves the current
  16-bit enemy battle shadow, and retains the original slow-battle
  animation and native enemy cry.
- Animation setup shares the existing `LoadMonAnimation` record writer
  but explicitly selects a native enemy dimension helper through the
  new call entry `LoadNativeEnemyBattleMonAnimation`. Its
  `GetNativeEnemyFrontpicDims` switches to WRAM bank 1, reloads exact
  native enemy base data after send-out effects, and obtains the
  picture size from the ordinary `GetPicSize` table. The generic
  `AnimateFrontpic` / `GetFrontpicDims` retain their historical
  legacy `GetBaseData` side effect for menu, trade and hatching.
- Added `tests/test_native_enemy_frontpic_dimensions.py`, a focused
  PyBoy CPU regression for both battle turns, ordinary/extended/current
  variant identities, empty/reserved shadows, dimension storage,
  byte-exact base data, saved-global restoration and generic animation
  isolation. Sprite ticks and `GetPicSize` are stubbed; the test
  does not verify rendered frames or full animation timing.
- The first CI attempt, run #35902048443, exposed a PyBoy test-hook
  mistake: the tick stub was patched **after** hook registration, which
  removed its hook. The corrected fixture patches the stub first and
  reads the animation structure in its actual WRAM bank.
- Validation: GitHub Actions run #35902373237 **passed** on corrected
  code/test commit `ada3437afd49db8a844525322f5dc279b9a41fe5`
  with RGBDS 1.0.3 and PyBoy 2.7.0. All eight build configurations
  and all twelve focused regression steps succeeded, with no CI errors.
  Normal **and** debug ROMs each passed 108 native/generic front-picture
  animation-dimension CPU cases, 107 front-picture renderer cases,
  72 enemy send-out temp-record cases, 106 ghost-reveal cases,
  106 Transform-picture cases and 2,704 move-animation cry cases
  (3,203 per ROM). Existing nonfatal linker farcall warnings remain.
- The new regression stubs GetPicSize and the animation tick; sprite
  frames, visual playback and complete battle animations have not been
  validated. No persistent Pokémon layout or save-format activation
  changed. This status-only commit follows the tested code commit.
- Next recommended step: audit other live battle front-picture animation
  call sites for direct generic `AnimateFrontpic` usage or legacy
  dimension/base-data side effects before migrating another consumer.

## Previous checkpoint: battle-only native enemy front-picture preparation (2026-09-23)

- `GetFrontpicOrGhostpic` now routes non-ghost enemy battle pictures to
  `PrepareNativeEnemyBattleAnimatedFrontpic` in the native species ROM
  section. It resolves the current 16-bit enemy shadow and its presentation
  form and loads exact native base data before sprite preparation. The
  existing ghost-special picture branch is unchanged.
- `_GetNativeFrontpic` in the shared graphics bank enters the existing
  size/picture-pointer/decompression body after the legacy `GetBaseData`
  side effect. Generic `GetFrontpic`, `PrepareFrontpic` and
  `PrepareAnimatedFrontpic` retain that side effect for menu, trade,
  hatch and other callers. The native entry shares the DE destination save
  to fit the nearly full bank14 section.
- Added `tests/test_native_enemy_frontpic_renderer.py`, which uses the real
  native identity, base-data and picture preparation code with low-level
  decompression/tile-transfer stubs. It checks the native base-data buffer
  at both picture and animated-tile entry points and that the generic
  renderer still calls legacy `GetBaseData`. The existing battle-picture
  boundary test is updated for the new dispatch and CI runs the new test
  for normal and debug ROMs.
- The first builds revealed a two-byte bank14 overflow. Sharing the
  destination-register save removed three bytes and fixed the section limit.
  The next test run revealed a fixture mistake: its animated-tile hook read
  WRAM bank 6 (decompression scratch) rather than bank 1. The corrected test
  selects bank 1 for inspection and restores the executing bank afterward.
- Validation: GitHub Actions run #35899496080 **passed** on code/test commit
  `9b4a89ad40e0581eff13caef75d8fdc18528942c`. All eight build
  configurations and all ten focused test steps succeeded. Normal **and**
  debug ROMs each passed 107 native-enemy/generic frontpic cases, 72 enemy
  send-out temp-record cases, 106 ghost-reveal cases, 106 Transform-picture
  cases, and 2,704 move-animation cry cases (3,095 per ROM). There were no
  CI errors. The linker still reports two nonfatal `unnecessary farcall`
  warnings at `engine/16/native_species.asm` for `GetBaseData` and
  `PrepareEnemyBattlePictureIdentity`; these can be shortened in a
  later cleanup.
- The separate legacy `GetBaseData` call in picture-animation
  `GetFrontpicDims` is **not** migrated. Low-level sprite decompression
  and tile copying are stubbed in the new test; displayed pixels, complete
  battle animations and the full legacy CPU suite remain untested.
  No save-format activation or party/opponent layout change occurred.
  This status-only commit follows the successfully tested code commit.
- Next recommended step: migrate the **battle-only** front-picture
  animation-sizing path so `GetFrontpicDims` cannot overwrite native
  enemy base data; leave generic menu, trade and hatch animations untouched.

## Previous checkpoint: shared front-picture base-data boundary audit (2026-09-23)

- Inspected `engine/gfx/load_pics.asm` and `home/pokemon.asm`.
  `_PrepareFrontpic` calls legacy `GetBaseData` before `GetPicSize`, but
  `GetPicSize` derives the size directly from
  `wCurSpecies`/`wCurForm` and `PokemonPicSizes`. The same presentation
  fields select `PokemonPicPointers`; the image decoder does not consume
  `wCurBaseData` to determine sprite size or pointer. The legacy lookup is
  retained as a base-data-buffer side effect for later consumers.
- `engine/gfx/pic_animation.asm:GetFrontpicDims` independently calls
  legacy `GetBaseData` before `GetPicSize`; battle front-picture animation
  therefore has a second legacy base-data side effect.
- The front-picture functions are shared by non-battle callers. Confirmed
  examples: `home/pokemon.asm:PrepMonFrontpic` (general picture placement),
  `engine/gfx/trademon_frontpic.asm:GetTrademonFrontpic` (trades), and
  `engine/pokemon/breeding.asm:GetEggFrontpic` /
  `GetHatchlingFrontpic` (hatching). These callers supply their own
  presentation identity and cannot safely be redirected to the active enemy
  battle shadow.
- Battle `DropEnemySub` already publishes native enemy presentation
  identity and loads exact native base data before calling
  `GetFrontpicOrGhostpic`; `PrepareAnimatedFrontpic` then runs the
  shared legacy lookup, replacing that exact base data. A broad removal or
  unconditional native substitution could alter non-battle consumers and
  the later `GetFrontpicDims` side effect.
- This is a code-path audit only: no runtime, tests, save formats, or build
  settings were changed; the last passing compiled-code CI checkpoint remains
  run #35895629364.
- Next recommended step: add a **battle-scoped** front-picture preparation
  boundary that preserves native enemy base data through decompression and
  animation sizing without changing the generic menu/trade/hatch renderer.
  Budget changes outside the already-full bank14 and test both call paths.

## Previous checkpoint: native enemy send-out temporary-record base data (2026-09-23)

- `Function_SetEnemyPkmnAndSendOutAnimation` now calls
  `CopyEnemyBattlePkmnToTempMon`. The new send-out-only helper decodes the
  selected opponent party record into the existing legacy temporary format,
  loads base data through `GetBaseDataFromEnemyBattleNativeSpecies`, and
  reuses the ordinary `CopyPkmnToTempMon` copy body. It no longer performs the
  redundant preliminary `GetBaseData` lookup or the old copy routine's second
  legacy base-data lookup for a valid native enemy shadow.
- An empty native shadow takes a conservative legacy `GetBaseData` fallback
  while still copying the opponent party record. The general player/opponent
  temporary-copy API is unchanged, as are opponent party layout and all save
  formats. `GetMonFrontpic` already uses the native enemy picture identity
  bridge; its lower-level renderer still has an internal legacy `GetBaseData`
  call, which is outside this send-out temporary-record change.
- Added `tests/test_native_enemy_sendout_tempmon.py`: opponent party slots,
  both battle turns and format markers, roots/extended/current variants,
  intentionally conflicting legacy/global IDs, byte-exact temp record copying,
  and byte-exact native base data. It stubs the legacy `GetBaseData` entry to
  verify that valid shadows do not use it and that empty shadows take the
  fallback. No full send-out visuals or gameplay are tested.
- The first CI attempts (#35894269579 and #35894329386) exposed an
  RGBDS section-capacity error: bank14 reached $400B bytes (11 bytes over
  its $4000-byte limit). The send-out-only bridge was moved out of the full
  bank14, from `engine/pokemon/tempmon.asm` into the existing `16-bit ID
  stuff` ROM section in `engine/16/native_species.asm`. It now calls the
  legacy party-species/form readers and shared temp-record copy body through
  far calls; the generic temp-record copier retains its old code and layout.
- Validation: GitHub Actions run #35895629364 succeeded on code commit
  `b19f0cc2ddbbc2bee08a1888a3acf868905c9b94` with RGBDS 1.0.3.
  All eight build variants passed. PyBoy 2.7.0 passed 72 native enemy
  send-out temporary-record CPU cases on **each** normal and debug ROM;
  the existing cry (2,704), Transform picture (106) and ghost-reveal
  picture/Dex (106) focused cases passed on each ROM too. All eight
  focused test steps succeeded, with no CI error lines.
- The regression stubs legacy `GetBaseData`; it validates the native lookup
  and byte-exact copied record, not full send-out visuals, rendered pixels or
  the entire legacy CPU suite. No persistent format activation or
  party/daycare record change was made. This status-only commit follows the
  successfully tested code commit.
- Next recommended step: inspect the remaining internal `GetBaseData`
  call in `engine/gfx/load_pics.asm` (front-pic preparation), and identify
  which callers can supply an explicit native identity before changing the
  shared renderer used by non-battle screens.

## Previous checkpoint: native Silph Scope ghost reveal (2026-09-23)

- In `engine/battle/core.asm`, the live Silph Scope reveal now calls
  `RevealGhostEnemyFrontpic` instead of invoking `GetFrontpic` directly
  with whatever one-byte legacy identity was left in the renderer globals.
  The helper resolves the current enemy's native 16-bit battle shadow through
  `PrepareEnemyBattlePictureIdentity` and retains the original `vTiles0`
  ghost-to-Pokémon animation destination.
- `RecordRevealedGhostEnemySeen` resolves the same native shadow again after
  the reveal animation and passes the matching renderer-compatible species/form
  to `SetSeenMon`. It no longer pairs a possibly stale global species with
  `wEnemyMonForm`. Empty and reserved roots skip picture and seen calls.
- Added `tests/test_native_ghost_reveal_picture.py` to exercise both turn
  values, extended roots, current mechanical variants, legacy-identity
  conflicts, cosmetic normalization, empty/reserved identities and
  post-animation renderer-global changes. Frontpic and Dex functions are
  stubbed; displayed pixels and the full ghost battle are not yet verified.
- Validation: GitHub Actions run #35888906288 succeeded on code commit
  `3225bd9d3bd48747f6396434926bad9653f43cf3` with RGBDS 1.0.3.
  All eight build configurations passed. PyBoy 2.7.0 passed 106 native
  ghost-reveal picture/Dex CPU cases on **each** of the normal and debug ROMs.
  The existing native Transform-animation picture (106 per ROM) and
  move-animation cry (2,704 per ROM) focused regression tests also passed.
  All six focused test steps passed; the logs contained no CI error lines.
- Frontpic and Dex entry points are stubbed in the ghost-reveal CPU cases.
  Real displayed pixels, the full ghost battle, and the remaining CPU
  regression suite have not been validated by this run. No save-format
  activation or party/daycare layout was changed. This status-only commit
  follows the tested code commit.
- Next recommended step: inspect the live enemy send-out front-picture
  preparation in `Function_SetEnemyPkmnAndSendOutAnimation` for any remaining
  legacy base-data or temporary-record identity round-trips.

## Previous checkpoint: Beat Up animation reachability audit (2026-09-23)

- Inspected `BattleAnimCmd_BeatUp`, the move/animation tables, and the
  `anim_beatup` macro. Beat Up is not a defined move in
  `constants/move_constants.asm`; it has no entry in
  `data/moves/animation_pointers.asm`; and its former animation, including
  its sole `anim_beatup` invocation in the move animation source, is
  commented out as removed. The command and its macro remain defined, but
  the current shipped move-animation scripts do not invoke them.
- The retained command writes the one-byte `wBattleAnimParam` into
  `wCurPartySpecies` and gets its form from the active battle mon on the
  opposite side. This is not sufficient to identify a *different*
  contributing party member's 16-bit species or form. Replacing it with
  `PreparePlayerBattlePictureIdentity` or
  `PrepareEnemyBattlePictureIdentity` would incorrectly draw the active
  battler when the participating party member differs.
- No dead Beat Up runtime code was altered. If Beat Up is reinstated, first
  define its animation parameter contract and pass the contributing party
  member's full native identity (with correct side/form) into a dedicated
  picture identity bridge. Do not reinterpret `wBattleAnimParam` as a party
  index without changing its producer.
- This audit changes documentation only; the prior native Transform picture
  and move-animation cry builds/tests remain validated by CI run
  #35886997786. No new runtime validation or save-format changes.
- Next recommended step: inspect the next *live* direct battle-picture
  call, including the Silph Scope ghost reveal `GetFrontpic` path in
  `engine/battle/core.asm`, for legacy/native identity mismatches.

## Previous checkpoint: native Transform animation picture (2026-09-23)

- `BattleAnimCmd_Transform` now publishes renderer-compatible presentation
  species/form using `PreparePlayerBattlePictureIdentity` or
  `PrepareEnemyBattlePictureIdentity` from the acting battler's current
  16-bit native identity shadow. It no longer selects pictures using the
  legacy `wTempEnemyMonSpecies` / `wTempBattleMonSpecies` fields.
- The Transform battle command already synchronizes the current native shadow
  before its animation. Existing back/front renderer selection, tile destination
  and WRAM-bank handling remain unchanged. The original command's side effect
  of restoring `wCurPartySpecies` but retaining the rendered `wCurForm`
  on success is preserved. Empty and reserved IDs skip rendering.
- `tests/test_transform_animation_native_picture.py` exercises both acting
  sides, root and extended species, all current mechanical variants, conflicting
  legacy temporary/species fields, invalid native IDs and the renderer boundary.
  Front/back renderers are stubbed; pixel output and full Transform gameplay
  are not verified by this focused test.
- Validation: GitHub Actions run #35886997786 succeeded on code commit
  `8308699662ee1831c524a1638689f0d1006f3bb4` with RGBDS 1.0.3.
  All eight build variants passed. PyBoy 2.7.0 passed 106 native
  Transform-animation picture CPU cases and 2,704 move-animation cry CPU cases
  on **each** of the normal and debug ROMs. All four focused test steps passed.
  The first CI attempt exposed a test-fixture mistake (the acting turn did
  not always match the initialized identity); that test setup was corrected
  before this successful run. The subsequent status-only commit does not
  change compiled source or tests.
- These focused tests stub front/back renderers and audio. They do not verify
  pixel output, audible playback, full Transform gameplay, or the entire
  legacy CPU regression suite. No persistent save-format switch was made.
- Next recommended step: audit remaining battle-animation picture consumers,
  especially `BattleAnimCmd_BeatUp`, whose pictured party member may differ
  from the active battler; preserve that identity distinction before migrating.

## Previous checkpoint: native move-animation cry (2026-09-23)

- `BattleAnimCmd_Cry` now selects the acting battler's current 16-bit
  `wBattleMonNativeSpecies` or `wEnemyMonNativeSpecies` using `hBattleTurn`.
  It calls `LoadCryFromNativeIDBC` instead of reconstructing identity from
  the legacy battle species/form bytes. Transform and native mechanical variants
  therefore follow their current root-species cry.
- Existing player/enemy stereo tracks, four script parameters, pitch and length
  adjustments, asynchronous playback, and WRAM-bank restoration are unchanged.
  Empty native identities, eggs, and reserved root $0100 still skip playback.
- Added `tests/test_native_move_animation_cry.py` to exercise both battle
  turns, all current native identities, all four script parameters, conflicting
  legacy bytes, stereo selection, silent identities, and state restoration.
- Validation: GitHub Actions run #35876244644 passed all eight configured
  RGBDS 1.0.3 build variants. PyBoy 2.7.0 passed 2,704 focused
  move-animation cry CPU cases on each of the normal and debug ROMs.
  The preceding run exposed a test-harness parameter-injection error: the
  fourth-byte script parameter was not reliably updated between cases.
  The test now supplies the command byte from WRAM0 through the real
  `GetBattleAnimByte` reader and asserts the byte that was consumed.
- The test stubs audio output and does not establish audible playback or full
  gameplay. The full CPU regression suite was not rerun on this head; the
  2,704-case tests ran in CI rather than the local workspace.
- No persistent formats or automatic party/daycare activation changed.
- Next recommended step: inspect remaining legacy-species battle-animation
  picture consumers, starting with `BattleAnimCmd_Transform`, before changing
  their rendering identity boundary.

## Previous checkpoint: native battle front-animation cry (2026-09-23)

- Battle front-sprite animation now uses the appended `ANIM_MON_BATTLE_SLOW`
  scene, with `NativeEnemyStereoCry` followed by the existing Setup2/Play
  commands. Existing animation indices and non-battle scenes retain their
  original behavior.
- `PokeAnim_NativeEnemyStereoCry` switches from animation WRAM to battle WRAM,
  plays the enemy's current native identity through
  `PlayEnemyBattleStereoCryNoWait`, restores WRAM and advances the scene.
  Playback remains asynchronous and uses the enemy stereo tracks.
- Blocking player/enemy entry helpers share the same playback implementation
  and still call WaitSFX. No WRAM fields or persistent formats were added.
- Validation: normal and clean debug builds with RGBDS 1.0.3; 679 focused
  animation/legacy-cry CPU cases and 1,352 prior stereo-helper regression cases
  passed on each ROM with PyBoy 2.7.0. The new test runs TickPokeAnim dispatch
  across every current native identity and both turn values, checks cry
  parameters, WRAM restoration, scene advance and absence of WaitSFX, and
  exercises legacy stereo animation commands.
- Playback, WaitSFX and tile-map transfer are stubbed in these tests. Audible
  output, rendered animation, full gameplay, the full regression suite and
  other build configurations were not tested at this checkpoint.
- Next recommended step: migrate `BattleAnimCmd_Cry`, the move-animation cry
  command that still selects legacy battle species/form bytes.

## Previous checkpoint: native explicit battle-entry stereo cries (2026-09-23)

- The explicit player send-out cry now calls `PlayPlayerBattleStereoCry`;
  `BattleAnimateFrontpic.cry_no_anim` calls `PlayEnemyBattleStereoCry`.
- Each helper selects its side's current native identity independently of
  `hBattleTurn`, uses the native cry loader and retains normal cry duration.
  Both enable stereo while preserving the caller's channel mask and BC/DE/HL
  around identity loading and playback. Existing status/animation gates remain.
- Empty identities, eggs and reserved root $0100 skip playback; regional and
  mechanical variants retain their root species' cry.
- Validation: normal and clean debug builds with RGBDS 1.0.3; 1,352 focused
  CPU cases passed on each ROM with PyBoy 2.7.0. Coverage includes every
  current native identity, both speakers with both turn values, conflicting
  legacy fields, cry/pitch/normal duration, stereo/channel settings and
  register/stack/bank/global preservation.
- Playback and WaitSFX are stubbed in these focused helper tests; audible
  output, full send-out sequences, the full regression suite and other build
  configurations were not tested at this checkpoint.
- Persistent formats and automatic activation remain unchanged. The separate
  `PokeAnim_StereoCry` path still uses animation species/form fields.
- Next recommended step: inspect and migrate the stereo cry inside front-sprite
  animation, preserving the animation system's non-battle callers.

## Previous checkpoint: native fainting cry lookup (2026-09-22)

- The fainting path now calls `PlayFaintCryFromActiveNativeSpecies`, selecting
  the current player/enemy native shadow with `hBattleTurn` instead of reading
  legacy battle species/form bytes.
- `LoadCryFromNativeIDBC` resolves mechanical variants to their root cry and
  reuses the existing cry data loader. Empty identities, eggs and the reserved
  root $0100 remain silent without changing cry parameters.
- `PlaySlowCryNativeBC` shares the existing 1.5x length adjustment and playback
  tail with `PlaySlowCryBC`. Existing script calls retain their legacy interface;
  the battle caller's stereo mask and channel selection are preserved.
- Validation: normal and clean debug builds with RGBDS 1.0.3; 680 focused CPU
  cases passed on each ROM with PyBoy 2.7.0. Tests cover every current native
  identity on both sides, exact cry/pitch/length from compiled ROM records,
  conflicting legacy bytes, silent identities, bank/stack/global preservation,
  stereo settings and the existing legacy slow-cry interface.
- Audio playback and waiting are stubbed in the CPU tests. Audible output,
  complete fainting sequences, the full regression suite and the remaining
  build configurations were not tested in this checkpoint.
- Persistent record formats and automatic activation remain unchanged.
- Next recommended step: migrate the remaining explicit stereo cry calls in
  battle send-in/front-animation paths to native identity.

## Previous checkpoint: native Transform armor restriction (2026-09-22)

- Transform's early Mewtwo/Armor Suit restriction now selects the opponent's
  current native species word with `hBattleTurn`, resolves its root through
  `GetRootSpeciesFromNativeIDBC`, and compares the full 16-bit root ID.
- Root matching preserves the existing form wildcard: both ordinary Mewtwo
  and Armored Mewtwo are blocked when holding Armor Suit. A matching native
  identity without that item is not rejected by this particular check.
- The held-item pointer is preserved across the banked root lookup. Empty
  shadows do not fall back to stale legacy species bytes. The existing earlier
  rejection of an already-transformed target is unchanged.
- `tests/test_transform_native_restriction.py` executes 410 CPU cases covering
  both turns, all 46 mechanical variants, ordinary/extended/empty identities,
  held-item and wrong-side guards, deliberately conflicting legacy species,
  prior transformed status, and stack/bank/global preservation.
- Tests execute the real Transform entry, then stub its rejection and immediate
  post-restriction continuation. The rest of Transform and its animations are
  outside this focused test's scope.
- Validation: normal and clean debug builds with RGBDS 1.0.3; 410 focused CPU
  cases passed on each ROM with PyBoy 2.7.0. Full regression suite, other build
  configurations and end-to-end gameplay were not run at this checkpoint.
- Persistent record formats and automatic activation remain unchanged.
- Next recommended step: migrate the fainting cry identity lookup, which still
  reads the active legacy species/form pair before calling `PlaySlowCryBC`.

## Previous checkpoint: native battle picture-refresh identity (2026-09-22)

- `DropPlayerSub` and `DropEnemySub` now derive renderer identity from the
  corresponding current 16-bit active shadow, independently of `hBattleTurn`.
- `PreparePlayerBattlePictureIdentity` / `PrepareEnemyBattlePictureIdentity`
  bridge native identity into `wCurPartySpecies` and `wCurForm`, preserving
  BC/DE/HL. Mechanical variants use the canonical presentation form in
  `NativeVariantIdentityTable`. Root species retain cosmetic overlays only
  when those overlays resolve to the same native identity; conflicting
  mechanical forms fall back to the plain form.
- Empty shadows and reserved root $0100 return carry without publishing globals
  or calling a renderer. Both refresh paths restore the caller's party species
  and form. The enemy path loads base data through its direct native helper.
- Ghost-image dispatch is retained. This is a compatibility bridge: the shared
  picture loaders still consume legacy presentation values and the animated
  front loader still performs its own compatible base-data lookup.
- `tests/test_battle_picture_native_identity.py` covers 254 CPU cases: both
  sides and turns, all 46 mechanical variants, extended roots, cosmetic
  examples, conflicting legacy identities, empty/reserved IDs, preserved
  registers/banks, renderer dispatch, restoration and enemy base-data inputs.
  Integration cases stub renderer entry points; they do not test decompression,
  VRAM output, or on-screen appearance.
- Validation: normal and clean debug builds with RGBDS 1.0.3; 254 picture CPU
  cases passed on each with PyBoy 2.7.0. The prior 36 Low Kick CPU cases also
  passed on the normal build. Full regression suite, remaining six build
  configurations and visual gameplay testing were not run at this checkpoint.
- No persistent record format or automatic activation setting changed.
- Next recommended step: migrate Transform's Armored Mewtwo restriction,
  which still checks the opponent's legacy species byte and held item.

## Previous checkpoint: native Low Kick weight lookup (2026-09-22)

- `BattleCommand_lowkick` selects the opposing active native species word using
  `hBattleTurn` and calls `GetNativeSpeciesWeight`. It no longer reconstructs
  identity from the legacy battle species/form bytes.
- Existing positive-weight thresholds, Light Metal and ability-ignore behavior
  are preserved. Current transformed identity follows the native battle shadow.
- Empty native shadows and zero effective weights return minimum power (20).
  This also prevents the old loop from scanning beyond its final zero threshold
  for the reserved zero-weight native entry or an empty identity.
- Validation executed locally with RGBDS 1.0.3 and PyBoy 2.7.0: normal build
  passed; clean debug build passed; 36 focused CPU cases passed on each ROM.
  Cases cover both turns, ordinary/extended/regional identities, conflicting
  legacy bytes, wrong-side guards, empty identities, Light Metal and ability
  ignoring, plus BC/E, stack, ROM-bank and WRAM-bank preservation.
- Only this focused CPU test was run; the complete regression suite and the
  other six CI build configurations were not run for this checkpoint.
- Persistent party/opponent formats remain unchanged and automatic activation
  remains disabled.
- Next recommended step: inspect the active-battler picture refresh paths
  (`DropPlayerSub` / `DropEnemySub`) and their native identity boundaries.

## Previous checkpoint: native species-restricted battle items (2026-09-22)

- `UserValidBattleItem` now reads the current active 16-bit native species
  identity instead of reconstructing species/form from the legacy battle
  structure.
- The converted `ValidBattleItemTableNative` keeps the same three-byte record
  width as before: one item byte plus one native root-species word. The active
  native identity is resolved through `GetRootSpeciesFromNativeIDBC` before
  matching Light Ball, Leek, Lucky Punch, Quick Powder and Thick Club entries.
- The check intentionally follows the current transformed species rather than
  the original party species, matching the old active-battle semantics. The
  preceding Transform checkpoint keeps the native shadow synchronized.
- Root-species matching preserves the old zero-form wildcard behavior: a
  mechanical/regional form still receives an item effect attached to its root
  species, while unrelated roots do not.
- `tests/test_native_species_battle_items.py` adds focused CPU coverage for
  both active sides, a real mechanical-variant/root match, deliberate
  legacy/native disagreement, unrelated roots, empty shadows and wrong-item
  guards.
- No persistent party or opponent-party record format changed in this step.


## Previous checkpoint: faithful Metal Powder native Ditto check (2026-09-22)

- The faithful-mode `DittoMetalPowder` rule now checks the opponent's current
  16-bit active native identity instead of reading the legacy battle species and
  extended-species form bit.
- `IsOpponentActiveNativeSpeciesBC` selects the opposing active shadow from
  `hBattleTurn` and compares the full 16-bit native word. This correctly
  distinguishes high-byte identities and follows the current transformed
  species because Transform now synchronizes the native shadows.
- The non-faithful rule is intentionally unchanged: it still checks Ditto's
  original party species so Metal Powder continues to work after Ditto
  transforms, matching that mode's existing behavior.
- `tests/test_opponent_native_species_match.py` adds eight focused CPU cases
  covering both battle turns, exact full-word matching, wrong-side guards,
  deliberately conflicting legacy species bytes and an empty native shadow.
- No opponent party representation was changed by this checkpoint.


## Previous checkpoint: native battle-animation species lists (2026-09-22)

- `CheckBattleAnimSubstitution` no longer reconstructs the current move user's
  identity from `wBattleMonSpecies` / `wEnemyMonSpecies` plus the legacy
  form byte before checking curated native species lists.
- `IsActiveBattleNativeSpeciesInList` selects
  `wBattleMonNativeSpecies` or `wEnemyMonNativeSpecies` with `hBattleTurn`
  and compares the direct native word against the zero-terminated native-ID
  list. The helper preserves DE because the animation substitution path keeps
  its replacement animation ID there.
- This path intentionally uses the current active native identity rather than
  original party identity. The preceding Transform checkpoint keeps that shadow
  synchronized when a battler transforms.
- The Milk Drink/Fresh Snack, Fury Strikes/Fury Attack and Defense Curl
  animation-variation checks now use this direct native matcher.
- `tests/test_active_native_species_list.py` adds ten focused CPU cases across
  both battle sides, ordinary species, species #256, Alolan Raichu, wrong-side
  guards, deliberately conflicting legacy identities and empty native shadows.
- Legacy battle species/form fields remain populated for other unconverted
  consumers.


## Previous checkpoint: Transform native-shadow synchronization (2026-09-22)

- Transform now keeps the direct native active-battle identity shadow in sync
  with the legacy battle species/form representation it already copies.
- `CopyTransformNativeIdentity` copies the target's native word into the
  transforming user's shadow using `hBattleTurn`: enemy→player for a player
  Transform and player→enemy for an enemy Transform.
- This preserves the distinction between a battler's current transformed
  identity and its original party identity, which is required before more
  current-species battle consumers can safely move to native IDs.
- `tests/test_transform_native_identity.py` adds eight focused CPU cases:
  both transform directions, an ordinary species, species #256, Alolan Raichu
  and a zero native shadow.
- The legacy battle species/form fields are still copied exactly as before;
  this checkpoint only synchronizes the parallel native shadow.


## Previous checkpoint: native active-battler ability reset (2026-09-22)

- `ResetPlayerAbility` and `ResetEnemyAbility` now source species identity from
  `wBattleMonNativeSpecies` and `wEnemyMonNativeSpecies` instead of the
  legacy byte-sized battle species fields.
- `GetAbilityFromNativeIDBC` reads the selected ability directly from the
  native base-data record while retaining the existing personality ability-slot
  selector. It preserves the caller's personality pointer and treats native ID
  zero as no active ability rather than falling back to a legacy species byte.
- `tests/test_active_battle_native_ability.py` adds eight focused CPU cases:
  both active sides, ordinary species, species #256, Alolan Raichu, conflicting
  legacy identities and empty native shadows.
- This remains an incremental active-battle bridge. Legacy species/form fields
  are still populated for unconverted consumers, and opponent party records
  remain legacy.


## Previous checkpoint: native Heavy Ball weight lookup (2026-09-22)

- `HeavyBallMultiplier` now reads `wEnemyMonNativeSpecies` directly and uses
  `GetNativeSpeciesWeight` / `GetBodyDataPointerFromNativeIDBC` rather than
  reconstructing identity from `wEnemyMonSpecies` and `wEnemyMonForm`.
- An empty native enemy shadow leaves the current catch rate unchanged instead
  of consulting a possibly stale legacy identity.
- `tests/test_heavy_ball_native_weight.py` covers light, middle and heavy
  thresholds plus species #256, Alolan Raichu, deliberately conflicting legacy
  identities and an empty shadow.
- GitHub Actions CI run #21 passes all eight configured ROM build variants for
  the Heavy Ball code head.
- The focused PyBoy test is committed but was not executed in this chat.


## Previous checkpoint: native Safari catch-rate reset (2026-09-20)

- The Safari bait/rock expiry path is now the second active-battle consumer to
  use the 16-bit enemy identity shadow. `HandleSafariAngerEatingStatus` calls
  `ResetSafariCatchRateFromEnemyNativeSpecies`, which restores the normal
  catch rate from `wEnemyMonNativeSpecies`.
- `GetBaseDataFromEnemyBattleNativeSpecies` provides a side-specific native
  base-data reader that does not depend on `hBattleTurn`. It preserves
  BC/DE/HL and the legacy species globals.
- The Safari reset still publishes `wEnemyMonSpecies` and `wEnemyMonForm`
  into `wCurSpecies`/`wCurForm`, preserving the old side effect for
  surrounding legacy battle code. Only the base-data identity source changed.
- An empty native enemy shadow returns carry and leaves the current catch rate
  unchanged rather than applying stale base data.
- `tests/test_safari_native_catch_rate.py` adds four focused CPU cases:
  ordinary, species #256, regional/mechanical identity, and an empty shadow.
  The fixtures deliberately make the legacy enemy identity disagree with the
  native word and compare the restored catch rate with the compiled ROM record.
- GitHub Actions CI run #17 passes all eight configured build variants: normal,
  faithful, VC, faithful VC, debug, debug-faithful, debug VC and
  debug-faithful VC.
- The new PyBoy test is committed but was **not executed on this head in this
  chat**; the available GitHub workflow builds ROM variants only. The last
  executed full CPU checkpoint remains **5,979 cases per normal/debug ROM**.
- Active battle structs still retain the legacy byte/form representation and
  automatic persistent-format activation remains disabled.


## Previous checkpoint: native active-battler base data (2026-09-20)

- Active player and enemy battlers now have direct 16-bit native identity
  shadows: `wBattleMonNativeSpecies` and `wEnemyMonNativeSpecies`. They reuse
  existing battle scratch bytes and do not move the surrounding WRAM layout.
- `SendInUserPkmn` publishes the native word whenever either side enters
  battle. Player records use the persistent-format-aware reader; opponent
  records remain explicitly legacy while the larger opponent migration is
  still pending.
- The send-in base-data lookup now uses
  `GetBaseDataFromActiveBattleNativeSpecies`, selected by `hBattleTurn`.
  Legacy species/form globals and the byte-sized battle structs are still
  populated for consumers that have not yet migrated.
- The legacy-to-native reader now distinguishes a truly empty record from
  species #256, whose legacy representation uses species byte `$00` together
  with the extended-species form bit.
- GitHub Actions CI run #12 passes all eight configured build variants: normal,
  faithful, VC, faithful VC, debug, debug-faithful, debug VC and
  debug-faithful VC.
- `tests/test_active_battle_native_base_data.py` adds eight direct CPU cases
  covering both active sides, ordinary/extended/variant IDs, exact base data,
  empty shadows and register/global preservation. The existing send-in test was
  moved to stop at the new native lookup boundary. The PyBoy suite was **not
  rerun on this head in this chat** because the available GitHub workflow only
  builds ROM variants and this runtime cannot clone GitHub directly. The last
  executed PyBoy checkpoint remains **5,979 cases per normal/debug ROM**.
- Automatic persistent-format activation remains disabled. Active battle
  structures still carry their legacy byte/form representation alongside the
  new native shadows; this checkpoint migrates only the first consumer.


## Previous checkpoint: native original-attacker base data (2026-09-20)

- Delayed Future Sight's attacker-type lookup now uses the original party
  record directly. Player records resolve their stored native IDs; opponent
  records explicitly use the legacy species/form reader regardless of the
  player format marker.
- `GetBaseDataFromTrueUserParty` handles current and off-field delayed users,
  preserves BC/DE/HL and species globals, and leaves base data unchanged for an
  empty identity. This preserves the move-type register used by STAB.
- The legacy native-ID reader is shared with the player/daycare fallback, and
  both base-data wrappers share the empty-identity check.
- 1,200 new CPU cases check both battle sides, all six slots, current/delayed
  users, four marker states, metadata, exact ROM data, register/global/table
  preservation and empty records. These are lookup tests, not full Future Sight
  damage/animation or end-to-end high-species gameplay tests.
- Normal and clean debug builds pass without assembler/linker warnings with
  RGBDS 1.0.3. Each ROM passes **5,979 CPU cases** under PyBoy 2.7.0. Free space
  is 18,952 bytes normal and 18,838 bytes debug.
- Automatic migration activation and battle/opponent representation changes
  remain disabled.


## Previous checkpoint: direct native party base-data lookup (2026-09-20)

- Player HUD and experience-recipient base-data reads now resolve the stored
  native identity directly. The lookup no longer reconstructs its ID from the
  transitional species/form globals. Those globals are still populated for
  surrounding legacy consumers; this does not switch battle representation.
- `GetNativeSpeciesIDFromPokemonDataStruct` reads native IDs from a marked
  player/daycare record or translates an unmarked legacy record. It preserves
  source/form-offset pointers and does not allocate slots or change globals.
- `GetBaseDataFromPokemonDataStruct` preserves caller registers and globals.
  Empty identities return carry and leave the previous base-data buffer intact.
- 512 new CPU cases check all eight party/daycare slots, four marker states,
  ordinary/extended/regional identities, metadata, exact ROM base data, empty
  records, and unchanged conversion tables. Deliberately conflicting form bytes
  prove that transient base-data lookup uses the native ID itself.
- Normal and clean debug builds pass without assembler/linker warnings with
  RGBDS 1.0.3. Each passes **4,779 CPU cases** under PyBoy 2.7.0. Free space:
  18,989 bytes normal and 18,875 bytes debug.
- High native words are tested for identity preservation only. No new playable
  species is added, and automatic migration activation remains disabled.


## Previous checkpoint: PC identities, save integrity and deferred battle users (2026-09-20)

- PC party/temp transfers decode player IDs on withdrawal into the temporary
  workspace and encode them when returning to a transient party. OT records
  remain legacy. Newbox records now carry a native word in the two previously
  unused extra bytes, with species byte zero as the format tag. Existing legacy
  records remain readable and are upgraded when rewritten. Hypertraining,
  gender/Egg metadata, fixed record sizes and storage addresses are preserved.
- Delayed Future Sight, Attract/Rivalry and Love Ball comparisons use decoded
  party identities. Surf, stat-wing naming and move-learning form offsets are
  corrected. Mewtwo armor changes refresh the persistent native identity.
- Variant decoding now preserves its source pointer. The native-word roaming
  store now allocates the supplied species word instead of its destination
  address. Both defects have regression coverage.
- Conversion-table saves have their own checksum and publish their magic last.
  Primary and backup tables are verified before loading their respective save.
  A version word inside the existing game-data checksum distinguishes a torn
  new table from an old save with no table. Existing SRAM addresses do not move.
- Save version 11 reads version 10 lazily and stamps the new version before
  writing updated Pokémon data. Older ROMs reject version 11. Returning to an
  older ROM requires an untouched older save; this is not a downgrade format.
- `MigrateLegacyPlayerPokemonData` converts all six party slots and both daycare
  records in RAM, locks intermediate IDs during collection, writes the marker
  last, and releases the locks. Repeating it is a no-op. This routine is tested
  but **not invoked automatically** while the activation gate remains closed.
- Normal and clean debug builds pass with RGBDS 1.0.3, with 19,046 and
  18,932 free bytes respectively. Each ROM passes **4,267 CPU cases** with
  PyBoy 2.7.0: the prior 2,600 plus 384 deferred/gender/form cases, 1,152 PC
  transfers, 72 box round-trips and 59 migration/storage/save cases.
- Full migration is **not complete**. Normal gameplay still uses legacy player
  identities until activation, and opponent/battle runtime identities remain
  transitional. The tests of native words above `$01ff` cover allocation and
  storage only, not a playable species above that boundary.


## Previous checkpoint: held items and post-battle abilities (2026-09-20)

- Continues PR #1 from `3530fb3`.
- Shared user/opponent party identity helpers decode player records according
  to the persistent marker and leave opponent records legacy.
- Eviolite, non-faithful Metal Powder and essential-item protection use those
  helpers. Faithful Metal Powder retains its current battle-species rule.
- Post-battle ability processing now decodes the party species before Natural
  Cure/Pickup/Honey Gather checks, while retaining Egg exclusion.
- The existing player/opponent HP/status write-back needs no identity change;
  tests verify it preserves every byte outside the intended level/status/HP span.
- Normal and clean debug builds pass with RGBDS 1.0.3. Free space: 19,518 bytes
  normal; 19,404 bytes debug.
- Each ROM passes **2,600 CPU cases**: the previous 2,024 plus 480 held-item,
  48 Natural Cure and 48 write-back cases. These test marker variants, both
  sides, all six party slots, essential form matching and Egg exclusion.
- Full battles, item acquisition distributions and faithful builds are not
  tested by this checkpoint. Persistent-format activation remains disabled.

## Previous checkpoint: lead abilities and generated insertion (2026-09-20)

- Continues PR #1 from `d232f17`.
- Lead field abilities now decode persistent species before lookup while
  preserving caller registers and current species/form globals. Synchronize
  nature selection uses this helper and excludes Eggs from field abilities.
- `TryAddMonToParty` converts completed player records after legacy generation
  and stat calculation. Generated opponent records remain legacy, including
  wild/trainer records and gift staging. Successful insertion still sets carry.
- Normal and clean debug builds pass with RGBDS 1.0.3. Free space is 19,556
  bytes normal and 19,442 bytes debug.
- Both ROMs pass **2,024 CPU cases**: all previous 1,592 plus 288 lead-ability
  cases and 144 complete generated-party insertions. New cases cover absent,
  partial and valid format markers, species/forms, ability slots/options,
  gender/Egg flags, all six target slots and player/opponent destinations.
- This does not validate complete trade UI or nature distributions. Persistent
  format activation, old-save conversion and gameplay validation remain pending.

## Previous checkpoint: collection roots and ordinary catches (2026-09-20)

- Continues PR #1 from `482db5e`.
- Conversion-table collection scans player/daycare records only when the
  persistent format marker is valid. All six player slots stay protected,
  including those hidden by the Bug-Catching Contest's temporary party count.
- Roamers, all three contest winners and the temporary contestant record remain
  roots. Locked/recent IDs remain protected by the existing table machinery.
- Legacy opponent, battle, temporary, contest-catch and Odd Egg records, plus
  legacy species globals, no longer pin coincidentally equal slot numbers.
- Ordinary catches now copy the legacy opponent record through
  `CopyCaughtPokemonToParty`, converting only the player destination identity.
  Naming, caught-data, Friend Ball and Heal Ball handling continue afterward;
  full-party PC catches still use the existing Newbox path.
- Clean normal/debug builds pass with RGBDS 1.0.3, without assembler/linker
  warnings. Free space: 19,585 bytes normal; 19,471 bytes debug.
- Each ROM passes **1,592 isolated CPU cases**: the previous 1,008, plus eight
  collection/allocation cases and 576 caught-record copies. New tests include
  a full conversion table, locks/recent IDs, contest-hidden slots, format-marker
  variants, Mismagius, Alolan Raichu, and gender/Egg metadata.
- These tests cover the storage helper, not interactive capture animations,
  nickname prompts, ball effects, or PC delivery. Persistent-format activation
  remains disabled; save conversion and full gameplay testing remain pending.

## Previous checkpoint: temporary-record identity boundary (2026-09-20)

- Continues the player battle-reader checkpoint from PR #1 (`c7079f1`).
- `CopyPkmnToTempMon`, `GetPkmnSpecies`, and `GetPkmnForm` now distinguish
  persistent player/daycare records from legacy opponent/link records.
- Player transient decoding preserves gender/Egg bits in the temporary form
  byte instead of overwriting them with the masked identity form.
- The source-type guard resides with the format helpers to fit the loader's
  nearly full ROM bank. Persistent-format activation is still disabled.
- Normal and clean debug builds pass with RGBDS 1.0.3; free space is 19,534
  bytes normal and 19,420 bytes debug. No new build warnings remain.
- Both ROMs pass 576 full temporary-record copy cases and all 432 existing
  battle-boundary cases under PyBoy 2.7.0: **1,008 cases per configuration**.
  Coverage includes absent/partial/valid markers, both party types, six slots,
  extended and variant identities, metadata, source preservation, and bank/
  stack preservation. These isolated CPU tests are not gameplay validation.

## Previous checkpoint: player battle readers (2026-09-20)

- Continued from repository `master` at `e47d19bd1e94fdfc4e85e6f252ae5c2757836c28`.
- The archived overworld/special-event reader slice is now imported source;
  its previously pending debug build has passed.
- Player battle entry now decodes persistent party identity before populating
  legacy battle species/form globals. Opponent parties remain explicitly legacy.
- The player HUD and experience-growth lookup now decode player party identity.
- Clean normal and debug builds passed with RGBDS 1.0.3. Reported ROM free
  space: 19,557 bytes normal; 19,443 bytes debug.
- Isolated PyBoy 2.7.0 CPU tests passed: 144 decoder cases on the normal ROM;
  144 decoder plus 288 send-in cases on the debug ROM. Tests cover both storage
  formats, all six slots, native ID 256, Alolan Raichu, metadata preservation,
  untouched source records, and legacy opponent battle entry.
- These are routine-level tests, not gameplay, save-upgrade, or species-above-
  `$01ff` end-to-end validation. The persistent-format marker remains disabled.

The snapshot sections below describe the original archive, including its
historical uncommitted state; use this checkpoint and the next-step section for
current progress.

## Snapshot identity

- Branch: `migration/16bit-species`
- Polished Crystal baseline: `f22d31a52cbbf1387d27ba63f5bf2fa959955d37`
- pokecrystal16 reference baseline: `e9701dce610e3b421356206992f93ed604085cd8`
- Required RGBDS version: 1.0.3
- Last completed commit: `3d08aaacc Make Battle Tower party boundaries format-aware`
- Export state: includes the uncommitted overworld/special-event reader work
  described below, plus this status file and the README build section.

This is a source snapshot of an unfinished migration. The 16-bit species system
must not yet be treated as complete or enabled for persistent Pokémon records.

## Already migrated

- The pokecrystal16 table macros, indirection routines, home-bank helpers, WRAM
  conversion table, locking, garbage collection, and SRAM persistence have
  been adapted to Polished Crystal.
- Mechanically distinct variants have canonical native 16-bit species IDs.
  Cosmetic and runtime forms remain in the separate form byte.
- Native/legacy/transient identity domains have explicit conversion helpers.
- Native lookup layers cover base stats, names, evolution and level-up data,
  egg moves, palettes, footprints, sprites, animations, picture sizes, icons,
  overworld palettes, cries, Pokédex entries, and body data.
- Trainer parties, scripted encounters, wild tables, special encounters,
  gifts, NPC trades, classification lists, hidden grottos, Odd Eggs, Battle
  Tower sets, and Pokédex ordering store native 16-bit IDs in ROM where their
  readers have already been adapted.
- Pokédex flags, roaming Pokémon, Bug Contest winners, Hall of Fame native
  shadows, conversion-table primary/backup save data, and related native-ID
  persistence infrastructure are present.
- Dual-format party/daycare structure helpers support legacy records and the
  future transient-ID persistent format.
- Party loading/search/menu, evolution, insertion, breeding/daycare, egg
  lifecycle, maintenance, graphical readers, Hall of Fame serialization, Gen 2
  link serialization/trade UI, and Battle Tower player-party boundaries have
  been made format-aware.
- The latest completed step, commit `3d08aaacc`, converts player records crossing
  Battle Tower work areas while retaining their established legacy layouts.

For the detailed checkpoint history and data-preservation notes, see
[`docs/16_bit_species_migration.md`](docs/16_bit_species_migration.md).

## Partially migrated in this snapshot

The working tree contains an unfinished overworld and special-event reader
slice after `3d08aaacc`. It updates identity reads used by:

- the Ho-Oh chamber party check;
- Professor Elm's evolution phone calls;
- script-selected Poképics;
- Wonder Trade's Spiky-eared Pichu restriction;
- outgoing NPC-trade metadata;
- the Judge Machine party switch;
- poison-step ability checks; and
- the general script helper that derives the current party species.

These edits are deliberately uncommitted. A clean normal build passed. The
final clean debug build and commit review were not completed before export.
Representation-independent reads such as Egg flags and structure offsets remain
direct byte reads by design.

## Not yet migrated or activated

- Automatic party/daycare conversion remains disabled. The RAM conversion
  routine exists and is tested; it is not wired into old-save load or new-game
  initialization until the complete consumer audit and gameplay gate pass.
- Opponent-party and central battle workspaces still store legacy identities.
  Their ingestion, consumers, temporary references and collection roots need
  to switch together if they are made transient.
- `GetLegacySpeciesAndFormFromNativeIDBC` still reduces a root species to a
  byte plus `EXTSPECIES_MASK`. This cannot represent an arbitrary root above
  `$01ff`; simply enabling the marker does not remove this limit. The current
  catalog ends at native ID `$0151`.
- Full save/load recovery, catch, evolution, breeding, PC, trade, Battle Tower,
  link, Hall of Fame, Pokédex and battle gameplay regressions remain pending.
  CPU calls into individual routines do not establish those complete flows.
- No end-to-end playable proof species above `$01ff` has been added or tested.
- 16-bit move and item IDs are outside the species milestone.

## Historical imported-archive build notes and workarounds

- The last committed checkpoint passed clean normal and debug builds with RGBDS
  1.0.3.
- The included uncommitted reader slice passed a clean normal build. Its clean
  debug build had not been run when this archive was created.
- No known source-level linker or assembler error is present in the normal
  configuration.
- RGBDS 1.0.3 was kept outside the repository during development and invoked by
  prepending its directory to `PATH`. It is not bundled in this archive.
- A monochrome build must be started after `make tidy`; reusing normal-mode
  generated objects can trigger palette-size assertions unrelated to the
  migration source.
- ROM0 space was reclaimed by moving `HandleStoneTableAction` beside its sole
  caller. This allows the 16-bit home routines to link without trampolines.
- The conversion table occupies WRAM bank 2 at `$d500-$d5ff`; its save copies
  use previously unused SRAM padding so existing checksum and Newbox addresses
  do not move.

## Remaining implementation sequence

Replace the nine-bit runtime boundary with native-aware battle/opponent data
access, including every writer and the collection roots for any new transient
workspace. Add an actual species above `$01ff` with complete lookup data and
prove generation, battle, party, PC and save/load identity round-trips. Then
wire the tested RAM conversion into save loading/new-game setup and run the
complete gameplay and backup-recovery matrix before enabling the format by
default. Native Newbox entries contain words directly and do not pin transient
conversion-table slots.

## Build commands

Install RGBDS 1.0.3 and the dependencies documented in `INSTALL.md`. With RGBDS
on `PATH`:

```sh
make tidy
make -j2
```

For the debug configuration:

```sh
make tidy
make -j2 debug
```

The generated `.gbc`, `.map`, `.sym`, object files, and compiled assets are
build products and are not included in the export. The project can regenerate
them from the included source and tool code.

## CPU regression tests

After building, install the optional emulator dependency and run all tests:

```sh
python -m pip install pyboy==2.7.0
for test in tests/test_*.py; do
  python "$test" polishedcrystal-3.2.3.gbc || break
done
```

After a debug build, substitute `polishedcrystal-debug-3.2.3.gbc`. Each ROM must
have its matching `.sym` file alongside it. Tests use disposable emulator state
and synthetic SRAM; they do not read or overwrite user saves. Coverage includes
party and battle identities, temporary records, collection, caught/generated
insertion, abilities/items, deferred users, gender, armor forms, PC encoding,
RAM migration, save version acceptance and primary/backup table integrity.
