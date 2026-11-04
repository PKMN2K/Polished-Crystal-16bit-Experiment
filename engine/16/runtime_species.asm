SECTION "Native runtime species handles", ROMX

IsWideNativeSpeciesBC::
; Carry if BC is a defined additional native root. Preserve BC/DE/HL.
if NUM_WIDE_SPECIES
	push hl
	ld hl, -FIRST_WIDE_SPECIES
	add hl, bc
	ld a, h
	cp HIGH(NUM_WIDE_SPECIES)
	jr c, .valid
	jr nz, .invalid
	ld a, l
	cp LOW(NUM_WIDE_SPECIES)
	jr nc, .invalid
.valid
	pop hl
	scf
	ret
.invalid
	pop hl
endc
	and a
	ret

IsValidNativeSpeciesBC::
; Z for an absent/unsupported identity. Preserve BC/DE/HL.
	push hl
	push de
	push bc
	farcall GetRootSpeciesFromNativeIDBC
	ld a, b
	or c
	jp PopBCDEHL

IsRuntimeSpeciesAliasBC::
; Carry if the transitional species/form pair contains a native table handle.
; No allocator state is read here; stale handles resolve to zero on decoding.
	bit MON_EXTSPECIES_F, b
	jr z, .ordinary
	ld a, c
	sub NATIVE_RUNTIME_ALIAS_BASE + 1
	cp MON_TABLE_ENTRIES
	ret
.ordinary
	and a
	ret

GetNativeRootFromRuntimeBC::
; Decode a runtime root without discarding its high byte. Preserve DE/HL.
	call IsRuntimeSpeciesAliasBC
	jr nc, .ordinary
	ld a, c
	sub NATIVE_RUNTIME_ALIAS_BASE
	push hl
	farcall GetNativeSpeciesIDFromTransientID
	pop hl
	ret
.ordinary
	ld a, b
	call ConvertFormToExtendedSpecies
	ld b, a
	ret

PackNativeRootForRuntimeBC::
; BC = valid native root, A = raw form/metadata.
; Return A=C=runtime species byte, B=encoded form. Preserve DE/HL.
; Existing roots remain byte-for-byte compatible; wide roots get donor handles.
	push hl
	push de
	ld e, a
	ld a, b
	cp 2
	jr nc, .wide
	assert MON_EXTSPECIES_F == 5
	add a
	add a
	add a
	add a
	add a
	ld d, a
	ld a, e
	and ~EXTSPECIES_MASK
	or d
	ld b, a
	ld a, c
	jr .done
.wide
	ld h, b
	ld l, c
	call GetPokemonIDFromIndex
	add NATIVE_RUNTIME_ALIAS_BASE
	ld c, a
	ld a, e
	or EXTSPECIES_MASK
	ld b, a
	ld a, c
.done
	pop de
	pop hl
	ret

_GetNationalDexNumber::
; input: c = species, b = extspecies+form
; output: bc = natdex number ((256*extspecies + c) - (2*extspecies))
	call GetNativeRootFromRuntimeBC
	call IsWideNativeSpeciesBC
	jr nc, .ordinary
	push hl
	ld hl, NUM_POKEMON + 1 - FIRST_WIDE_SPECIES
	add hl, bc
	ld b, h
	ld c, l
	pop hl
	ret
.ordinary
	ld a, b
	add a
	push de
	ld d, a
	ld a, c
	sub d
	pop de
	ld c, a
	ret nc
	dec b
	ret


SkipEvolutionData::
; HL points to an evolution list in the evolution bank.
; Return HL at the learnset, A=0; preserve BC/DE. Native words may contain $ff.
.loop
	ld a, BANK(EvosAttacks)
	call GetFarByte
	inc hl
	inc a
	ret z
	dec a
	call SkipEvolutionEntry
	jr .loop

SkipEvolutionEntry::
; A=method, HL=first parameter. Skip parameters and native word + form.
; Preserve BC/DE.
	cp EVOLVE_STAT
	jr z, .extra
	cp EVOLVE_HOLDING
	jr z, .extra
	cp EVOLVE_PARTY
	jr nz, .target
.extra
	inc hl
.target
	inc hl
	inc hl
	inc hl
	inc hl
	ret

ReadNativeDexRecord::
; HL = native root word followed by form/metadata in the current WRAM bank.
; Return runtime BC/A and HL on the form byte; preserve DE.
	ld a, [hli]
	ld c, a
	ld a, [hli]
	ld b, a
	ld a, [hl]
	farjp GetLegacySpeciesAndFormFromNativeIDBC

WriteNativeDexRecord::
; HL = three-byte list record, BC = runtime species/form. Preserve BC/DE/HL.
	push hl
	push bc
	ld a, b
	push af
	call GetNativeRootFromRuntimeBC
	ld a, c
	ld [hli], a
	ld a, b
	ld [hli], a
	pop af
	ld [hl], a
	pop bc
	pop hl
	ret

NativeSpeciesFromDexOrdinal::
; BC = zero-based national Pokédex ordinal. Preserve DE/HL.
	push hl
	ld hl, -NUM_POKEMON
	add hl, bc
	jr c, .wide
	inc bc
	ld a, b
	and a
	jr nz, .past_reserved
	ld a, c
	cp EGG
	jr c, .done
.past_reserved
	inc bc
	inc bc
	jr .done
.wide
	ld bc, FIRST_WIDE_SPECIES
	add hl, bc
	ld b, h
	ld c, l
.done
	pop hl
	ret

CanEvolveWithItemB::
; HL=evolution list, B=item. Return Z when a matching item/trade entry exists.
.loop
	ld a, BANK(EvosAttacks)
	call GetFarByte
	inc hl
	cp $ff
	jr z, .none
	push af
	ld c, EVOLVE_ITEM
	ld a, b
	cp LINKING_CORD
	jr nz, .got_type
	ld c, EVOLVE_TRADE
.got_type
	pop af
	push af
	cp c
	jr nz, .skip
	ld a, BANK(EvosAttacks)
	call GetFarByte
	cp b
	jr z, .match
.skip
	pop af
	call SkipEvolutionEntry
	jr .loop
.match
	pop bc ; discard saved method without changing Z
	ret
.none
	or 1
	ret

ReadNativeSpeciesForm::
; A=ROM bank, HL=native word + presentation form. Return runtime BC/A,
; HL immediately after the record; preserve DE.
	push af
	push hl
	call GetFarWord
	ld b, h
	ld c, l
	pop hl
	inc hl
	inc hl
	pop af
	call GetFarByte
	inc hl
	farjp GetLegacySpeciesAndFormFromNativeIDBC
