; Native-ID data accessors. These are introduced before callers migrate so each
; subsystem can switch independently without altering party/save structures.

GetBaseDataFromNativeIDBC::
; in: bc = one-based native species ID
	dec bc
	jp GetBaseDataFromIndexBC

GetEggMovePointerFromNativeIDBC::
; in: bc = one-based native species ID
; out: a:hl = egg-move record pointer
	ld hl, EggSpeciesMovesPointers
	ld a, BANK(EggSpeciesMovesPointers)
	jp LoadDoubleIndirectPointer

GetPokemonNameFromNativeIDBC::
; in: bc = one-based native species ID
; out: de = wStringBuffer1 containing the display name
	ld a, b
	cp HIGH(NUM_SPECIES)
	jr c, .got_name_root
	jr nz, .variant
	ld a, c
	cp LOW(NUM_SPECIES) + 1
	jr c, .got_name_root

.variant
	call GetNativeVariantIdentityPointer
	inc hl
	inc hl
	ld a, BANK(NativeVariantIdentityTable)
	call GetFarWord
	ld b, h
	ld c, l

.got_name_root
	ld hl, PokemonNames
	ld a, BANK(PokemonNames)
	call LoadIndirectPointer
	ld de, wStringBuffer1
	push de
	ld bc, MON_NAME_LENGTH - 1
	ld a, BANK(PokemonNames)
	call FarCopyBytes
	ld h, d
	ld l, e
	ld [hl], '@'
	pop de
	ret

GetRootSpeciesFromNativeIDBC::
; Resolve a one-based native species ID to the root species used by Polished's
; transitional species/form runtime representation.
; in: bc = one-based native species ID
; out: bc = one-based root species ID
	ld a, b
	cp HIGH(NUM_SPECIES)
	ret c
	jr nz, .variant
	ld a, c
	cp LOW(NUM_SPECIES) + 1
	ret c

.variant
	call GetNativeVariantIdentityPointer
	inc hl
	inc hl
	ld a, BANK(NativeVariantIdentityTable)
	call GetFarWord
	ld b, h
	ld c, l
	ret

GetNativeVariantIdentityPointer:
; in: bc = one-based native mechanical-variant ID
; out: hl = its five-byte identity record
	ld h, b
	ld l, c
	ld de, -(NUM_SPECIES + 1)
	add hl, de
	ld b, h
	ld c, l
	add hl, hl
	add hl, hl
	add hl, bc
	ld de, NativeVariantIdentityTable
	add hl, de
	ret

GetNativeVariantIDFromOrdinalBC::
; in: bc = zero-based mechanical-variant ordinal
; out: bc = explicit one-based native species ID
	push de
	ld h, b
	ld l, c
	add hl, hl
	add hl, hl
	add hl, bc
	ld de, NativeVariantIdentityTable
	add hl, de
	ld a, BANK(NativeVariantIdentityTable)
	call GetFarWord
	ld b, h
	ld c, l
	pop de
	ret

GetNativeSpeciesIndexFromLegacyForm::
; Resolve the transitional species/form pair through the visual compatibility
; map, then replace its positional mechanical-variant result with the explicit
; native identity-table ID.
; in: c = species, b = form
; out: bc = zero-based native species index, carry if a variant was found
	ld hl, VariantVisualSpeciesAndFormTable
	call GetSpeciesAndFormIndexFromHL
	ret nc
	ld hl, -NUM_SPECIES
	add hl, bc
	ld b, h
	ld c, l
	call GetNativeVariantIDFromOrdinalBC
	dec bc
	scf
	ret

GetPokedexFlagIndex::
; Resolve a transitional species/form pair to its save-compatible Pokédex flag
; index. Mechanical identity is determined from the native species ID; cosmetic
; overlays retain their existing block between root species and variants.
; in: c = species, b = form
; out: de = zero-based physical Pokédex flag index; preserves bc
	push bc
	call GetNativeSpeciesIndexFromLegacyForm
	jr c, .mechanical_variant
	pop bc
	push bc
	call GetCosmeticSpeciesAndFormIndex
	jr .got_index
.mechanical_variant
	ld hl, NUM_COSMETIC_FORMS
	add hl, bc
	ld b, h
	ld c, l
.got_index
	ld d, b
	ld e, c
	pop bc
	ret

