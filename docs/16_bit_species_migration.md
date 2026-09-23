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

The shared temporary-Pokémon loader now checks both the persistent format marker
and source record type. Opponent/link records stay legacy even when the player
format marker is set, so catch/item and summary consumers do not mistake an
opponent species byte for a conversion-table slot. Decoding a player record
merges only species/form bits into `wTempMonForm`, preserving the gender and Egg
flags copied from the source. The helper lives beside the existing format
helpers because the original loader's ROM bank has little remaining space.
`tests/test_tempmon_identity.py` exercises the complete copy and real base-data
lookup with valid, absent, and partial format markers. Catch insertion and
conversion-table garbage-collection representation auditing remain pending.

Conversion-table collection now follows the active representation boundaries:
player/daycare slots are scanned only when the persistent marker is valid;
roamers and four contest winner/work records remain transient roots. All six
player slots are scanned because the contest temporarily hides five by changing
only the party count. Legacy opponent, battle, temporary, contest-catch and Odd
Egg identities, and legacy species globals, are not slot references. Locks and
recent allocations remain protected. Contest result memory overlaps unrelated
scratch buffers, so this checkpoint conservatively retains those four values;
phase-specific suppression is deferred.

Ordinary catches now copy the legacy wild opponent through a shared destination
boundary and convert the player record only after the full structure is copied.
Opponent bytes and the destination's non-identity data remain unchanged. The
existing nickname, caught-data and ball-effect processing follows the copy.
Full-party PC delivery remains on the legacy Newbox path. The focused collection
and catch CPU suite forces table exhaustion and checks live-root preservation,
slot reclamation and copied identities in both formats; it does not simulate
the entire interactive capture sequence or enable persistent-format activation.

Lead field-ability lookup now resolves the persistent player identity before
using the existing personality/form-based ability lookup. It preserves the
current species/form globals and caller registers. Synchronize's nature
selection now uses that same lead helper, including its Egg exclusion, as the
other field-ability paths do.

`TryAddMonToParty` now converts a generated player record only after its legacy
construction and stat calculation finish. Generated opponent records, including
wild/trainer parties and gift staging workspaces, remain legacy. Its successful
return still sets carry after conversion. The lead helper resides with the
format helpers, with a home-bank entry point, to avoid increasing ROM0 usage.
The new CPU suite checks lead ability slots/options and executes complete
player/opponent generation for each of the six target slots. Trade dialog,
nature distribution, full gameplay and save-upgrade validation remain pending.

Species-dependent held-item checks now use shared user/opponent party identity
helpers. Player records decode through the persistent marker; opponent records
stay legacy. Eviolite, non-faithful Metal Powder, and essential-item protection
therefore compare canonical legacy-compatible species/form pairs instead of
transient slot numbers. Faithful Metal Powder continues checking the current
legacy battle identity, preserving its different Transform behavior.

Post-battle ability processing decodes each player's identity before checking
Natural Cure, Pickup or Honey Gather. Egg filtering remains representation-
independent. The focused suite executes held-item checks and Natural Cure across
both formats, both sides and all six slots. It also verifies the unchanged
player/opponent HP/status write-back routines copy only their intended fields
and leave species/form and all other party bytes intact. Future Sight's delayed
attacker and gender-dependent battle identity reads remain to be migrated;
item acquisition distributions and full battles have not been validated.


## PC storage, save envelope and remaining activation boundary

Newbox keeps its existing record size and pointer/allocation protocol. A stored
species byte of zero tags a native word in `SAVEMON_EXTRA + 1` and `+ 2`; the
first extra byte retains hypertraining. Zero was not a valid stored legacy
species (`$0100` is unused). Encoding computes the native ID before the record
checksum. Decoding checks the checksum before interpreting the tag, validates
the native range and unused root slot, and sends invalid records through the
existing Bad Egg path. Old nonzero species records retain the legacy decoder.
Rewritten entries adopt the new format without scanning all boxes up front.

Party/temp transfers respect direction and source: the player party follows
its format marker, while temp and opponent parties remain legacy. Mechanical
form changes, including adding/removing Mewtwo armor, update the transient ID.
Variant decoding must preserve HL because callers use it as the struct pointer;
the root lookup formerly overwrote it with the resolved root word.

