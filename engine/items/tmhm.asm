CanLearnTMHMMove:
	ld a, [wCurPartySpecies]
	ld [wCurSpecies], a
	call GetBaseData
	ld hl, wBaseTMHM
	push hl

	ld a, [wPutativeTMHMMove]
	call GetMoveIndexFromID
	ld d, h
	ld e, l
	ld c, 0
	ld hl, TMHMMoves
.loop
	ld a, [hli]
	ld b, a
	ld a, [hli]
	or b
	jr z, .end
	dec hl
	ld a, [hli]
	cp d
	jr nz, .next
	ld a, b
	cp e
	jr z, .found
.next
	inc c
	jr .loop

.found
	pop hl
	ld b, CHECK_FLAG
	push de
	ld d, 0
	farcall SmallFlagAction
	pop de
	ret

.end
	pop hl
	ld c, 0
	ret

GetTMHMMove:
	ld a, [wTempTMHM]
	dec a
	ld hl, TMHMMoves
	ld b, 0
	ld c, a
	add hl, bc
	add hl, bc
	ld a, BANK(TMHMMoves)
	call ReadMoveWordFromHL
	ld [wTempTMHM], a
	ret

INCLUDE "data/moves/tmhm_moves.asm"
