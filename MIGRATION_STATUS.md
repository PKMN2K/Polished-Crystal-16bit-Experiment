# DanielOlivaw 16-bit migration status

**Status: native species and move-ID port integrated; wild/trainer battles, capture, PC/daycare transfers, move learning, evolution, hatching and cold save reload validated. Full playthrough and linked hardware/emulator validation remain.**

Branch: `migration/danielolivaw-16bit` in
`PKMN2K/Polished-Crystal-16bit-Experiment`.

## Sources

- Polished Crystal source: `Rangi42/polishedcrystal@bd535b89f8e1337151b715f76a235296c26a60c7`.
- Requested donor: `DanielOlivaw/pokecrystal16@ace283e879e8dd683fc0ccc26e8b85e70dc72313`.
- Compatible Polished adapters reused from `migration/battle-party-readers@f2089e9e6580c0113217c13db4bdee4ec39db28c`.
- Toolchain: RGBDS 1.0.4, PyBoy 2.7.0, Python 3.12; Pillow 13.0.0 for gameplay screenshots.

The donor shares the original aaaaaa123456789/pokecrystal16 index architecture.
Conversion-table macros, bank-safe home wrappers, table allocation and indirect
pointer routines were checked against the requested donor. The species and move
adapters use that architecture with current RGBDS syntax and Polished-specific
party, form, Newbox and save layouts. Additional roster and gameplay content
were not imported. Source commits and SHA-256 hashes of donor reference files
are recorded in `docs/16bit-sources.json`.

## Native identities and consumers

- Native species identities retain separate mechanical variants, byte runtime
  aliases, allocation, locks and garbage collection. Trainer/wild/event species
  records and stats, names, evolution, learnsets, graphics and Pokédex lookups
  use native identities.
- Fresh games initialize native player/daycare storage and native move handling.
  Opponent and temporary species records retain their byte/form layout with
  tagged conversion-table handles for wide roots. Direct battle identity shadows
  preserve full words independently of those aliases.
- Move IDs use a separate donor-style 230-entry conversion table with 18 lock
  slots, 16 recent allocations and a 16-entry cache. The table occupies 512 WRAM
  bytes. Party/daycare, both battle sides, temporary/link records, move menus,
  AI/history and animation state are garbage-collection roots. A compile-time
  bound reserves enough entries for all roots, locks and recent allocations.
- Move data, names, descriptions and animations use native table indirection.
  Catalog ordinals map sparse wide IDs to data without allocating thousands of
  empty pointer entries. Ordinary battle moves keep a byte runtime handle;
  animation controls retain their independent `$0100+` namespace.
- Move constants, AI/ability lists, priorities, traps, conditional boosts,
  Metronome, Sketch/Transform, learning, breeding, evolution parameters,
  relearner/tutor/TM paths, trainers, Battle Tower, special eggs, wild encounters,
  gifts, field moves and radio move names use the native adapters.
- Evolution targets and Pokédex lists retain native species words and separate
  form/metadata. Evolution readers skip whole records, including word move
  parameters, so `$ff` inside an ID is never a list terminator.
- Current upstream's grass encounter rate, Bloodmoon Battle Tower sets, assets
  and gameplay data are retained. Existing species fixes cover daycare gender
  and form inheritance, Metal Powder and native Hall of Fame restoration.
- Opponent party/name copies now resolve each source address explicitly; the
  new link sidecar means those arrays no longer share one offset from the
  player arrays. The relearner supplies the explicit species-to-form offset.
- Scripted wild encounters allocate wide runtime aliases through the shared
  native species/form decoder. Folding the native high byte into the form had
  turned species `$02ff` into byte `$ff` with an incorrect Egg flag.
- Post-battle berry conversion preserves its party counter across species
  decoding. The overwritten counter could scan beyond the party or leave a
  completed battle stuck after the experience message.
- Trainer party readers use the same native species/form decoder as scripted
  encounters. The old high-byte-to-form packing truncated `$02ff` to `$00ff`
  and set Egg metadata in a real trainer battle.
- Phone trainer names resolve native words directly. The party walker now
  preserves the record boundary and skips variable nicknames and escaped move
  IDs, so it can select every party member without treating move bytes as species.
- Daycare growth queries decode saved species handles before calling the runtime
  level calculator. Without this boundary conversion, the wrong growth group
  could make a level-20 wide species return at level 22 without taking any steps.
  The existing withdrawal policy of resetting EXP to the level floor is retained.

## Formats and compatibility