The conversion table is outside `sGameData`, so the existing save checksum did
not protect it. The new `$16be` envelope adds a table checksum in unused padding
and publishes magic only after the table and checksum are copied. A second
version word in unused, checksummed Pokémon data prevents a torn table header
from masquerading as an older save. Primary and backup integrity checks run
before loading their respective records; failed primary checks select backup.
The `$16bd` legacy table remains loadable for legacy player records. A transient
player marker without a protected table is rejected rather than guessed at.

Save format 11 accepts version 10 on read. Pokémon-data writers stamp version
11 before updating records, ensuring older ROMs stop at their version check.
Existing struct, main-checksum and Newbox addresses remain fixed. This supports
forward migration; new saves cannot be used with older ROMs.

`MigrateLegacyPlayerPokemonData` is RAM-only and not automatically enabled. It
converts six party records (including contest-hidden slots) and two daycare
records, protects intermediate IDs with dedicated locks, publishes the format
marker last, and clears its locks. It is idempotent. CPU tests force collection
with an occupied 100-slot table and verify the resulting records and lock state.

The deferred Future Sight user, gender-dependent battle comparisons, Love Ball
root comparison, Surf identity, stat-wing naming and move-learning form offset
now use the corresponding decoded identity boundary. Native roaming storage
also now passes the native BC word to the allocator rather than the destination
HL address. Tests include high native words for storage, which is deliberately
not described as a playable high-ID proof.

The remaining architectural limit is the legacy runtime bridge: a byte and bit
5 of the form can encode only nine root-species bits. The current native catalog
ends at `$0151`. Full activation still needs native-aware opponent/battle
consumers, an actual species above `$01ff` with complete data, integration of the
RAM conversion into load/new-game paths, and full gameplay/save-recovery tests.


## Direct native party base-data lookup

The player HUD and experience recipient previously decoded persistent identity
into legacy globals and then reconstructed a native ID for `GetBaseData`.
They now retain legacy-global publication for surrounding consumers but obtain
base data directly through `GetBaseDataFromPokemonDataStruct`.

The shared native reader follows the player/daycare format marker, preserves
HL/DE, and neither allocates IDs nor changes globals. The base-data wrapper also
preserves BC and returns carry without touching the buffer for an empty identity.
Its table lookup uses the stored native word even if the legacy form byte would
resolve to a different record. This removes a round-trip at these two lookup
sites; other battle, opponent, naming and presentation consumers remain pending.

`tests/test_native_party_base_data.py` adds 512 CPU cases. It compares the full
base-data buffer against the compiled ROM records, tests all party/daycare slots
and marker states, checks metadata/register/global/table preservation, and tests
empty records. Values above `$01ff` exercise only the native identity reader;
they are not a substitute for the outstanding playable high-ID proof.


## Native base data for the original attacker

The external-user branch of Future Sight STAB now calls
`GetBaseDataFromTrueUserParty` after publishing the existing legacy globals.
The helper uses `TrueUserPartyAttr` to select the original attacker and reads
player identity through the format-aware native reader. Enemy party records
use `GetNativeSpeciesIDFromLegacyPokemonDataStruct` explicitly, so a transient
player marker cannot reinterpret an opponent's species byte as a table slot.
The helper preserves the move-type register and other caller registers/globals.
Empty identities share the existing no-write/carry behavior.

`tests/test_native_deferred_base_data.py` checks 1,200 lookup cases across both
sides, six slots, deferred/current users, marker variants, regional/extended
identities and metadata. It verifies exact compiled base data, source/global/
table preservation and empty-record behavior. Full damage execution, active
battle representation migration and a playable species above `$01ff` are still
outside this checkpoint.


## Native active-battler identity and first consumer

The battle runtime now keeps a direct native word for each active battler in
`wBattleMonNativeSpecies` and `wEnemyMonNativeSpecies`. These words occupy
bytes that were already reserved as battle scratch, so this change does not
shift neighboring WRAM addresses. They are native species IDs, not conversion-
table slots, and therefore do not need to become collection roots.

`SendInUserPkmn` stores the native identity before decoding the existing legacy
battle species/form fields. Player send-ins resolve through the persistent
format marker, while opponent records still resolve through the explicit legacy
reader. This preserves the established battle struct representation while
creating a 16-bit source for consumers that migrate one at a time.

