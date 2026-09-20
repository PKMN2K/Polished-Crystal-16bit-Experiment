# 16-bit Species-ID Migration

This branch ports the stable Pokémon-indexing infrastructure from
`fellowship-of-the-roms/pokecrystal16` into Polished Crystal. Polished Crystal
remains the base project; pokecrystal16 is a reference implementation.

## Pinned baselines

- Polished Crystal: `f22d31a52cbbf1387d27ba63f5bf2fa959955d37`
- pokecrystal16: `e9701dce610e3b421356206992f93ed604085cd8`
- RGBDS: `1.0.3`
- Pristine Polished ROM SHA-256:
  `469d08907d0ef474d174d87d84d25e108b86ca481131b41fa291bd8aae97c29b`
- Pristine pokecrystal16 ROM SHA-256:
  `aac5c87fded6066f0abcddf5e5dda0373449f3488d143f899b0659245efaa0b2`

## Scope of the first milestone

Convert Polished Crystal's existing roster to native 16-bit species IDs without
changing content or gameplay. Do not expand move or item IDs in this milestone.
Retain a form byte only for cosmetic or runtime forms that should not be separate
species.

The milestone is complete when the unchanged roster can be created, battled,
caught, evolved, bred, deposited, withdrawn, saved, loaded, traded, and displayed
in the Pokédex without corruption. A later proof test will add one species above
`$01ff`.

## Upstream port sequence

Port the pokecrystal16 commits in conceptual order, adapting each change instead
of cherry-picking it:

1. `0fa88915` — shared WRAM structures
2. `30cd5c96` — generic 16-bit table operations
3. `ca20b7c6` — home-bank call helpers
4. `2ed4d250` — indirection tables
5. `ed116c4f` through `dcb610e8` — species conversion and persistence
6. `aa879374` — boxed species IDs (reconcile with Polished Newbox)
7. `92db8ed9` and `98de5621` — Hall of Fame and link data
8. `21968ad4` — indirect data pointers

## Polished-specific conflict map

- WRAM is split between `ram/wram0.asm` and `ram/wramx.asm`; upstream changes to
  `ram/wram.asm` must be placed and linked manually.
- Polished already has extended-species/form conversion routines. Native 16-bit
  IDs will replace mechanically distinct extended species, while cosmetic forms
  continue using form metadata.
- Polished's party, battle, daycare, Newbox, Pokédex, and save structures differ
  substantially from vanilla and must be migrated as one consistent schema.
- Existing saves will need either a versioned conversion routine or an explicit
  incompatibility boundary. This decision must be made before changing SRAM.
- Move and item expansion remain out of scope until species IDs pass regression
  testing.

## Implementation checkpoints

- [x] Build both pinned upstream baselines.
- [x] Create an isolated migration branch.
- [x] Port base table macros and allocate shared WRAM without changing the ROM.
- [x] Introduce native species constants and conversion tables.
- [ ] Convert party and battle structures.
- [ ] Convert trainer, wild, evolution, learnset, graphics, cry, and Pokédex data.
- [ ] Reconcile Newbox and SRAM persistence.
- [ ] Convert Hall of Fame and link data.
- [ ] Pass existing-roster regression tests.
- [ ] Prove a species ID above `$01ff` end to end.

## ROM0 reorganization

The pokecrystal16 `LoadIndirectPointer` and `LoadDoubleIndirectPointer` routines,
plus the Pokémon-ID home wrappers, initially overflowed Polished Crystal's ROM0.
`HandleStoneTableAction` occupied 146 ROM0 bytes and had only one caller. It now
lives in the same bank as that caller (`engine/overworld/events.asm`), freeing
enough space to link the new home routines while preserving its direct-call and
bank-restoration behavior.

## Current conversion-table checkpoint

- The Pokémon conversion table occupies one aligned WRAM page at `$d500-$d5ff`
  in WRAM bank 2.
- It supports 100 transient IDs, 30 locked IDs, 8 protected recent allocations,
  and a 16-entry cache.
- Native-index load/store, locking, and active-structure garbage collection are
  linked, but no existing gameplay structure calls them yet.
- Stored Newbox records are deliberately not scanned by garbage collection at
  this stage. Their species field will be converted to a native representation
  before the conversion table is activated in gameplay.

## Species identity and forms

Party records retain a one-byte transient species ID, as designed by
pokecrystal16. Expanding every party structure to two bytes is not part of this
architecture. Data files and lookup routines use native 16-bit species IDs; the
conversion table supplies temporary byte IDs to in-memory consumers.

