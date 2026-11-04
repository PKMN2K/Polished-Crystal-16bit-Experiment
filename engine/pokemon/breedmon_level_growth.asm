GetBreedMon1LevelGrowth:
	ld hl, wBreedMon1
	call CopyBreedMonForLevelGrowth
	ld a, [wBreedMon1Level]
	ld b, a
	ld a, d
	ld e, a
	sub b
	ld d, a
	ret

GetBreedMon2LevelGrowth:
	ld hl, wBreedMon2
	call CopyBreedMonForLevelGrowth
	ld a, [wBreedMon2Level]
	ld b, a
	ld a, d
	ld e, a
	sub b
	ld d, a
	ret

CopyBreedMonForLevelGrowth:
; CalcLevel consumes a runtime identity, while daycare saves use native handles.
	push hl
	ld de, wTempMon
	ld bc, BREEDMON_STRUCT_LENGTH
	rst CopyBytes
	pop hl
	ld de, MON_FORM - MON_SPECIES
	farcall GetLegacySpeciesAndFormFromPokemonDataStruct
	ld [wTempMonSpecies], a
	ld a, [wTempMonForm]
	and ~SPECIESFORM_MASK
	or b
	ld [wTempMonForm], a
	farjp CalcLevel