The first consumer is the send-in base-data lookup.
`GetBaseDataFromActiveBattleNativeSpecies` selects the player or enemy shadow
with `hBattleTurn` and loads the native base-data record directly. Existing
legacy globals remain published for unconverted code. Empty shadows return
carry and leave the base-data buffer untouched.

The legacy reader also now treats species byte `$00` plus the extended-species
form bit as species #256 rather than an empty record. A zero species byte is
empty only when no extended-species identity bit is present.

GitHub Actions run #12 passes all normal, faithful, VC and debug combinations.
`tests/test_active_battle_native_base_data.py` adds eight focused PyBoy cases,
and the existing send-in regression test now hooks the new native lookup
boundary. Those PyBoy tests are committed but were not executed on this head in
this chat; the last executed full CPU checkpoint remains 5,979 cases per
normal/debug ROM.


## Second active-battle consumer: Safari catch-rate reset

When Safari bait or rock effects expire, the engine must restore the wild
opponent's normal catch rate from its base data. That path previously rebuilt
base data from `wEnemyMonSpecies` and `wEnemyMonForm`.

`ResetSafariCatchRateFromEnemyNativeSpecies` now preserves the old publication
of those legacy fields into `wCurSpecies` and `wCurForm`, but performs the
actual base-data lookup through `wEnemyMonNativeSpecies`. The new
`GetBaseDataFromEnemyBattleNativeSpecies` helper is side-specific and does not
depend on the current `hBattleTurn` value. If the native shadow is empty, it
returns carry and the existing catch rate is left untouched.

This is intentionally narrower than replacing the enemy battle structure. The
legacy species/form bytes remain available to all unconverted consumers; the
Safari catch-rate source alone is now native.

`tests/test_safari_native_catch_rate.py` adds four focused CPU cases covering
an ordinary species, species #256, a native regional/mechanical identity and an
empty shadow. Conflicting legacy/native fixtures prove the catch-rate record is
selected from the native word while the legacy-global side effects remain.
These new PyBoy cases are committed but were not run in this chat. GitHub
Actions run #17 passes all eight configured ROM build variants.


## Third active-battle consumer: Heavy Ball weight lookup

Heavy Ball previously rebuilt the enemy identity from `wEnemyMonSpecies` and
`wEnemyMonForm` before looking up body weight. That made its weight threshold
logic depend on the transitional byte/form representation even though the active
enemy now has a direct native identity shadow.

`HeavyBallMultiplier` now reads `wEnemyMonNativeSpecies` and calls
`GetNativeSpeciesWeight`, which uses the one-based native ID directly with
`GetBodyDataPointerFromNativeIDBC`. The existing weight thresholds and catch-
rate adjustments are unchanged. A zero native shadow returns without changing
the current catch rate instead of falling back to a stale legacy identity.

`tests/test_heavy_ball_native_weight.py` covers light, medium and heavy weight
bands, species #256, Alolan Raichu, deliberately conflicting legacy identity and
an empty native shadow. GitHub Actions run #21 passed all eight configured ROM
build variants for the Heavy Ball code head.


## Fourth active-battle consumer: ability reset

The active ability reset path still passed the byte-sized battle species into
the legacy `GetAbility` routine. That meant a mechanically distinct native
identity could still select its ability table through reconstructed legacy
species/form state.

`GetAbilityFromNativeIDBC` now accepts a one-based native species ID directly.
It keeps the existing personality byte as the ability-slot selector, loads the
ability list from the native base-data record and returns no active ability for
native ID zero. `ResetPlayerAbility` and `ResetEnemyAbility` read their
respective native battle shadows and use this helper.

`tests/test_active_battle_native_ability.py` adds focused cases for both battle
sides, ordinary species, species #256, Alolan Raichu, conflicting legacy
species bytes and empty native shadows. The battle structs themselves remain
legacy-compatible; only this consumer's identity source has moved to the native
word.


## Transform synchronization for active native identity

The direct native battle shadows originally represented the identity published
at send-in. That is insufficient for consumers which intentionally inspect the
battler's current species after Transform, because Transform already replaces
the legacy active species/form fields.

`CopyTransformNativeIdentity` now mirrors that operation for the native word.
When the player transforms, `wEnemyMonNativeSpecies` is copied into
`wBattleMonNativeSpecies`; when the enemy transforms, the player native word
is copied into `wEnemyMonNativeSpecies`. The source shadow is unchanged, and
a zero source remains zero.