Mechanically distinct variants now have explicit native constants in the compact
range immediately following `NUM_SPECIES`. Examples include `RED_GYARADOS`,
`ARMORED_MEWTWO`, `ALOLAN_RATTATA`, `HISUIAN_GROWLITHE`, and
`PALDEAN_WOOPER`. These IDs are deliberately independent of Polished Crystal's
visual-form indexes. Cosmetic forms remain in the existing form byte and do not
consume native species IDs.

Native-ID accessors now exist for base data and display names. Base data uses the
existing contiguous order, which already matches the canonical native-ID order.
Variant display names resolve through `NativeVariantIdentityTable`, allowing a native
ID such as `ALOLAN_RATTATA` to display the shared name “Rattata” without reverting
to the old species/form identity model. Existing callers have not been switched
yet; this keeps the migration checkpoint behavior-neutral.

Trainer party ROM records now store a little-endian native 16-bit species ID,
followed by the existing form byte. Mechanically distinct variants therefore
have canonical IDs in trainer data, while cosmetic and runtime forms retain
their form metadata. Until all party consumers decode transient IDs, the trainer
reader deliberately resolves the native ID back to Polished's legacy root
species/form representation before creating the opponent party. The phone-call
trainer-name lookup uses the same transitional decoding. This changes the ROM
schema without prematurely activating ambiguous transient IDs in gameplay.

Scripted `loadwildmon` records now store native 16-bit species IDs plus the
existing form and level bytes. Their interpreter resolves the native ID back to
the transitional root species/form representation before starting the battle,
so caught scripted Pokémon remain compatible with the current party and Newbox
paths. Mechanical encounters name their canonical IDs directly (for example,
`RED_GYARADOS`, `GALARIAN_MOLTRES`, and `BLOODMOON_URSALUNA`).

Packed grass, water, and swarm encounters now store a level, little-endian
native species ID, and raw form byte. The tables were widened only after their
consumers became bank-aware and the arrays were split across linker sections.
The shared reader reconstructs the transitional root species/form pair before
existing battle, Pokédex, phone, or radio code consumes it. All 3,786 logical
encounter records were verified against the preceding ROM; 165 records now name
mechanical variants with distinct native IDs while preserving their former
runtime result.

The shared grass/water lookup layer is now bank-aware in preparation for that
split. Each selected normal or swarm table records its own ROM bank in
`wWildMonDataBank`; encounter-rate loading, map lookup, battle selection,
Pokédex area scans, and phone lookups read through far-access helpers. Pokédex
table descriptors now store bank/address triples. The bank byte occupies an
existing unused WRAM slot, so every following WRAM address is unchanged. The
tables themselves have not moved or widened at this checkpoint.

The eight packed grass, water, and swarm arrays now occupy independent linker
sections instead of sharing the Wild Data code bank. Their contents remain in
the legacy three-byte-per-encounter format for this checkpoint, but they are no
longer constrained by one shared `$4000`-byte bank. The original Wild Data
section now contains only `$7b5` bytes, leaving room for the native-ID reader.
All 12,182 table bytes were preserved while the linker placed the arrays across
separate banks.

The evolution-move and combined evolution/level-up learnset pointer tables now
use native one-based IDs through the generic indirection layer. The legacy
species/form resolver remains temporarily in front of live callers, with its
zero-based result converted to the corresponding native ID. New code can call
`GetEvosAttacksPointerFromNativeIDBC` directly.

Egg-move and breeding-family pointers now use the same native-ID indirection
layer. `GetEggMovePointerFromNativeIDBC` provides the direct native API, while
current breeding, daycare, happiness, and battle calculations translate their
legacy zero-based species/form result during the transition.

Base stats now use a native-ID indirect table. The main base-data loader,
ability selection, gender-ratio lookup, Fast Ball speed check, and Pokédex search
all resolve through this interface. Legacy callers convert their existing
zero-based resolved index to a one-based native ID at the boundary.

Pokémon palettes and Pokédex footprint pointers now use native-ID indirect
tables as well. Their live callers retain the legacy species/form resolver only
as a transition boundary, then convert its result to a one-based native ID.
Palette records continue to exclude cosmetic-form identity, so Unown letters
and similar visual forms remain governed by the separate form byte.

Front pictures, back pictures, animation frames, animation scripts, idle
scripts, and animation bitmasks now use 16-bit-capable indirect tables. These
tables intentionally use a one-based visual ID: native mechanical species form
the identity, while cosmetic-form entries remain addressable as a graphics-only
overlay. Current callers resolve the species and cosmetic form at this boundary;
they do not reinterpret cosmetic forms as native species.

