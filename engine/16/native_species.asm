; Native-ID data accessors. These are introduced before callers migrate so each
; subsystem can switch independently without altering party/save structures.

GetBaseDataFromNativeIDBC::
; in: bc = one-based native species ID
	dec bc
	jp GetBaseDataFromIndexBC


GetAbilityFromNativeIDBC::
; in: bc = one-based native species ID, hl = target personality
; out: ability in a and b; preserves hl, de and c
; Reads the base-data ability bytes through a far pointer so this routine can
; live outside ROM0 without disturbing the current base-data buffer.
	ld a, b
	or c
	jr z, .no_ability

	ld a, [wInitialOptions]
	and ABILITIES_OPTMASK
	jr z, .got_ability

	push de
	push hl
	ld a, [hl]
	and ABILITY_MASK
	push af
	push bc

	ld hl, BaseData
	ld a, BANK(BaseData)
	call LoadIndirectPointer
	ld d, a
	ld bc, BASE_ABILITIES
	add hl, bc

	pop bc
	pop af
	cp ABILITY_1
	jr z, .got_ability_ptr
	inc hl
	cp ABILITY_2
	jr z, .got_ability_ptr
	inc hl
.got_ability_ptr
	ld a, d
	call GetFarByte
	pop hl
	pop de
	jr .got_ability

.no_ability
	xor a
.got_ability
	ld b, a
	ret

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
	push hl
	push af
	call GetRootSpeciesFromNativeIDBC
	pop af
	pop hl
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

IsActiveBattleNativeSpeciesInList::
; Test the current move user's direct native battle identity against a
; zero-terminated native-ID word list. hBattleTurn selects player (0) or enemy.
; in: hl = native-ID list
; out: carry set if found; preserves de
	push de
	push hl
	ld hl, wBattleMonNativeSpecies
	ldh a, [hBattleTurn]
	and a
	jr z, .got_shadow
	ld hl, wEnemyMonNativeSpecies
.got_shadow
	ld c, [hl]
	inc hl
	ld b, [hl]
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
	ld h, b
	ld l, c
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

CopyCaughtPokemonToParty::
; Copy the legacy wild opponent into a player slot, then convert only the
; completed destination identity to the active persistent format.
; in: a = zero-based player-party slot (caller has increased wPartyCount)
; The opponent record and all non-identity bytes remain unchanged.
	ld hl, wPartyMon1Species
	call GetPartyLocation
	push hl
	ld d, h
	ld e, l
	ld hl, wOTPartyMon1Species
	ld bc, PARTYMON_STRUCT_LENGTH
	rst CopyBytes
	pop hl
	jp PrepareLegacyPokemonDataStructForStorage

GetLeadAbilityFromPokemonData::
; Returns a = lead ability (zero for an Egg/empty record), preserving bc/de/hl
; and the current species/form globals and base data.
	ld a, [wPartyMon1IsEgg]
	and IS_EGG_MASK
	xor IS_EGG_MASK
	ret z
	push hl
	push de
	push bc
	ld hl, wPartyMon1Species
	ld de, MON_FORM - MON_SPECIES
	call GetLegacySpeciesAndFormFromPokemonDataStruct
	inc a
	jr z, .done
	dec a
	jr z, .done
	ld hl, wPartyMon1Personality
	call GetAbility
.done
	jp PopBCDEHL

PrepareGeneratedPlayerMonForStorage::
; TryAddMonToParty has finished its legacy construction. Convert only player
; records; trainer/wild/temporary gift opponent workspaces remain legacy.
; Preserves bc/de/hl; caller sets carry to report successful insertion.
	ld a, [wMonType]
	and $f
	ret nz
	push hl
	push de
	push bc
	ldh a, [hMoveMon]
	dec a
	ld hl, wPartyMon1Species
	call GetPartyLocation
	call PrepareLegacyPokemonDataStructForStorage
	jp PopBCDEHL

GetUserPartySpeciesAndForm::
; Return a=c=legacy species, b=encoded form, hl=source species address.
; Preserve de; player records follow the marker, opponents remain legacy.
	ld a, MON_SPECIES
	call UserPartyAttr
	ldh a, [hBattleTurn]
	jr DecodeBattlePartySpeciesAndForm

GetOpponentPartySpeciesAndForm::
	ld a, MON_SPECIES
	call OpponentPartyAttr
	ldh a, [hBattleTurn]
	xor 1
	; fallthrough
DecodeBattlePartySpeciesAndForm:
	push de
	and a
	jr nz, .legacy
	ld de, MON_FORM - MON_SPECIES
	call GetLegacySpeciesAndFormFromPokemonDataStruct
	pop de
	ret
.legacy
	ld c, [hl]
	push hl
	ld de, MON_FORM - MON_SPECIES
	add hl, de
	ld a, [hl]
	and SPECIESFORM_MASK
	ld b, a
	ld a, c
	pop hl
	pop de
	ret