This does not alter the original party record or the existing transformed
substatus. It only keeps the current active-battle native identity parallel to
the current legacy battle representation. This is a prerequisite for migrating
current-species consumers such as animation-variation and transformed-species
checks without incorrectly using the send-in identity.

`tests/test_transform_native_identity.py` covers both transform directions,
ordinary species, species #256, Alolan Raichu and a zero native shadow.


## Native current-species lists for battle animation substitution

`CheckBattleAnimSubstitution` uses curated species lists to swap a move's
battle animation for particular users. Those lists are already stored as native
16-bit IDs, but the old path first rebuilt a native ID from the user's legacy
battle species/form bytes before comparing it.

`IsActiveBattleNativeSpeciesInList` now selects the current move user's
`wBattleMonNativeSpecies` or `wEnemyMonNativeSpecies` shadow with
`hBattleTurn` and compares that word directly against the native list. This
removes a native→legacy→native round-trip from the active battle path and keeps
the animation check aligned with transformed identity because the preceding
Transform checkpoint synchronizes the active native shadow.

The helper preserves DE so the caller can keep its candidate replacement
animation ID there. An empty native shadow never matches. The Fresh Snack/Milk
Drink, Fury Strikes/Fury Attack and Defense Curl variation checks now use this
path.

`tests/test_active_native_species_list.py` covers both active sides, ordinary
and extended IDs, Alolan Raichu, deliberate legacy/native disagreement,
wrong-side selection guards and empty active native shadows.


## Faithful Metal Powder current-species check

Polished Crystal has two intentional Metal Powder behaviors. In non-faithful
mode, the effect follows Ditto's true party species and continues to apply after
Ditto transforms. That path remains party-record based and unchanged.

In faithful mode, the rule instead asks whether the opponent's current battle
species is Ditto. That check previously read the legacy active species byte and
extended-species form bit. `IsOpponentActiveNativeSpeciesBC` now selects the
opponent's direct native shadow using `hBattleTurn` and compares the complete
16-bit native ID. Because Transform synchronizes the active native shadows, a
non-Ditto transformed into Ditto matches, while a Ditto transformed into
something else does not.

This helper is intentionally exact rather than root-species based: a different
high-byte native identity with the same low byte does not compare equal.
`tests/test_opponent_native_species_match.py` covers both battle turns,
full-word mismatch, wrong-side guards, conflicting legacy bytes and empty
native shadows.


## Native species-restricted held-item checks

`UserValidBattleItem` controls species-restricted held-item effects such as
Light Ball, Leek, Lucky Punch, Quick Powder and Thick Club. The old path read
the current battle species byte and form, then matched a three-byte table record
containing item + legacy species/form.

The table is now `ValidBattleItemTableNative`, with the same three-byte record
width but a simpler identity representation: item byte + 16-bit native root
species ID. The caller selects the current user's `wBattleMonNativeSpecies` or
`wEnemyMonNativeSpecies` shadow from `hBattleTurn`, resolves that identity
through `GetRootSpeciesFromNativeIDBC`, and compares the resulting root word.

This remains a current-battle-species rule, not an original-party-species rule.
Transform therefore changes which species-restricted item effects apply, just as
the legacy active species/form fields did; the Transform synchronization
checkpoint ensures the native shadow follows that behavior. Resolving the
native identity to its root species also preserves the old zero-form wildcard:
regional/mechanical forms inherit an item effect attached to their root species,
while unrelated roots do not.

`tests/test_native_species_battle_items.py` covers both active sides, a real
mechanical-variant/root match, legacy/native disagreement, unrelated roots,
empty native shadows and wrong-item guards.


## Native move-animation cry checkpoint

The move-animation `BattleAnimCmd_Cry` now reads the current native identity of
its acting battler from the appropriate active-battle shadow. This removes the
legacy species/form lookup for that command without changing the existing
four script parameters, cry-track masks, pitch/length adjustments, asynchronous
playback, or WRAM restoration. Mechanical variants use their root species'
cry, and empty/egg/reserved identities remain silent. The focused PyBoy test
is `tests/test_native_move_animation_cry.py`; it is committed but was not
executed in the chat that introduced this checkpoint. This is still an
incremental battle bridge, not a persistent-format activation.


## Native Transform-animation picture

