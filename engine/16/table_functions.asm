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
	___conversion_bitmap_check_structs wPartyMons, PARTYMON_STRUCT_LENGTH, PARTY_LENGTH, .set_bit
	___conversion_bitmap_check_structs wBreedMon1Species, wBreedMon2 - wBreedMon1Species, 2, .set_bit
	___conversion_bitmap_check_structs wOTPartyMons, PARTYMON_STRUCT_LENGTH, PARTY_LENGTH, .set_bit
	___conversion_bitmap_check_structs wRoamMon1, wRoamMon2 - wRoamMon1, 3, .set_bit
	___conversion_bitmap_check_structs wBugContestFirstPlaceMon, wBugContestSecondPlaceMon - wBugContestFirstPlaceMon, 3, .set_bit
	___conversion_bitmap_check_values .set_bit, wTempMonSpecies, wContestMonSpecies, wBattleMonSpecies, \
		wEnemyMonSpecies, wOddEggSpecies, wCurSpecies
	pop af
	ldh [rSVBK], a
	___conversion_bitmap_free_unused wPokemonIndexTable, MON_TABLE
	pop de
	ret

.set_bit
	___conversion_bitmap_set MON_TABLE

_LockPokemonID::
	___conversion_table_lock_ID wPokemonIndexTable, MON_TABLE
