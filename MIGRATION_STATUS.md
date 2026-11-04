# DanielOlivaw 16-bit migration status

**Status: incomplete engine port; native species link-packet checkpoint.**

Branch: `migration/danielolivaw-16bit` in
`PKMN2K/Polished-Crystal-16bit-Experiment`.

## Sources

- Polished Crystal source: `Rangi42/polishedcrystal@bd535b89f8e1337151b715f76a235296c26a60c7`.
- Requested donor: `DanielOlivaw/pokecrystal16@ace283e879e8dd683fc0ccc26e8b85e70dc72313`.
- Compatible Polished adapters reused from `migration/battle-party-readers@f2089e9e6580c0113217c13db4bdee4ec39db28c`.
- Toolchain: RGBDS 1.0.4, PyBoy 2.7.0, Python 3.12.

The donor shares the original aaaaaa123456789/pokecrystal16 index architecture.
The conversion-table macros, bank-safe home wrappers, WRAM table allocation
and indirect pointer routines were checked against the requested donor.
Existing adapters implement that architecture with current RGBDS syntax and
Polished-specific party, form, Newbox and save layouts. The donor's move table,
additional roster and gameplay content were not imported.
Source commits and SHA-256 hashes of donor reference files are recorded in
`docs/16bit-sources.json`.

## Integrated in this branch

- Existing-roster native species identities with separate mechanical variants,
  transient byte IDs, allocation, locks and garbage collection.
- Widened trainer/wild/event species records and native table indirection for
  stats, names, evolution/learnset data, graphics and Pokédex data.
- Native player-party/daycare storage, direct battle identity shadows, and
  Polished's native Newbox storage and conversion-table save integrity envelope.
- Fresh games initialize native player storage. Opponent and temporary records
  retain their byte/form layout, with explicitly tagged conversion-table handles
  for wide roots. Native IDs are decoded before names, cries, data and picture
  lookups; wide identities are not truncated to nine bits.
- Conversion-table collection protects live wide handles in opponent/link-party
  workspaces, battle/temporary records, trade-animation records and rendering
  globals.
- Link protocol 6 carries native species words and separate form/egg/gender
  metadata. The receiver validates identities before allocating its own runtime
  aliases. Packet lengths and serial escaping remain unchanged; older link
  protocols are rejected for both trading and battles.
- Evolution targets and hatchling records store a native word plus a separate
  form. Evolution-list readers skip whole records, so an ID byte of `$ff` is
  not mistaken for a terminator. Party-species evolution parameters use words.
- Pokédex lists store native root words plus separate form/metadata. List
  construction and searches do not retain one conversion slot per species.
- Daycare compatibility preserves the first parent's gender across the second
  decoder. Form/ball inheritance preserves its selected parent-field pointer.
- Current upstream's single grass encounter rate, new Battle Tower Bloodmoon
  sets, current map/assets and WRAM layout are retained.
- Save version 12 is required. Version 10 and both incompatible meanings of
  version 11 are rejected. No automatic old-save upgrade is claimed.
- Fixed inherited Metal Powder behavior: non-Ditto Pokémon no longer get the
  boost, and faithful builds preserve the defense value during species matching.
- Fixed native Hall of Fame restoration: keep the full species word while
  locating the form byte, and preserve gender/personality metadata. The
  regression covers all mechanical variants, cosmetic forms, ten stored
  teams, history rotation and party-to-save/load with Eggs excluded.
- Reconciled imported assembly with the upstream optimization check while
  retaining the native decoders' register and bank-switching contracts.
- A single bounded test runner, thirteen-config CI, and shared opcode-checked hooks
  replace unsafe ResetSubHit/GetUserItem entry breakpoints across the suite.
- Stale tests now use the valid extended root $0101 instead of reserved $0100,
  correct ability-slot bits and supported PyBoy register access. The end-turn
  fixture controls speed-tie randomness and checks side preservation.

## Verification

The exact local build/test results and ROM hashes are recorded in
`docs/16bit-validation.json`. These are local results; GitHub Actions status must
be checked separately for the published commit.

The normal and debug CPU suites each include 162 test programs. The ordinary
roster checks include native daycare generation, all 289 Pokédex list entries
in national/Johto/alphabetical order, cursor selection and cosmetic form cycling.

Five separate `native-test` builds define one real catalog fixture at `$0201`,
`$02fd`, `$02fe`, `$02ff` or `$0300`. They reuse Annihilape's art/stats and have explicit native
evolution and hatchling records. They add no Pokémon to the production roster.
`tests/fixtures/wide_species.py` uses no ROM stubs and exercises:

- Native encounter-record reading and the full wild generator, plus player and
  opponent insertion, catching and native battle identity publication.
- Base data, names, cries, front-picture decompression and battle-picture identity.
- Full PC encoding/checksum/decoding with stat reconstruction, evolution
  eligibility/target decoding in both directions, and daycare egg generation.
- Pokédex construction, cursor lookup and search; primary/backup Pokémon data
  and conversion-table saves; independent runtime roots under allocator pressure.

These are compiled-routine integration checks with synthetic game state. They
are not a complete interactive playthrough, an entire wide-species battle, or a
physical cable compatibility test. Existing battle regressions document any presentation
or unrelated-behavior stubs in their individual files.

`tests/test_native_link_packets.py` runs two independent emulator instances with
different conversion tables. Each normal/debug/wide ROM executes 48 party-packet
transfers across party sizes 1–6, trade/battle modes and both input formats. The
real packet builder, serial patch encoder/decoder, identity validation, battle
shadow publication and post-trade persistent insertion run without ROM stubs.
The harness transports byte buffers; it does not simulate cable interrupts,
link timing, the trade animation, mail delivery or a complete linked battle.
Wide builds also force collection during receive and independently preserve
all four trade-animation identity roots under allocator pressure.

The version-6 party record has the following wire representation:

| Field | On the wire | After receiving |
| --- | --- | --- |
| `MON_SPECIES` | Native ID low byte | Local runtime species byte |
| `MON_UNUSED` | Native ID high byte | Zero |
| `MON_FORM` | Form, egg and gender metadata; EXTSPECIES clear | Locally encoded form/metadata |

Eggs carry their underlying native species, never the `$00ff` display sentinel.
Unused slots are zeroed. Unsupported IDs, invalid counts and wire EXTSPECIES
bits are rejected before any destination records or allocator state are changed.
Save version 12 and party/save struct sizes remain unchanged.

Build a fixture with `make native-test NATIVE_TEST_SPECIES=513` (or 765–768),
then run `python3 tests/fixtures/wide_species.py polishedcrystal-native-test-3.2.3.gbc`.
Run `make tidy` between configurations. Production builds leave
`NUM_WIDE_SPECIES` at zero; adding a roster requires defining native records,
ordering and any new form/classification data rather than changing a count alone.

## Remaining work before a completed engine migration

1. Validate protocol 6 over an actual cable or a linked emulator pair, including
   a complete trade/animation, mail delivery and linked battle. The automated
   two-peer packet tests do not establish hardware timing compatibility.
2. Port the donor's move-ID conversion architecture and all move consumers for
   the expanded move namespace.
3. Validate wide-species gameplay interactively, including a complete battle,
   evolution animation, hatching, transfers and longer allocator lifetimes.
4. Extend and test content-specific forms/classification tables for any added
   roster, and provide explicit save-import tooling if old saves must migrate.

The branch remains experimental. The five high-ID catalog fixtures prove the
listed paths, not a finished replacement engine or an arbitrary expanded roster.