The active-battle Transform command copies the opposing native species word
into the acting battler's current native shadow before playing its animation.
`BattleAnimCmd_Transform` now uses the existing side-specific
`PreparePlayerBattlePictureIdentity` / `PrepareEnemyBattlePictureIdentity`
compatibility bridge to select the rendered back/front picture. Mechanical
variants derive their presentation form from their native identity; cosmetic
forms are retained only when they resolve to the same native species.
Legacy temporary species bytes remain available to unconverted callers but
no longer select Transform's picture. The command keeps the original tile
destination and WRAM-bank restoration, restores `wCurPartySpecies` as before,
and retains `wCurForm` for the transformed picture on successful rendering.
Empty or reserved native identities do not invoke a renderer. Focused PyBoy
coverage resides in `tests/test_transform_animation_native_picture.py`; it
stubs the front/back renderer and cannot prove on-screen pixel correctness.


## Retired Beat Up animation identity boundary

`BattleAnimCmd_BeatUp` and its `anim_beatup` macro are retained in the
animation command dispatch, but the move is absent from the current move
constants and animation pointer table. The former `BattleAnim_BeatUp` script
is commented out as removed. There is therefore no live move-animation
caller to migrate at this checkpoint.

If Beat Up is reintroduced, its former animation command cannot safely use
the active battler's native shadow: the pictured participant may be a
different member of the attacker's party. The retained command currently
treats the one-byte `wBattleAnimParam` as a legacy species number and reads
the active battle mon's form. A future implementation must define a producer
for the actual contributing party member's full native 16-bit identity and
form, and a renderer-compatible bridge for that selected member. It must
preserve the enemy-front/player-back tile destinations and restore the
temporary renderer globals. No runtime or persistent-record change was
made as part of this audit.


## Native Silph Scope ghost reveal

The initial unrevealed ghost remains the special `GhostFrontpic` while
`BATTLETYPE_GHOST` is active. When the player has the Silph Scope,
`BattleIntro` invokes `RevealGhostEnemyFrontpic` to publish the active
enemy's renderer-compatible species/form from `wEnemyMonNativeSpecies`
through `PrepareEnemyBattlePictureIdentity`; it then draws the revealed
front picture to the original `vTiles0` transition tiles. The ghost-to-Pokémon
animation still runs at its original point.

After the animation, `RecordRevealedGhostEnemySeen` resolves the native
shadow again before calling `SetSeenMon`. The second resolution avoids
using renderer globals modified during the animation and ensures the Dex
is given the revealed appearance's compatible species/form rather than a
stale pre-battle species with a separate legacy enemy-form byte. Empty and
reserved native IDs skip picture rendering and seen registration. This is
a transient rendering/Dex boundary change, not a persistent party save
format change. `tests/test_native_ghost_reveal_picture.py` stubs renderer
and Dex calls to test inputs, routing and state; full ghost-battle visuals
still require in-game validation.


## Native enemy send-out temporary-record base data

The selected trainer opponent's canonical native word is published to
`wEnemyMonNativeSpecies` by `SendInUserPkmn` before the send-out picture
path runs. `Function_SetEnemyPkmnAndSendOutAnimation` now calls the
send-out-specific `CopyEnemyBattlePkmnToTempMon` helper instead of redundantly
calling legacy `GetBaseData` before the general temporary-record copier.

The new helper retains the opponent's legacy species/form and copies the
complete original opponent party record into `wTempMon` through the shared
temporary-record body. For a populated native shadow, it obtains base data
directly through `GetBaseDataFromEnemyBattleNativeSpecies` rather than
reconstructing a native ID from the legacy byte/form pair. With an empty
shadow, it takes the existing legacy `GetBaseData` fallback. Neither the
general temporary-record copier nor any persistent format is changed.

The subsequent `GetMonFrontpic` already resolves the active enemy's
native battle identity for rendering. Its lower-level sprite preparation
still has an internal legacy base-data lookup; that broader renderer change
is separate. `tests/test_native_enemy_sendout_tempmon.py` checks byte-exact
temporary records and native base data and stubs the legacy loader to
enforce the new helper's normal-path boundary. Real send-out animations
and pixel output are not exercised by that CPU test.

