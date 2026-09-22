# Polished Crystal to pokecrystal16 migration status

## Latest checkpoint: Transform native-shadow synchronization (2026-09-22)

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
