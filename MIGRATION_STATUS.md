# DanielOlivaw 16-bit migration status

**Status: incomplete engine port; buildable species migration checkpoint.**

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
- Fresh games initialize native player storage; opponent and several temporary
  structures still use the legacy runtime representation.
- Current upstream's single grass encounter rate, new Battle Tower Bloodmoon
  sets, current map/assets and WRAM layout are retained.
- Save version 12 is required. Version 10 and both incompatible meanings of
  version 11 are rejected. No automatic old-save upgrade is claimed.
- Fixed inherited Metal Powder behavior: non-Ditto Pokémon no longer get the
  boost, and faithful builds preserve the defense value during species matching.
- A single bounded test runner, eight-config CI, and shared opcode-checked hooks
  replace unsafe ResetSubHit/GetUserItem entry breakpoints across the suite.
- Stale tests now use the valid extended root $0101 instead of reserved $0100,
  correct ability-slot bits and supported PyBoy register access. The end-turn
  fixture controls speed-tie randomness and checks side preservation.

## Verification

The exact local build/test results and ROM hashes are recorded in
`docs/16bit-validation.json`. These are local results; GitHub Actions status must
be checked separately for the published commit.

A headless boot check reached the Polished Crystal title screen. CPU tests
exercise compiled routines with synthetic fixtures and, where documented in
each test, stubbed presentation or unrelated behavior. Passing them does not
prove a complete playthrough, link compatibility or arbitrary expanded species.

## Remaining work before a completed engine migration

1. Remove the nine-bit legacy projection from live generation, opponent parties,
   temporary records, evolution/breeding and graphical paths. In particular,
   `GetLegacySpeciesAndFormFromNativeIDBC` and
   `PrepareBattlePictureIdentity.pack_legacy_root` still limit representable
   runtime roots. A 16-bit allocator alone does not remove these limits.
2. Prove a real catalog species above $01ff through encounter, generation,
   battle, catching, party, PC, save/load, evolution/breeding and Pokédex use.
   The current tests of larger raw words establish storage primitives only.
3. Reconcile link battle/trade serialization with native IDs, and test both peers.
4. Port the donor's move-ID conversion architecture and all move consumers if
   the requested full 16-bit engine is to include its expanded move namespace.
5. Complete interactive gameplay validation and explicit save-import tooling.

The branch is experimental. Do not treat it as a finished replacement engine
or as proof that more than 511 playable species can already be added.