Picture dimensions, mini/icon graphics, mini masks, and overworld icon colors
now use that same visual-ID boundary. Picture dimensions were expanded from
packed nybbles to one byte per entry so they can be addressed through the common
indirection routines without special arithmetic.

Pokédex entry pointers now use one-based native species IDs, preserving distinct
descriptions for regional and other mechanical variants. Cry parameter records
also use the indirection layer, but remain keyed to root species because current
Polished Crystal forms share their root species' cry. A variant can receive a
separate native cry mapping later without changing party or save structures.

Body measurements, body shape, and body color now use native-ID indirection;
the Pokédex, search, and ball-weight consumers translate at their existing
species/form boundaries. Root Pokémon names also use indirect records, and the
native name accessor maps mechanical variants to the appropriate shared name.
The regional and alphabetical Pokédex orders remain curated species lists for
now: converting those entries requires the runtime native-to-transient bridge,
not merely a table-format change.
The complete 256-byte Pokémon conversion table is now stored in both the main
and backup save reservations and restored along their respective load paths.
The allocations consume previously unused padding, so legacy check values,
checksums, and Newbox addresses do not move. A format marker distinguishes new
table data from old-save padding; old saves load with a clean conversion table.
The table is garbage-collected before the primary copy is written.

Trainer parties, scripted wild encounters, and packed grass/water encounters
now use widened native-ID ROM formats. They deliberately decode back to the
transitional root species/form representation at the runtime boundary. Native
IDs must not enter party or battle structures until all downstream consumers
decode transient IDs, because compact legacy values overlap the conversion-table
slot range.

Fishing, headbutt/rock-smash, and Bug-Catching Contest records now use the same
native-ID ROM boundary. Their encounter selection and Pokédex-area scanners
share a direct-ROM decoder that restores the transitional root species/form
pair. All 227 logical records and 17 tree-table terminators were verified
against the preceding ROM; six regional/mechanical records now carry distinct
native IDs.

Roaming Pokémon now store transient species IDs backed by the persisted native
conversion table. Their existing WRAM/SRAM structs and addresses remain fixed.
Encounter and Pokédex-area consumers decode them back to the transitional
species/form representation, while initialization and respawn paths allocate
from native IDs. Loading a save without the current conversion-table marker
upgrades all three roaming records in place; existing forms are reduced to
their presentation bits after their mechanical identity is captured.

Bug-Catching Contest judging templates now store native species words in ROM
and allocate transient IDs when their temporary five-byte result records are
built. Player and NPC winner records use the same transient representation,
and name display decodes them explicitly. These records are WRAM overlays, not
save data, so this conversion does not require another save-format migration.

Hall of Fame team records retain their original 98-byte SRAM format and
addresses, but now have a parallel table of native 16-bit species identities in
previously unused Hall-of-Fame SRAM. This avoids depending on transient IDs that
may later be garbage-collected. Existing entries populate the native shadow on
first access, new entries shift both tables together, and playback overlays the
canonical identity before resolving graphics, names, and Pokédex data.

Mail's one-byte species field remains intentionally legacy. It is only a
Portrait Mail artwork hint, has no accompanying form, and is transmitted in
the fixed Gen II link-mail packet; it is not used as mechanical Pokémon
identity. Making it a transient conversion-table ID would make linked mail
depend on the sender's private runtime mapping. Battle Tower SRAM likewise
needs no species migration: it stores stable tier/set selectors whose catalog
records already contain native IDs.

Scripted gifts, gift eggs, party-species checks, and NPC trades now store native
species IDs in ROM and decode them before touching current party structures.
This covers 46 script records and all nine NPC trades. The trade records retain
their original form/gender matching behavior and all non-species fields; the
Galarian Weezing trade now carries its canonical native identity. A shared
register-level decoder is used by scripts, trades, and encounter-table readers
so extended root bits are reconstructed consistently.

Plain species-classification lists now use zero-terminated native ID words.
This covers sleeping tree Pokémon, legendary/uber classification, Fury Strikes
animation users, and the Withdraw/Harden/Milk Drink animation selectors. The
shared comparator converts the transitional runtime species/form pair to its
canonical native identity before scanning and preserves cosmetic-form wildcard
behavior. All 79 entries were verified, including six IDs above `$00ff`.

