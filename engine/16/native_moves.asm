SECTION "Native move IDs", ROMX

MoveDataUsesTransientIDs::
; Z in native mode. Preserve BC/DE/HL and the selected WRAM bank.
	push bc
	ldh a, [rSVBK]
	ld c, a
	ld a, BANK(wMoveDataFormat)
	ldh [rSVBK], a
	ld a, [wMoveDataFormat]
	cp LOW(MOVE_DATA_TRANSIENT_FORMAT)
	jr nz, .done
	ld a, [wMoveDataFormat + 1]
	cp HIGH(MOVE_DATA_TRANSIENT_FORMAT)
.done
	ld a, c
	ldh [rSVBK], a
	pop bc
	ret

InitializeNativeMoveDataForNewGame::
	call ClearMoveIndexTable
	push af
	ldh a, [rSVBK]
	push af
	ld a, BANK(wMoveDataFormat)
	ldh [rSVBK], a
	ld a, LOW(MOVE_DATA_TRANSIENT_FORMAT)
	ld [wMoveDataFormat], a
	ld a, HIGH(MOVE_DATA_TRANSIENT_FORMAT)
	ld [wMoveDataFormat + 1], a
	pop af
	ldh [rSVBK], a
	pop af
	ret

ClearMoveIndexTable::
	push bc
	push hl
	ldh a, [rSVBK]
	push af
	ld a, BANK(wMoveIndexTable)
	ldh [rSVBK], a
	ld hl, wMoveIndexTable
	ld bc, wMoveIndexTableEnd - wMoveIndexTable
	xor a
	rst ByteFill
	pop af
	ldh [rSVBK], a
	pop hl
	pop bc
	ret

_GetMoveIndexFromID::
; A = runtime handle -> HL = native word. Preserve BC/DE.
	ld h, a
	call MoveDataUsesTransientIDs
	ld a, h
	jr z, .native
	ld l, a
	ld h, 0
	ret
.native
	___conversion_table_load wMoveIndexTable, MOVE_TABLE

_GetMoveIDFromIndex::
; HL = native word -> A = runtime handle. Preserve BC/DE.
	call MoveDataUsesTransientIDs
	jr z, .native
	ld a, h
	and a
	jr z, .legacy
	xor a ; high IDs require native mode; never silently truncate them
	ret
.legacy
	ld a, l
	ret
.native
	___conversion_table_store wMoveIndexTable, MOVE_TABLE
MoveTableGarbageCollection:
	push de
	ldh a, [rSVBK]
	push af
	ld a, BANK(wMoveIndexTable)
	ldh [rSVBK], a
	___conversion_bitmap_initialize wMoveIndexTable, MOVE_TABLE, .set_bit
	ld hl, .roots
.root_loop
	ld a, [hli]
	cp $ff
	jr z, .free
	ldh [rSVBK], a
	ld a, [hli]
	ld e, a
	ld a, [hli]
	ld d, a
	ld a, [hli]
	ld c, a
	push hl
	ld h, d
	ld l, e
.values
	ld a, [hli]
	push hl
	push bc
	call .set_bit
	pop bc
	pop hl
	dec c
	jr nz, .values
	pop hl
	jr .root_loop
.free
	ld a, BANK(wMoveIndexTable)
	ldh [rSVBK], a
	___conversion_bitmap_free_unused wMoveIndexTable, MOVE_TABLE
	pop af
	ldh [rSVBK], a
	pop de
	ret
.set_bit
	___conversion_bitmap_set MOVE_TABLE

DEF NATIVE_MOVE_ROOT_BYTES = 0
MACRO move_runtime_root
	REDEF NATIVE_MOVE_ROOT_BYTES += \2
	db BANK(\1)
	dw \1
	db \2
ENDM

.roots
for n, 1, PARTY_LENGTH + 1
	move_runtime_root wPartyMon{d:n}Moves, NUM_MOVES
	move_runtime_root wOTPartyMon{d:n}Moves, NUM_MOVES
	move_runtime_root wLinkPlayerPartyMon{d:n}Moves, NUM_MOVES