The ROM remains **2 MiB MBC3 with 32 KiB SRAM**, and the PC retains **400 usable
Pokémon slots**. Native move words are stored at persistent and link boundaries;
transient handles are reconstructed for the current session.

| Boundary | Encoding |
| --- | --- |
| Runtime move slots | Byte handles into the independent move table; zero means no move |
| Sequential ROM move streams | IDs `$0000–$00fe`: one byte; IDs `$00ff–$ffff`: `$ff` escape plus little-endian word |
| Indexed ROM move arrays | Little-endian native words; list terminators are explicit `$ffff` words |
| Primary/backup party and daycare saves | 32 native move words per copy, with magic and checksum, in existing padding |
| PC record | 51 bytes; four native low bytes plus four high bytes, all checksummed |
| Link party | Move low bytes in each record and 24 high bytes after the six records |

`move_id` emits the compact ROM stream; `ReadMoveIDFromHL` allocates its runtime
handle and `SkipMoveIDFromHL` skips an entire encoded ID. Fixed arrays use `dw`
and `ReadMoveWordFromHL`. Runtime literals use `ld_move` and `cp_move`.
Learnset level terminators remain separate from the encoded move. Native move
zero means no move, and `$ffff` remains reserved, never a playable move.
Adding moves requires real data/name/description/animation records and catalog
mapping, rather than increasing a count alone.

**Save version 13 is required.** Versions 10, 11 and 12 are rejected; no automatic
old-save importer is provided. Party/save block lengths remain unchanged. PC
records store species low/high directly, derive level from experience, and use
17 name characters for the existing character/checksum encoding. Binary move
highs have separate checksum coverage. Each database half has 160/27/20 records
across its three SRAM sections: 207 per half, 414 physical records total.

**Link protocol 7 is required for both trading and battles.** The receiver
validates every species and move word before allocating peer-local aliases.
The party packet is 465 bytes; serial escaping covers the added move sidecar.
The mail buffer boundary remains separate.

| Party field | On the wire | After receiving |
| --- | --- | --- |
| `MON_SPECIES` | Native species low byte | Local runtime species byte |
| `MON_UNUSED` | Native species high byte | Zero |
| `MON_FORM` | Form, egg and gender metadata; EXTSPECIES clear | Locally encoded form/metadata |
| `MON_MOVES` | Four native move low bytes | Four local runtime move handles |
| Move sidecar | Four native move high bytes per slot | Used to reconstruct those handles |

Eggs carry their underlying native species, never the `$00ff` display sentinel.
Unused slots are zeroed. Unsupported IDs, invalid counts and wire EXTSPECIES
bits are rejected before destination records or either allocator are changed.

## Verification

`docs/16bit-lifecycle-validation.json` records the latest local results and exact
ROM hashes. `docs/16bit-gameplay-validation.json` and `docs/16bit-validation.json`
retain the earlier encounter and move-ID phase evidence. GitHub Actions status
must be checked separately for the published
commit. CI covers 23 configurations: eight production combinations, five
species fixtures, eight move fixtures, one combined fixture and one playable
gameplay fixture. Normal and debug each run 166 CPU test programs. Static audits
reject byte-only symbolic move boundaries and known unsafe emulator entry
hooks; the upstream optimization check remains enabled.

Five species-only `native-test` builds define one catalog fixture at `$0201`,
`$02fd`, `$02fe`, `$02ff` or `$0300`, reusing Annihilape's art/stats with explicit
native evolution and hatchling records. They add no production Pokémon.
`tests/fixtures/wide_species.py` executes real encounter/generator, insertion,
catching, battle-identity, names/cries/pictures, PC, evolution, daycare, Pokédex,
save and allocator paths without ROM stubs.

Move-only fixtures use `$0100`, `$0101`, `$01fd`, `$01fe`, `$01ff`, `$0200`,
`$fd01` and `$feff`. A combined build uses species `$02ff` and move `$fffe`.
They reuse Tackle, except `$fd01` reuses Ember to cover a special non-contact
move above the old Struggle boundary. Production builds add no moves.
`tests/test_native_move_ids.py` covers:

- All 255 ordinary moves: eight properties, names, descriptions, structs,
  animations and contact classifications, with handles distinct from IDs.
- Root preservation under collection, primary/backup native save remapping,
  corrupt sidecar rejection and PC round trips with derived levels.
- Address and non-overlap checks for all 414 physical PC records.
- Compact/fixed readers, learnsets, TMs and synchronized random selection.
- Real move-data, priority, contact, damage and STAB routines on both sides;
  wide and ordinary aliases must produce equal damage.