Hidden-grotto and special Egg records now store native species ID words followed
by their unchanged raw form byte. Their readers decode back to the transitional
runtime representation before writing save-backed grotto contents or party/box
records, so both persistent layouts remain compatible. This covers all 88
hidden-grotto choices, ten Odd Eggs, and the Mystri Egg.

The shared Battle Tower and Battle Factory set catalog now uses native species
ID words plus unchanged form/gender bytes. Selected opponent and rental sets are
decoded before entering the existing party and facility SRAM structures. Tier
terminators are full zero words, avoiding collisions with future native IDs
whose low byte is `$ff`.

The regional and alphabetical Pokédex order tables now store native ID words.
List iteration decodes each entry only at the existing UI boundary, and regional
forms continue to inherit their root species' curated list position. Johto-to-
National number conversion and the general `GetPokedexNumber` search compare
native words rather than packed extended-species bits.

Mechanical variants now have an explicit identity table containing their native
ID, root species, and presentation form. Native lookup no longer treats a visual
table offset as the species identity. The legacy species/form sequence remains
only as `VariantVisualSpeciesAndFormTable`, preserving cosmetic and mechanical
form cycling, Pokédex flags, and graphics ordering during the transition.
The resolver checks species-specific forms before broad regional form values, so
Paldean Tauros's Blaze/Aqua breeds and Bloodmoon Ursaluna cannot be intercepted
by numerically identical Alolan/Galarian form constants.

Pokédex flag access now resolves mechanical forms through their explicit native
species IDs and cosmetic overlays through the visual-form table. The 394-bit
seen and caught arrays retain their existing physical ordering, with a defined
compatibility offset for native variants, so current saves do not lose Pokédex
progress. Flag capacity is now expressed as native species plus cosmetic forms
rather than the graphics-oriented unique-form count.

The transition now has explicit domain-boundary helpers. ROM data can be
encoded with `GetTransientIDFromLegacySpeciesAndForm`; unchanged party and
battle structures can be decoded with `GetNativeSpeciesIDFromTransientID` or
`GetNativeSpeciesIndexFromTransientID`. These APIs are intentionally inactive
until all persistent structure consumers and old-save upgrade handling can be
switched atomically.

The party/daycare activation audit currently identifies 122 direct references
to party or opponent-party species fields. Generic structure primitives now
store a native ID as a transient byte, decode a transient species plus its form
at legacy boundaries, and migrate a legacy species/form record in place.
Roaming Pokémon use these shared primitives as the first active proof. Party,
opponent-party, daycare, contest-party, and battle records remain legacy until
their complete consumer sweep and old-save migration can switch together.

The saved Pokémon-data block now reserves a two-byte format marker inside its
existing seven padding bytes; no following WRAM or save address moves. The
central party-to-temporary-Pokémon loader accepts either format. With the marker
unset it follows the unchanged legacy path. With the marker set it resolves the
source structure's transient ID to native identity before base-data access, then
provides a decoded legacy-compatible temporary record for consumers that have
not yet migrated. The marker remains unset until the party/daycare consumer
sweep and old-save conversion can activate the format atomically.

Party species searches now read records through a shared dual-format structure
decoder. Scripted ownership checks preserve their existing form-wildcard rules
in both formats, including trainer-ID-qualified searches. Battle Tower entry
validation uses the same decoder and compares the resulting canonical identity
against its native-ID banned list; it no longer interprets that widened word
list as the former packed species/form table.

Party-menu species access now uses the dual-format decoder for TM/HM
compatibility, evolution-item eligibility, gender display setup, and final menu
selection. A shared loader publishes the decoded transitional species/form
globals and also returns the pair for evolution and learnset lookup. This
removes the remaining raw species/form reads from the party menu while keeping
its legacy-format behavior unchanged.

Evolution and move-management readers now accept either party storage format.
This covers after-battle and in-battle evolution checks, party-composition
evolution requirements, evolution-item and remembered-move data, and Pikachu's
move-dependent form updates. Reloading an evolved battler decodes its source
identity before populating the transitional battle structure. The final
evolution write-back now honors the party-format marker: all evolution work is
performed through the legacy-compatible temporary record, then its completed
identity is converted immediately before the record is copied to the party.
Legacy saves retain their original byte representation. The shared conversion
primitive also preserves the complete form byte, preventing Egg and gender
metadata loss when persistent party/daycare migration is activated later.