endr
	move_runtime_root wBreedMon1Moves, NUM_MOVES
	move_runtime_root wBreedMon2Moves, NUM_MOVES
	move_runtime_root wBattleMonMoves, NUM_MOVES
	move_runtime_root wEnemyMonMoves, NUM_MOVES
	move_runtime_root wTempMonMoves, NUM_MOVES
	move_runtime_root wContestMonMoves, NUM_MOVES
	move_runtime_root wOddEggMoves, NUM_MOVES
	move_runtime_root wPlayerUsedMoves, NUM_MOVES
	move_runtime_root wAIMoves, NUM_MOVES
	move_runtime_root wListMoves_MoveIndicesBuffer, NUM_MOVES
	move_runtime_root wMoveScreenMoves, 55
	move_runtime_root wMoveScreenSelectedMove, 1
	move_runtime_root wMoveSwapBuffer, 1
	move_runtime_root wNamedObjectIndex, 1
	move_runtime_root wCurMove, 1
	move_runtime_root wCurPlayerMove, 1
	move_runtime_root wCurEnemyMove, 1
	move_runtime_root wPlayerSelectedMove, 1
	move_runtime_root wEnemySelectedMove, 1
	move_runtime_root wLastPlayerCounterMove, 1
	move_runtime_root wLastEnemyCounterMove, 1
	move_runtime_root wLastPlayerMove, 1
	move_runtime_root wLastEnemyMove, 1
	move_runtime_root wPlayerTrappingMove, 1
	move_runtime_root wEnemyTrappingMove, 1
	move_runtime_root wPlayerMoveStructAnimation, 1
	move_runtime_root wEnemyMoveStructAnimation, 1
	move_runtime_root wPutativeTMHMMove, 1
	move_runtime_root wForewarnBestMove, 1
	move_runtime_root wFXAnimIDLo, 1
	db $ff
	assert NATIVE_MOVE_ROOT_BYTES + MOVE_TABLE_SAVED_RECENT_INDEXES + MOVE_TABLE_LOCKED_ENTRIES < MOVE_TABLE_ENTRIES

_CompareMoveIDToDE::
; Like CP against a native constant: preserve A/BC/DE, return Z/C, clobber HL.
	push bc
	ld b, a
	call GetMoveIndexFromID
	ld a, h
	cp d
	jr nz, .done
	ld a, l
	cp e
.done
	ld a, b
	pop bc
	ret

IsValidNativeMoveHL::
; Z for zero or an unsupported native move. Preserve HL/BC/DE.
	ld a, h
	and a
	jr nz, .wide
	ld a, l
	and a
	ret
.wide
if NUM_WIDE_MOVES
	push de
	push hl
	ld de, -FIRST_WIDE_MOVE
	add hl, de
	ld a, h
	cp HIGH(NUM_WIDE_MOVES)
	jr c, .valid
	jr nz, .invalid
	ld a, l
	cp LOW(NUM_WIDE_MOVES)
	jr nc, .invalid
.valid
	ld a, 1
	and a
	jr .done
.invalid
	xor a
.done
	pop hl
	pop de
	ret
else
	xor a
	ret
endc

_ReadMoveWordFromHL::
; Read a fixed native word from A:HL and allocate its local handle. Advance HL by 2.
; Preserve BC/DE; A is the resulting runtime move ID.
	push bc
	push hl
	call GetFarWord
	call GetMoveIDFromIndex
	pop hl
	inc hl
	inc hl
	pop bc
	ret

GetNativeMoveAddress::
; A = runtime move -> A:HL = eight-byte data record. Preserve BC/DE.
	push bc
	call GetMoveIndexFromID
	call IsValidNativeMoveHL
	jr z, .invalid
	call GetNativeMoveDataIndex
	ld hl, Moves
	ld a, BANK(Moves)
	call LoadIndirectPointer
	pop bc
	ret
.invalid
	ld hl, .no_move
	ld a, BANK(.no_move)
	pop bc
	ret
.no_move
	db 0, 0, 0, NORMAL, 0, 0, 0, STATUS

