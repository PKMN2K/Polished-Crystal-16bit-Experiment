PlayStereoCry::
	push af
	ld a, 1
	ld [wStereoPanningMask], a
	pop af
	call _PlayMonCry
	jmp WaitSFX

PlayStereoCry2::
; Don't wait for the cry to end.
; Used during pic animations.
	push af
	ld a, 1
	ld [wStereoPanningMask], a
	pop af
	jr _PlayMonCry

PlayMonCry::
	call PlayMonCry2
	jmp WaitSFX

PlayMonCry2::
; Don't wait for the cry to end.
	push af
	xor a
	ld [wStereoPanningMask], a
	ld [wCryTracks], a
	pop af
	; fallthrough

_PlayMonCry::
	push hl
	push de
	push bc

	call GetCryIndex
	jr c, .done

	ld e, c
	ld d, b
	call PlayCry

.done
	jmp PopBCDEHL

LoadCryFromNativeIDBC::
; Native mechanical forms share their root species' cry, as in LoadCry.
	farcall GetRootSpeciesFromNativeIDBC
	ld a, b
	or c
	scf
	ret z
	ld a, b
	and a
	jr nz, .valid
	ld a, c
	cp EGG
	scf
	ret z
.valid
	dec bc
	jr LoadCry.load_index

LoadCry::
; Load cry bc.

	call GetCryIndex
	ret c
.load_index
	anonbankpush PokemonCries

_LoadCry:
	inc bc ; zero-based base-species index -> one-based native species ID
	ld hl, PokemonCries
	ld a, BANK(PokemonCries)
	call LoadIndirectPointer

	ld a, [hli]
	ld e, a
	ld d, 0
	ld a, [hli]
	ld [wCryPitch], a
	ld a, [hli]
	ld [wCryPitch + 1], a
	ld a, [hli]
	ld [wCryLength], a
	ld a, [hl]
	ld [wCryLength + 1], a

	and a
	ret

GetCryIndex::
; input: C=runtime species byte, B=form; output: BC=zero-based native root.
	farcall GetNativeRootFromRuntimeBC
	ld a, b
	or c
	jr z, .no
	ld a, b
	and a
	jr nz, .valid
	ld a, c
	cp EGG
	jr z, .no
.valid
	dec bc
	and a
	ret
.no
	scf
	ret