The initial implementation placed the send-out helper in the already-full
bank14 and exceeded its $4000-byte section limit by 11 bytes. The validated
implementation lives in `engine/16/native_species.asm` in the existing
`16-bit ID stuff` ROM section and far-calls the legacy
`GetPkmnSpecies` / `GetPkmnForm` readers and
`_CopyPkmnToTempMon.copy_data` copy entry. This relocation does not alter
the shared temporary-record layout. GitHub Actions run #35895629364
compiled all eight ROM configurations and passed 72 focused enemy send-out
CPU cases on each normal/debug ROM. The existing focused cry, Transform
picture and ghost-reveal regressions also passed in that run.


## Shared front-picture base-data lookup audit

`engine/gfx/load_pics.asm:_PrepareFrontpic` is a shared renderer used by
`GetFrontpic`, `PrepareFrontpic` and `PrepareAnimatedFrontpic`. It calls
legacy `GetBaseData` as a side effect before obtaining size and pixels.
The size itself comes from `GetPicSize`, which resolves
`wCurSpecies`/`wCurForm` into `PokemonPicSizes`; the image pointer is
resolved independently through `GetCosmeticSpeciesAndFormIndex` and
`PokemonPicPointers`. Neither lookup directly uses `wCurBaseData`.

The renderer cannot simply be changed to read `wEnemyMonNativeSpecies`
unconditionally. General picture placement (`PrepMonFrontpic`), the trade
front picture (`GetTrademonFrontpic`), and hatch egg/hatchling pictures
(`GetEggFrontpic`/`GetHatchlingFrontpic`) also invoke these shared
routines and have their own source identities. Their legacy base-data
side effects may matter to the surrounding flow.

In battle, `DropEnemySub` already calls
`PrepareEnemyBattlePictureIdentity` and
`GetBaseDataFromEnemyBattleNativeSpecies` before
`PrepareAnimatedFrontpic`. The shared renderer's subsequent
`GetBaseData` replaces that exact native base-data buffer through a
legacy representation round-trip. During front-picture animation,
`GetFrontpicDims` in `engine/gfx/pic_animation.asm` repeats a legacy
`GetBaseData` before `GetPicSize`.

A future implementation should expose an **explicit battle-only** front
picture/dimension contract: preserve the active enemy's native identity for
base-data side effects while retaining the existing shared renderer
behavior for menu, trade and hatch calls. Do not infer battle context
from `wCurPartySpecies`, `hBattleTurn` or the global `wBattleMode`
alone, since shared picture calls may run in other contexts. Both
rendering and animation-size paths need coverage. The existing bank14
section is at its size limit, so avoid adding uncompensated code there.
This checkpoint is documentation-only; no live renderer behavior changed.


## Battle-only native enemy front-picture preparation

The battle enemy's non-ghost sprite path now calls
`PrepareNativeEnemyBattleAnimatedFrontpic`, in the native species ROM section,
instead of the general `PrepareAnimatedFrontpic`. This explicit battle entry
resolves `wEnemyMonNativeSpecies` and the enemy's supported presentation form,
loads exact native base data, and preserves the original `vTiles2` destination
and `vTiles3` animated-tile setup. Ghost-frontpic decompression remains a
separate, unchanged branch.

`_GetNativeFrontpic` in the shared graphics bank reuses the existing
`_PrepareFrontpic` size/picture-pointer/decompression body but enters after
the generic `GetBaseData` call. `_GetFrontpic` and all public generic
front-picture functions still take the original legacy base-data side-effect
path. The battle-only entry therefore does not replace native base data
with reconstructed legacy data during front-picture preparation, and menu,
trade, hatch and other non-battle front pictures retain their existing
behavior. The extra graphics-bank entry is small because bank14 is nearly
full; the larger battle wrapper lives outside that bank.

`tests/test_native_enemy_frontpic_renderer.py` exercises the real picture
preparation with only low-level decompression/tile-copy routines stubbed.
It checks the native base-data buffer and presentation identity at
preparation and animated-tile boundaries and verifies that the generic
renderer still invokes `GetBaseData`. It does not verify displayed pixels.

**Still pending:** `GetFrontpicDims` in the shared picture-animation setup
independently calls legacy `GetBaseData`. That second call may replace
the native buffer when an enemy front picture is subsequently animated;
the next scoped migration must address the battle animation-dimension
boundary without changing non-battle animations. No save-format or party
layout change was made by this front-picture preparation step.