NativeGetMoveProperty::
; A = runtime move, HL = Moves + attribute. Preserve BC/DE.
	push bc
	push de
	ld c, a
	ld a, l
	sub LOW(Moves)
	ld e, a
	ld a, c
	and a
	jr z, .read
	ld a, e
	and a
	ld a, c
	jr z, .done ; MOVE_ANIM holds the runtime identity, not a native low byte
.read
	call GetNativeMoveAddress
	ld d, a
	ld c, e
	ld b, 0
	add hl, bc
	ld a, d
	call GetFarByte
.done
	pop de
	pop bc
	ret

NativeGetFixedMoveStruct::
; A = runtime move, DE = destination. Keep its runtime identity in MOVE_ANIM.
	push af
	push de
	call GetNativeMoveAddress
	ld bc, MOVE_LENGTH
	call FarCopyBytes
	pop hl
	pop af
	ld [hl], a
	call GetFixedCategory
	ld bc, MOVE_CATEGORY
	add hl, bc
	ld [hl], a
	ret

NativeGetMoveFixedCategory::
	push bc
	ld c, a
	ld hl, Moves + MOVE_CATEGORY
	call NativeGetMoveProperty
	cp STATUS
	jr z, .done
	ld b, a
	ld a, [wInitialOptions]
	bit PSS_OPT, a
	ld a, b
	jr nz, .done
	ld a, c
	ld hl, Moves + MOVE_TYPE
	call NativeGetMoveProperty
	cp SPECIAL_TYPES
	sbc a
	inc a
.done
	pop bc
	ret

NativeGetMoveName::
	push hl
	push bc
	ld a, [wNamedObjectIndex]
	ld [wCurSpecies], a
	call GetMoveIndexFromID
	call IsValidNativeMoveHL
	jr z, .invalid
	call GetNativeMoveDataIndex
	ld hl, MoveNames
	ld a, BANK(MoveNames)
	call LoadDoubleIndirectPointer
	ld de, wStringBuffer1
	push de
	ld bc, MOVE_NAME_LENGTH
	call FarCopyBytes
	pop de
	jr .done
.invalid
	ld de, wStringBuffer1
	ld a, '@'
	ld [de], a
.done
	pop bc
	pop hl
	ret

NativeGetMoveDescription::
	call GetMoveIndexFromID
	call IsValidNativeMoveHL
	jr z, .invalid
	call GetNativeMoveDataIndex
	ld hl, MoveDescriptions
	ld a, BANK(MoveDescriptions)
	jp LoadDoubleIndirectPointer
.invalid
	ld hl, Move00Description
	ld a, BANK(Move00Description)
	ret

LoadNativeMoveAnimation::
; FX animation IDs with a zero high byte are runtime move handles. Controls
; retain their separate $0100+ animation namespace, including move substitutes.
	call GetMoveIndexFromID
	call IsValidNativeMoveHL
	jr z, .empty
	call GetNativeMoveDataIndex
	ld hl, NativeMoveAnimations
	ld a, BANK(NativeMoveAnimations)
	call LoadIndirectPointer
	jr .read
.empty
	ld hl, BattleAnimations
	ld a, BANK(BattleAnimations)
.read
	call GetFarWord
	ld a, l
	ld [wBattleAnimAddress], a
	ld a, h
	ld [wBattleAnimAddress + 1], a
	ret

_ReadNativeMoveID::
; A:HL compact ROM stream -> BC native word; advance HL; preserve DE.
	push de
	ld d, a
	call GetFarByte
	inc hl
	ld b, 0
	ld c, a
	inc a
	jr nz, .done
	ld a, d
	call GetFarByte
	inc hl
	ld c, a
	ld a, d
	call GetFarByte
	inc hl
	ld b, a
.done
	pop de
	ret

_ReadMoveIDFromHL::
; A:HL compact ROM stream -> local handle A; advance HL; preserve BC/DE.
	push bc
	call _ReadNativeMoveID
	push hl
	ld h, b
	ld l, c
	call GetMoveIDFromIndex
	pop hl
	pop bc
	ret

_SkipMoveIDFromHL::
	push bc
	call _ReadNativeMoveID
	pop bc
	ret

