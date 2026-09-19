_FindThatSpeciesYourTrainerID:
	call FindThatSpecies
	ret z
	ld a, e
	ld hl, wPartyMon1ID
	ld bc, PARTYMON_STRUCT_LENGTH
	rst AddNTimes
	ld a, [wPlayerID]
	cp [hl]
	jr nz, .nope
	inc hl
	ld a, [wPlayerID + 1]
	cp [hl]
	jr nz, .nope
	ld a, $1
	and a
	ret

.nope
	xor a
	ret

FindThatSpecies:
; Find species = c, extspecies+form = b in your party.
; If form == NO_FORM, only check extspecies
; If you have no Pokemon, returns e = -1 and z.
; If that species is in your party, returns its location in e, and nz.
; Otherwise, returns z.
	ld e, -1
	ld a, [wPartyCount]
	ld d, a
	and a
	ret z
	inc e
	ld hl, wPartyMon1Species
.loop
	push de
	push bc
	ld de, MON_FORM - MON_SPECIES
	farcall GetLegacySpeciesAndFormFromPokemonDataStruct
	pop de
	call CompareSpeciesWithDE
	pop de
	jr nz, .next
	or 1
	ret

.next
	inc e
	ld a, d
	and $f
	cp e
	ret z
	push de
	ld de, PARTYMON_STRUCT_LENGTH
	add hl, de
	pop de
	jr .loop
