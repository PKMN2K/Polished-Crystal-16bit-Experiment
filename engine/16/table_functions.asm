INCLUDE "engine/16/macros.asm"

; ID means the transient 8-bit representation used by structures that have not
; yet migrated. Index means the native 16-bit species identifier.

_GetPokemonIndexFromID::
	___conversion_table_load wPokemonIndexTable, MON_TABLE

_GetPokemonIDFromIndex::
	___conversion_table_store wPokemonIndexTable, MON_TABLE
	; Fall through when the table is full, as required by the store macro.
PokemonTableGarbageCollection:
	; Preserve de and rSVBK as required by ___conversion_table_store.
	push de
	ldh a, [rSVBK]
	push af
	___conversion_bitmap_initialize wPokemonIndexTable, MON_TABLE, .set_bit
	ld a, BANK(wPartyMons)
	ldh [rSVBK], a
	; Only persistent player/daycare records follow the save-format marker.
	; Keep all six slots: the contest hides party members by reducing the count.
	farcall PokemonDataUsesTransientSpecies
	jr nz, .legacy_party
	___conversion_bitmap_check_structs wPartyMons, PARTYMON_STRUCT_LENGTH, PARTY_LENGTH, .set_bit
	___conversion_bitmap_check_structs wBreedMon1Species, wBreedMon2 - wBreedMon1Species, 2, .set_bit
.legacy_party
	; Roamers and contest winner records already store transient IDs.
	___conversion_bitmap_check_structs wRoamMon1, wRoamMon2 - wRoamMon1, 3, .set_bit
	___conversion_bitmap_check_structs wBugContestFirstPlaceMon, wBugContestSecondPlaceMon - wBugContestFirstPlaceMon, 4, .set_bit
	; Runtime species/form pairs may carry wide-species handles. Ordinary
	; legacy bytes are excluded by the extension-bit/range check.
	call .scan_runtime_roots
	pop af
	ldh [rSVBK], a
	___conversion_bitmap_free_unused wPokemonIndexTable, MON_TABLE
	pop de
	ret

.set_bit
	___conversion_bitmap_set MON_TABLE

.scan_runtime_roots
	ld hl, .runtime_roots
.runtime_loop
	ld a, [hli]
	cp $ff
	ret z
	ldh [rSVBK], a
	ld a, [hli]
	ld c, a
	ld a, [hli]
	ld b, a
	ld a, [hli]
	ld e, a
	ld a, [hli]
	ld d, a
	push hl
	ld a, [bc]
	ld c, a
	ld a, [de]
	ld b, a
	farcall IsRuntimeSpeciesAliasBC
	jr nc, .next_runtime
	ld a, c
	sub NATIVE_RUNTIME_ALIAS_BASE
	call .set_bit
.next_runtime
	pop hl
	jr .runtime_loop

MACRO runtime_species_root
	db BANK(\1)
	dw \1, \2
ENDM

.runtime_roots
for n, 1, PARTY_LENGTH + 1
	runtime_species_root wOTPartyMon{d:n}Species, wOTPartyMon{d:n}Form
	runtime_species_root wLinkPlayerPartyMon{d:n}Species, wLinkPlayerPartyMon{d:n}Form
	runtime_species_root wHallOfFameTempMon{d:n}, wHallOfFameTempMon{d:n} + 4
endr
	runtime_species_root wBattleMonSpecies, wBattleMonForm
	runtime_species_root wEnemyMonSpecies, wEnemyMonForm
	runtime_species_root wTempMonSpecies, wTempMonForm
	runtime_species_root wContestMonSpecies, wContestMonForm
	runtime_species_root wOddEggSpecies, wOddEggForm
	runtime_species_root wCurSpecies, wCurForm
	runtime_species_root wCurPartySpecies, wCurForm
	runtime_species_root wWildMon, wWildMonForm
	runtime_species_root wTempWildMonSpecies, wWildMonForm
	runtime_species_root wNamedObjectIndex, wTempForm
	runtime_species_root wEvolutionOldSpecies, wEvolutionOldForm
	runtime_species_root wEvolutionNewSpecies, wEvolutionNewForm
	runtime_species_root wTempBattleMonSpecies, wTempBattleMonForm
	runtime_species_root wTempEnemyMonSpecies, wTempEnemyMonForm
	runtime_species_root wCurIconSpecies, wCurIconForm
	runtime_species_root wPokeAnimSpecies, wPokeAnimVariant
	runtime_species_root wColorVarySpecies, wColorVaryForm
	db $ff

_LockPokemonID::
	___conversion_table_lock_ID wPokemonIndexTable, MON_TABLE