GetFixedCategory::
; return category in a without modifying hl
; if category is STATUS, return it
	push hl
	ld bc, MOVE_CATEGORY
	add hl, bc
	ld a, BANK(Moves)
	call GetFarByte
	pop hl
	cp STATUS
	ret z
; if PSS_OPT is on, return the category
	ld b, a
	ld a, [wInitialOptions]
	bit PSS_OPT, a
	ld a, b
	ret nz
; return PHYSICAL or SPECIAL depending on the type
	push hl
	ld bc, MOVE_TYPE
	add hl, bc
	ld a, BANK(Moves)
	call GetFarByte
	pop hl
	cp SPECIAL_TYPES
	ld a, PHYSICAL
	ret c
	inc a ; SPECIAL
	ret


EncodeNativeBoxMoves::
	ld hl, wEncodedTempMonMoves
	ld de, wEncodedTempMonMoveHighs
	ld b, NUM_MOVES
.loop
	ld a, [hl]
	push hl
	call GetMoveIndexFromID
	ld a, h
	ld [de], a
	inc de
	ld a, l
	pop hl
	ld [hli], a
	dec b
	jr nz, .loop
	ret

DecodeNativeBoxMoves::
	ld hl, wEncodedTempMonMoves
	ld de, wEncodedTempMonMoveHighs
	ld b, NUM_MOVES
.loop
	ld a, [de]
	inc de
	push hl
	ld l, [hl]
	ld h, a
	or l
	jr z, .zero
	call IsValidNativeMoveHL
	jr z, .invalid
	call GetMoveIDFromIndex
.zero
	pop hl
	ld [hli], a
	dec b
	jr nz, .loop
	and a
	ret
.invalid
	pop hl
	scf
	ret

NativeSavedMoveRoots:
for n, 1, PARTY_LENGTH + 1
	dw wPartyMon{d:n}Moves
endr
	dw wBreedMon1Moves, wBreedMon2Moves

SaveNativeMoveData::
; SRAM open, DE = magic/data/checksum envelope. Never save transient handles.
	ldh a, [rSVBK]
	push af
	ld a, BANK(wPartyMon1)
	ldh [rSVBK], a
	push de
	xor a
	ld [de], a
	inc de
	ld [de], a
	inc de
	push de
	ld hl, NativeSavedMoveRoots
	ld b, PARTY_LENGTH + 2
.record
	push bc
	ld a, [hli]
	ld c, a
	ld a, [hli]
	push hl
	ld h, a
	ld l, c
	ld b, NUM_MOVES
.move
	ld a, [hli]
	push hl
	call GetMoveIndexFromID
	ld a, l
	ld [de], a
	inc de
	ld a, h
	ld [de], a
	inc de
	pop hl
	dec b
	jr nz, .move
	pop hl
	pop bc
	dec b
	jr nz, .record
	pop hl
	ld bc, NATIVE_SAVED_MOVE_LENGTH
	farcall Checksum
	ld a, e
	ld [hli], a
	ld [hl], d
	pop hl
	ld a, LOW(NATIVE_SAVED_MOVE_MAGIC)
	ld [hli], a
	ld [hl], HIGH(NATIVE_SAVED_MOVE_MAGIC)
	pop af
	ldh [rSVBK], a
	ret

LoadNativeMoveData::
; SRAM open, HL = native move words; rebuild local handles in party/daycare.
; Keep any other live runtime roots intact (e.g. returning from a link battle).
	ldh a, [rSVBK]
	push af
	ld a, BANK(wPartyMon1)
	ldh [rSVBK], a
	ld d, h
	ld e, l
	ld hl, NativeSavedMoveRoots
	ld b, PARTY_LENGTH + 2
.record
	push bc
	ld a, [hli]
	ld c, a
	ld a, [hli]
	push hl
	ld h, a
	ld l, c
	ld b, NUM_MOVES
.move
	push hl
	ld a, [de]
	inc de
	ld l, a
	ld a, [de]
	inc de
	ld h, a
	call GetMoveIDFromIndex
	pop hl
	ld [hli], a
	dec b
	jr nz, .move
	pop hl
	pop bc
	dec b
	jr nz, .record
	pop af
	ldh [rSVBK], a
	ret