GetTrueUserPartySpeciesAndForm::
; TrueUserPartyAttr accounts for a delayed Future Sight user off the field.
	ld a, MON_SPECIES
	call TrueUserPartyAttr
	ldh a, [hBattleTurn]
	jp DecodeBattlePartySpeciesAndForm

BattlePartyRootsMatch::
; z if the true user and opponent have the same root species (forms ignored).
	push hl
	push de
	push bc
	call GetTrueUserPartySpeciesAndForm
	ld d, b
	ld e, c
	call GetOpponentPartySpeciesAndForm
	ld a, c
	cp e
	jr nz, .done
	ld a, b
	xor d
	and EXTSPECIES_MASK
.done
	jp PopBCDEHL

ConvertCopiedPartyTempIdentity::
; After CopyBetweenPartyAndTemp copies a record: b=direction/type flags,
; c=zero-based slot. Both the OT workspace and temp records remain legacy.
	bit 7, b
	ret nz
	push hl
	push de
	push bc
	ld a, c
	ld hl, wPartyMon1Species
	call GetPartyLocation
	bit 0, b
	jr z, .to_party
	ld de, MON_FORM - MON_SPECIES
	call GetLegacySpeciesAndFormFromPokemonDataStruct
	ld a, c
	ld [wTempMonSpecies], a
	ld a, [wTempMonForm]
	and ~SPECIESFORM_MASK
	or b
	ld [wTempMonForm], a
	jr .done
.to_party
	call PrepareLegacyPokemonDataStructForStorage
.done
	jp PopBCDEHL

EncodeNativeBoxIdentity::
; Newbox reserves species byte zero as an explicit native-record tag.
; Native ID lives in the two formerly unused extra bytes; layout is unchanged.
	ld a, [wEncodedTempMonSpecies]
	ld c, a
	ld a, [wEncodedTempMonForm]
	and SPECIESFORM_MASK
	ld b, a
	call GetSpeciesAndFormIndex
	inc bc
	ld a, c
	ld [wEncodedTempMonExtra + 1], a
	ld a, b
	ld [wEncodedTempMonExtra + 2], a
	xor a
	ld [wEncodedTempMonSpecies], a
	ret

DecodeNativeBoxIdentity::
; Called only after the stored checksum has been checked. Carry on bad ID.
; Old nonzero legacy species records need no conversion and remain readable.
	ld a, [wEncodedTempMonSpecies]
	and a
	ret nz
	ld a, [wEncodedTempMonExtra + 1]
	ld c, a
	ld a, [wEncodedTempMonExtra + 2]
	ld b, a
	or c
	jr z, .invalid
	ld a, b
	cp HIGH(NUM_NATIVE_SPECIES + 1)
	jr c, .valid
	jr nz, .invalid
	ld a, c
	cp LOW(NUM_NATIVE_SPECIES + 1)
	jr nc, .invalid
.valid
	; $0100 is the unused root slot, not a storable species.
	ld a, b
	cp 1
	jr nz, .decode
	ld a, c
	and a
	jr z, .invalid
.decode
	ld a, [wEncodedTempMonForm]
	and FORM_MASK
	farcall GetLegacySpeciesAndFormFromNativeIDBC
	ld a, c
	ld [wEncodedTempMonSpecies], a
	ld a, [wEncodedTempMonForm]
	and ~SPECIESFORM_MASK
	or b
	ld [wEncodedTempMonForm], a
	and a
	ret
.invalid
	scf
	ret

RefreshPartyIdentityAfterFormChange::
; Mechanical forms have their own native IDs; refresh the stored slot after
; a form-byte edit without ever treating the transient byte as a root species.
	call PokemonDataUsesTransientSpecies
	ret nz
	push hl
	push de
	push bc
	ld hl, wPartyMon1Species
	ld a, [wCurPartyMon]
	call GetPartyLocation
	ld de, MON_FORM - MON_SPECIES
	call GetLegacySpeciesAndFormFromPokemonDataStruct
	push hl
	farcall GetTransientIDFromLegacySpeciesAndForm
	pop hl
	ld [hl], a
	jp PopBCDEHL

MigrateLegacyPlayerPokemonData::
; RAM-only migration; publish the format marker after all eight records exist.
; Dedicated locks keep partially converted records alive during collection,
; while the old marker still prevents scanning them as transient records.
; Caller must already have loaded/validated the save's conversion table.
; Kept behind the activation gate until gameplay and >$01ff proofs pass.
	call PokemonDataUsesTransientSpecies
	ret z
	push hl
	push de
	push bc
	ld hl, wPartyMon1Species
	ld b, PARTY_LENGTH
	ld c, MON_LOCK_SAVE_MIGRATION_START