- Wide egg/level inheritance, evolution parameter names, evolution-move
  duplicate detection, relearner and TM compatibility, special egg insertion,
  trainers, Battle Tower, unique wild moves and script readers. These routine
  tests observe gift insertion before its naming UI. The gameplay fixture below
  also exercises the gift UI.

`tests/test_native_link_packets.py` runs two independent emulator instances
with different species and move tables. Each normal/debug/fixture ROM executes
48 transfers across party sizes 1–6, trade/battle modes and both species input
formats. The actual packet builder, serial patch codec, validation, battle
shadow publication and post-trade persistent insertion run without ROM stubs.
Wide fixtures force collection while receiving and check independent roots.
The high-ID fixtures include serial control bytes in both halves of an ID.

The checks above execute compiled routines with synthetic game state. The
link harness transports buffers; it does not simulate cable interrupts, timing,
the complete trade animation, mail delivery or a complete linked battle.
Existing battle regressions document their presentation/unrelated-behavior
stubs. Shared opcode-checked observation helpers avoid emulator breakpoint
loops without replacing the observed battle routines.

`tests/test_scripted_native_encounters.py` checks all supported ordinary and
mechanical variant identities, cosmetic forms, script parameter advancement,
and preservation of a pending wide encounter during garbage collection.
`tests/test_native_post_battle.py` checks exact traversal of party sizes 1–6 in
both storage formats, including mixed species and all-Shuckle parties. Both
regressions fail on the preceding move-ID commit.

`tests/test_native_trainer_daycare.py` checks 335 production identities (336 in
each wide fixture), dynamic-form defaults, all 64 optional trainer record layouts,
three-member phone selection, variable nicknames and escaped moves across an
address-page boundary. It also checks 1,340 production daycare growth cases
(1,344 in each wide fixture), covering every identity, both parents, legacy/native
storage, unchanged source records and correct runtime temporary identities.
These CPU tests use synthetic WRAM records without ROM stubs.

`tests/fixtures/native_gameplay.py` boots a new game and reaches test-only bedroom
events with species `$02ff` and move `$fd01` (Ember). Joypad input drives:

- Gift and capture UIs, a complete wild battle and a two-member trainer battle
  with both wide and ordinary opponent identities.
- PC deposit/withdraw and daycare deposit/withdraw, checking species, moves,
  levels, EXP and restored PP.
- A full move-replacement prompt learning native Ember; evolution from ordinary
  Annihilape into the wide fixture, Shadow Claw learning, and return evolution.
- An Egg gift, ordinary overworld walking through all 20 hatch cycles, the full
  hatch animation and nickname prompt. Egg timers and hatch routines are unchanged.
- Two menu saves and cold Continue sessions using only cartridge SRAM/RTC.
  The final save contains a boxed wide species with native Ember; after reload,
  the PC withdrawal restores it exactly alongside the evolved and hatched party.

The final local scenario completed in 255,180 emulated frames. It uses no CPU
hooks, memory/register writes, ROM patches or emulator save states. CI preserves
screenshots, battery files and a structured checkpoint log. Test-only trainer,
learnset and bedroom content is absent from production builds; no save/link format
changes are introduced by this phase.

Example fixture builds (run `make tidy` between configurations):

```sh
make native-test NATIVE_TEST_SPECIES=513
python3 tests/fixtures/wide_species.py polishedcrystal-native-test-3.2.3.gbc
make tidy
make native_move_test=1 NATIVE_TEST_MOVE=64769
python3 tests/test_native_move_ids.py polishedcrystal-3.2.3.gbc
python3 tests/test_native_link_packets.py polishedcrystal-3.2.3.gbc
make tidy
make native-test NATIVE_TEST_SPECIES=767 native_move_test=1 NATIVE_TEST_MOVE=64769 native_gameplay_test=1
python3 -m pip install pyboy==2.7.0 Pillow==13.0.0
python3 tests/fixtures/native_gameplay.py polishedcrystal-native-test-3.2.3.gbc
```

## Remaining work before a completed migration

1. Validate protocol 7 over an actual cable or a linked emulator pair, including
   a complete trade/animation, mail delivery and linked battle.
2. Extend joypad-driven coverage to daycare breeding/egg collection, long allocator
   lifetimes across many distinct identities, additional gameplay systems and a
   full playthrough. Gift-Egg hatching is covered; it is not breeding UI coverage.
3. Add and test the intended expanded roster/move content and any corresponding
   forms/classification tables. Provide explicit save-import tooling if older
   saves must migrate.

The branch remains experimental. The high-ID fixtures establish the paths
listed above, not a complete interactive playthrough or arbitrary added content.