GetLegacySpeciesAndFormFromNativeIDBC::
; Resolve a native species ID and raw form to Polished's transitional runtime
; representation.
; in: bc = one-based native species ID, a = raw form
; out: a = c = root species byte, b = encoded form
	push af
	call GetRootSpeciesFromNativeIDBC
	pop af
	ld e, a
	ld a, b
	assert MON_EXTSPECIES_F == 5
	add a
	add a
	add a
	add a
	add a
	or e
	ld b, a
	ld a, c
	ret

LoadLegacySpeciesFromNativeWord::
; Read a native species word and resolve it to Polished's transitional runtime
; representation with no form. Intended for curated species-order lists.
; in: hl = native species word
; out: a = c = root species byte, b = encoded form, hl = next word
	ld a, [hli]
	ld c, a
	ld a, [hli]
	ld b, a
	xor a
	jp GetLegacySpeciesAndFormFromNativeIDBC

IsLegacySpeciesInNativeList::
; Test a transitional species/form pair against a zero-terminated native-ID
; word list.
; in: c = legacy species, b = form, hl = native-ID list
; out: carry set if found
	push de
	push hl
	call GetSpeciesAndFormIndex
	inc bc
	pop hl
.loop
	ld e, [hl]
	inc hl
	ld d, [hl]
	inc hl
	ld a, d
	or e
	jr z, .not_found
	ld a, e
	cp c
	jr nz, .loop
	ld a, d
	cp b
	jr nz, .loop
	scf
	pop de
	ret
.not_found
	and a
	pop de
	ret

GetTransientIDFromLegacySpeciesAndForm::
; Convert a compact Polished species/form pair at a ROM ingestion boundary.
; in: c = legacy species, b = form
; out: a = transient species ID
	call GetSpeciesAndFormIndex
	inc bc
	ld h, b
	ld l, c
	jp GetPokemonIDFromIndex

GetNativeSpeciesIDFromTransientID::
; Resolve an unchanged party/battle structure's species byte.
; in: a = transient species ID
; out: bc = one-based native species ID
	call GetPokemonIndexFromID
	ld b, h
	ld c, l
	ret

GetNativeSpeciesIndexFromTransientID::
; Resolve an unchanged party/battle structure's species byte.
; in: a = transient species ID
; out: bc = zero-based native species index
	call GetPokemonIndexFromID
	dec hl
	ld b, h
	ld c, l
	ret

GetLegacySpeciesAndFormFromTransientID::
; Decode a transient structure species and its presentation form.
; in: a = transient species ID, b = raw form
; out: a = c = root species byte, b = encoded form
	ld e, b
	push de
	call GetNativeSpeciesIDFromTransientID
	pop de
	ld a, e
	jp GetLegacySpeciesAndFormFromNativeIDBC

LoadTransientSpeciesAndFormFromHL::
; Read a native species word and raw form from the current ROM bank.
; out: a = transient species ID, b = raw form, hl = next byte
	ld a, [hli]
	ld c, a
	ld a, [hli]
	ld b, a
	ld a, [hli]
	ld e, a
	push de
	push hl
	ld h, b
	ld l, c
	call GetPokemonIDFromIndex
	pop hl
	pop de
	ld b, e
	ret

StoreTransientSpeciesFromNativeID::
StoreRoamMonNativeSpecies::
; Store a native species ID in a structure's transient species byte.
; in: bc = one-based native species ID, hl = structure species byte
	push hl
	call GetPokemonIDFromIndex
	pop hl
	ld [hl], a
	ret

GetLegacySpeciesAndFormFromTransientStruct::
; Decode a transient structure at a legacy runtime boundary.
; in: hl = structure species byte, de = form offset from species
; out: a = c = root species byte, b = encoded form; preserves hl
	push de
	push hl
	ld a, [hl]
	and a
	jr z, .empty
	call GetNativeSpeciesIDFromTransientID
	pop hl
	pop de
	push hl
	add hl, de
	ld a, [hl]
	and SPECIESFORM_MASK
	pop hl
	jp GetLegacySpeciesAndFormFromNativeIDBC
.empty
	ld b, a
	ld c, a
	pop hl
	pop de
	ret

MigrateLegacySpeciesAndFormAtHL::
; Convert one legacy structure to transient species storage in place.
; in: hl = structure species byte, de = form offset from species
; preserves hl and the complete form byte, including Egg and gender metadata
	ld a, [hl]
	and a
	ret z
	ld c, a
	push hl
	add hl, de
	ld b, [hl]
	call GetTransientIDFromLegacySpeciesAndForm
	pop hl
	ld [hl], a
	ret