VerifyNativeMoveData::
; SRAM open, HL = envelope. Return NZ for bad magic, checksum or native ID.
	ld a, [hli]
	cp LOW(NATIVE_SAVED_MOVE_MAGIC)
	jr nz, .done
	ld a, [hli]
	cp HIGH(NATIVE_SAVED_MOVE_MAGIC)
	jr nz, .done
	push hl
	ld bc, NATIVE_SAVED_MOVE_LENGTH
	farcall Checksum
	ld a, [hli]
	cp e
	jr nz, .bad_checksum
	ld a, [hl]
	cp d
.bad_checksum
	pop hl
	jr nz, .done
	ld b, NATIVE_SAVED_MOVE_COUNT
.move
	ld a, [hli]
	ld c, a
	ld a, [hli]
	push hl
	ld h, a
	ld l, c
	or l
	jr z, .valid
	call IsValidNativeMoveHL
	jr z, .bad_id
.valid
	pop hl
	dec b
	jr nz, .move
	xor a
	jr .done
.bad_id
	pop hl
	ld a, 1
	and a
.done
	push af
	call CloseSRAM
	pop af
	ret

GetRandomNativeMove::
; Choose uniformly from catalog ordinals, then map sparse expansion IDs.
; Use the synchronized battle PRNG for every draw.
	push bc
	push hl
.random
	call BattleRandom
	ld l, a
if NUM_NATIVE_MOVES > $100
	DEF MOVE_RANDOM_HIGH_MASK = 1
	REPT 8
		if MOVE_RANDOM_HIGH_MASK < HIGH(NUM_NATIVE_MOVES - 1)
			REDEF MOVE_RANDOM_HIGH_MASK = MOVE_RANDOM_HIGH_MASK * 2 + 1
		endc
	ENDR
	call BattleRandom
	and MOVE_RANDOM_HIGH_MASK
else
	xor a
endc
	ld h, a
	cp HIGH(NUM_NATIVE_MOVES)
	jr c, .chosen
	jr nz, .random
	ld a, l
	cp LOW(NUM_NATIVE_MOVES)
	jr nc, .random
.chosen
if NUM_WIDE_MOVES
	ld a, h
	and a
	jr nz, .wide
	ld a, l
	cp NUM_ATTACKS
	jr c, .ordinary
.wide
	ld bc, FIRST_WIDE_MOVE - NUM_ATTACKS
	add hl, bc
	jr .convert
.ordinary
endc
	inc hl
.convert
	call GetMoveIDFromIndex
	pop hl
	pop bc
	ret

if DEF(NATIVE_MOVE_TEST)
NativeWideMoveTestIdentity::
	dw WIDE_TEST_MOVE
NativeWideMoveTestAlias::
	dw WIDE_TEST_MOVE_ALIAS
NativeMoveStreamFixture::
	move_id NO_MOVE, TACKLE, STRUGGLE, WIDE_TEST_MOVE
NativeMoveWordFixture::
	dw NO_MOVE, TACKLE, STRUGGLE, WIDE_TEST_MOVE
endc

if DEF(NATIVE_MOVE_TEST)
NativeMoveReaderManifest::
	db CAL, GROUP_MAHOGANY_TOWN, MAP_MAHOGANY_TOWN
NativeMoveGiftScriptFixture::
	givepoke PIKACHU, PLAIN_FORM, 20, NO_ITEM, POKE_BALL, WIDE_TEST_MOVE
NativeMoveLoadScriptFixture::
	loadmove wPartyMon1Moves + 1, WIDE_TEST_MOVE
endc

GetNativeMoveDataIndex::
; Valid native HL -> one-based catalog ordinal BC. Sparse expansion IDs need
; no placeholder data records or thousands of empty indirect-table entries.
	ld b, h
	ld c, l
	ld a, h
	and a
	ret z
	ld bc, NUM_ATTACKS + 1 - FIRST_WIDE_MOVE
	add hl, bc
	ld b, h
	ld c, l
	ret