.party
	call .convert_and_lock
	ld de, PARTYMON_STRUCT_LENGTH
	add hl, de
	dec b
	jr nz, .party
	ld hl, wBreedMon1Species
	call .convert_and_lock
	ld hl, wBreedMon2Species
	call .convert_and_lock
	ld a, LOW(POKEMON_DATA_TRANSIENT_FORMAT)
	ld [wPokemonDataFormat], a
	ld a, HIGH(POKEMON_DATA_TRANSIENT_FORMAT)
	ld [wPokemonDataFormat + 1], a
	ld l, MON_LOCK_SAVE_MIGRATION_START
.unlock
	xor a
	push hl
	call LockPokemonID
	pop hl
	inc l
	ld a, l
	cp MON_LOCK_SAVE_MIGRATION_END
	jr nz, .unlock
	jp PopBCDEHL
.convert_and_lock
	push bc
	ld de, MON_FORM - MON_SPECIES
	farcall MigrateLegacySpeciesAndFormAtHL
	pop bc
	push hl
	ld a, [hl]
	ld l, c
	push bc
	call LockPokemonID
	pop bc
	pop hl
	inc c
	ret

GetNativeSpeciesIDFromPokemonDataStruct::
; in: hl = player/daycare species byte, de = form offset
; out: bc = one-based native ID (zero for an empty record)
; Preserve hl/de and do not publish legacy globals or allocate a table slot.
	call PokemonDataUsesTransientSpecies
	jr nz, GetNativeSpeciesIDFromLegacyPokemonDataStruct
	push hl
	push de
	ld a, [hl]
	farcall GetNativeSpeciesIDFromTransientID
	pop de
	pop hl
	ret

GetNativeSpeciesIDFromLegacyPokemonDataStruct::
; Same contract, for opponent records independent of the player format marker.
	push hl
	push de
	ld a, [hl]
	ld c, a
	ld b, 0
	add hl, de
	ld a, [hl]
	and SPECIESFORM_MASK
	ld b, a
	ld a, c
	and a
	jr nz, .convert
	ld a, b
	and EXTSPECIES_MASK
	jr z, .done
.convert
	call GetSpeciesAndFormIndex
	inc bc
.done
	pop de
	pop hl
	ret

GetBaseDataFromPokemonDataStruct::
; Load base data directly from a persistent native identity. This avoids a
; native -> legacy root/form -> native round-trip at the data lookup boundary.
; in: hl = player/daycare species byte; preserves bc/de/hl and species globals
; out: carry set for an empty identity (base-data buffer left unchanged)
	push hl
	push de
	push bc
	ld de, MON_FORM - MON_SPECIES
	call GetNativeSpeciesIDFromPokemonDataStruct
	call LoadBaseDataFromNonzeroNativeIDBC
	jp PopBCDEHL

LoadBaseDataFromNonzeroNativeIDBC:
	ld a, b
	or c
	scf
	ret z
	farcall GetBaseDataFromNativeIDBC
	and a
	ret

GetBaseDataFromEnemyBattleNativeSpecies::
; Load base data directly from the active enemy's native identity shadow.
; Preserve bc/de/hl and species globals; carry set for an empty shadow.
	push hl
	push de
	push bc
	ld hl, wEnemyMonNativeSpecies
	ld c, [hl]
	inc hl
	ld b, [hl]
	call LoadBaseDataFromNonzeroNativeIDBC
	jp PopBCDEHL

GetBaseDataFromActiveBattleNativeSpecies::
; Load base data from the native identity shadow of the active battler.
; hBattleTurn selects player (0) or enemy (1). Preserve bc/de/hl and species
; globals; carry set for an empty shadow, leaving base data unchanged.
	push hl
	push de
	push bc
	ld hl, wBattleMonNativeSpecies
	ldh a, [hBattleTurn]
	and a
	jr z, .got_shadow
	ld hl, wEnemyMonNativeSpecies
.got_shadow
	ld c, [hl]
	inc hl
	ld b, [hl]
	call LoadBaseDataFromNonzeroNativeIDBC
	jp PopBCDEHL

GetBaseDataFromTrueUserParty::
; Load the original attacker's base data, including delayed Future Sight.
; Player records follow their format marker; opponent records remain legacy.
; Preserve bc/de/hl and species globals; carry set for an empty identity.
	push hl
	push de
	push bc
	ld a, MON_SPECIES
	call TrueUserPartyAttr
	ldh a, [hBattleTurn]
	and a
	jr z, .player
	ld de, MON_FORM - MON_SPECIES
	call GetNativeSpeciesIDFromLegacyPokemonDataStruct
	call LoadBaseDataFromNonzeroNativeIDBC
	jr .done
.player
	call GetBaseDataFromPokemonDataStruct
.done
	jp PopBCDEHL