GetLegacyRoamMonSpeciesAndForm::
; Decode a persistent roaming Pokémon at a legacy runtime boundary.
; in: hl = wRoamMon#Species
; out: d = root species byte, e = encoded form; preserves bc and hl
	push bc
	ld de, wRoamMon1Form - wRoamMon1Species
	call GetLegacySpeciesAndFormFromTransientStruct
	ld d, c
	ld e, b
	pop bc
	ret

MigrateLegacyRoamMons::
; Upgrade roaming Pokémon loaded from a save without a conversion table.
; Their old species/form fields are translated in place without moving any
; save-backed addresses.
	ld hl, wRoamMon1Species
rept 3
	call .migrate_one
	ld de, wRoamMon2Species - wRoamMon1Species
	add hl, de
endr
	ret

.migrate_one
	ld de, wRoamMon1Form - wRoamMon1Species
	jp MigrateLegacySpeciesAndFormAtHL


SECTION "Pokemon data format helpers", ROMX

GetLegacySpeciesAndFormFromPokemonDataStruct::
; Read a party-like structure in either the legacy or transient save format.
; in: hl = structure species byte, de = form offset from species
; out: a = c = root species byte, b = encoded form; preserves hl
	call PokemonDataUsesTransientSpecies
	jr nz, .legacy
	farcall GetLegacySpeciesAndFormFromTransientStruct
	ret
.legacy
	push hl
	ld a, [hl]
	ld c, a
	add hl, de
	ld a, [hl]
	and SPECIESFORM_MASK
	ld b, a
	ld a, c
	pop hl
	ret

LoadCurSpeciesAndFormFromPokemonDataStruct::
; Decode a party-like structure and publish the transitional runtime globals.
; in: hl = structure species byte; preserves hl
; out: a = c = root species byte, b = encoded form
	ld de, MON_FORM - MON_SPECIES
	call GetLegacySpeciesAndFormFromPokemonDataStruct
	ld a, b
	ld [wCurForm], a
	ld a, c
	ld [wCurPartySpecies], a
	ld [wCurSpecies], a
	ret

LoadBreedMon1LegacySpeciesAndForm::
	ld hl, wBreedMon1Species
	jr LoadBreedMonLegacySpeciesAndForm

LoadBreedMon2LegacySpeciesAndForm::
	ld hl, wBreedMon2Species
	; fallthrough

LoadBreedMonLegacySpeciesAndForm:
; Decode a daycare record and publish the transitional runtime globals.
; out: a = c = root species byte, b = encoded form
	ld de, MON_FORM - MON_SPECIES
	call GetLegacySpeciesAndFormFromPokemonDataStruct
	ld a, b
	ld [wCurForm], a
	ld a, c
	ld [wCurPartySpecies], a
	ld [wCurSpecies], a
	ret

PrepareLegacyPokemonDataStructForStorage::
; Convert a completed legacy party-like record immediately before storing it
; in a block whose format is selected by wPokemonDataFormat.
; in: hl = structure species byte; preserves hl
	call PokemonDataUsesTransientSpecies
	ret nz
	ld de, MON_FORM - MON_SPECIES
	farcall MigrateLegacySpeciesAndFormAtHL
	ret

PokemonDataUsesTransientSpecies::
; Return z when persistent player-party and daycare structures use transient
; conversion-table species IDs. This marker does not describe legacy opponent
; workspaces; source-selecting loaders must also check their record type.
	ld a, [wPokemonDataFormat]
	cp LOW(POKEMON_DATA_TRANSIENT_FORMAT)
	ret nz
	ld a, [wPokemonDataFormat + 1]
	cp HIGH(POKEMON_DATA_TRANSIENT_FORMAT)
	ret

PokemonDataSourceUsesTransientSpecies::
; Opponent/link parties remain legacy even when player/daycare records use
; transient IDs. Match GetPkmnSpecies/GetPkmnForm's source selection; do not
; apply the player save-format marker to an opponent record.
; out: z for a transient source, nz for a legacy source; preserves bc/de/hl
	ld a, [wMonType]
	cp OTPARTYMON
	jr z, .legacy_opponent
	jp PokemonDataUsesTransientSpecies
.legacy_opponent
	ld a, 1
	and a
	ret