Party insertion from `wTempMon` now converts the completed destination record
to the selected persistent Pokémon-data format. This covers scripted gifts and
daycare-created eggs while leaving their legacy temporary records available to
the existing Pokédex and happiness code. Bug-Catching Contest insertion uses
the same rule after nickname and caught-data processing. Egg hatching does not
rewrite species identity, so an already stored transient ID remains unchanged.
Opponent-party construction and ordinary wild catches remain legacy until the
battle/opponent-party consumer sweep can be activated atomically.

Daycare records now have shared dual-format decoders. Deposit and retrieval
continue copying records without changing their representation, while breeding
compatibility, base-data loading, retrieval stat recalculation, overworld
daycare icons, and daycare cries resolve the stored identity first. This keeps
legacy saves unchanged and makes the same paths safe once the persistent party
and daycare marker selects transient IDs.

Egg generation now decodes both parents before Ditto, gender, mother, species,
and inherited-form decisions. Parent records remain untouched, and the child is
still constructed as a legacy-compatible `wTempMon`; the shared party insertion
boundary converts that completed egg only when transient persistent storage is
active. Same-species random inheritance compares decoded species and mechanical
form identity, so transient slot numbers can never be mistaken for species.

Egg-cycle processing now decodes each non-Egg party member before checking
Flame Body or Magma Armor. Hatching continues to operate through the decoded
legacy-compatible temporary record while leaving the stored transient identity
in place; post-hatch stat recalculation now decodes that party record directly.
First-party Egg and happiness name helpers also use the dual-format decoder.

Remaining non-battle maintenance paths now decode party or daycare identity
before species-dependent work. This includes Mirror Herb egg-move validation,
field-move eligibility, Surfing Pikachu detection, Shuckle's Berry Juice event,
the move deleter's Pikachu form reset, general stat recalculation, and NPC-trade
stat setup. The move deleter also now supplies the required form offset to the
shared decoder.

Party-menu palette and icon loaders now decode persistent species identity
before selecting native graphical records. Cosmetic forms still come from the
separate form byte, shiny/DV color variation is unchanged, and Egg records
continue using the dedicated Egg icon and palette. Fly-menu icon and palette
paths use the same boundary instead of treating a transient slot as a species.

Hall of Fame capture now decodes party records before writing the legacy Hall
of Fame payload. The existing native-ID shadow table therefore receives the
correct canonical identity even after party storage switches to transient IDs.
The legacy payload layout and addresses remain unchanged, and gender and other
personality metadata sharing the form byte are preserved during serialization.

Gen 2 link transmission now serializes party records through a dual-format
identity boundary instead of copying transient species bytes directly onto the
wire. Packet sizes, offsets, patch-list behavior, and the legacy species/form
layout are unchanged. Egg, gender, personality, moves, stats, OT names, and
nicknames remain byte-preserved. Received opponent/link parties intentionally
remain legacy until the opponent-party and battle consumer sweep lands.

Link-trade menus now distinguish local transient party records from received
legacy opponent records. Local species names, trade confirmation text, trade
animation metadata, and the outgoing trade identity buffer decode through the
persistent-format boundary. The received side retains its established legacy
interpretation, and incoming Pokémon still convert only when inserted into the
player's party.

Battle Tower team selection now converts copied player records from the
persistent party format into the Tower's transitional legacy OT-party work
area. Species/form clause checks and generated trainer teams therefore retain
their existing representation. The shared Tower level/stat routine decodes
player records when necessary while continuing to read opponent records as
legacy. Player teams copied back from reordered Tower selections or rental OT
workspaces are converted to the selected persistent format after the copy, with
no Tower SRAM or trainer-data layout changes.

Overworld and special-event identity readers now decode persistent party
records before species-dependent work. This covers the Ho-Oh chamber type
check, Professor Elm's evolution calls, script-driven Poképics, Wonder Trade
restrictions, NPC-trade metadata, the Judge Machine, and poison-step ability
checks. Egg flags and structural offsets remain direct byte reads because they
are representation-independent.

Player battle entry now resolves the source party record before publishing
legacy battle identity. Only the player side uses the persistent-format decoder;
trainer/link opponent parties retain their legacy representation. The decoded
form is merged into the copied battle form without changing gender or Egg bits,
and both temporary battle identity and base-data globals read that result.
Player HUD base-data access and experience-growth lookup use the same existing
party decoder, preserving the experience recipient pointer across the call.
The focused CPU test in `tests/test_battle_party_identity.py` exercises the
compiled decoder and send-in boundary. Persistent-format activation, opponent
conversion, catch/write-back auditing, and Newbox migration are still pending.
