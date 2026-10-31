BattleCommand_lowkick:
	push bc
	push de
	ldh a, [hBattleTurn]
	and a
	ld hl, wBattleMonNativeSpecies
	jr nz, .got_opp_species
	ld hl, wEnemyMonNativeSpecies
.got_opp_species
	ld c, [hl]
	inc hl
	ld b, [hl]
	; An empty native shadow uses the minimum power, never a stale legacy ID.
	ld a, b
	or c
	ld hl, 0
	jr z, .got_weight
	farcall GetNativeSpeciesWeight
.got_weight
	ld d, h
	ld e, l

	call GetOpponentIgnorableAbility
	cp LIGHT_METAL
	jr nz, .not_light_metal
	srl d
	rr e

.not_light_metal
	; Zero weight (including an empty/reserved identity) must not scan past
	; the table's final zero threshold.
	ld c, 20
	ld a, d
	or e
	jr z, .got_power
	ld hl, LowKickPowerByWeight
.loop2
	ld a, [hli]
	ld c, a
	ld a, [hli]
	sub e
	ld a, [hli]
	sbc d
	jr nc, .loop2
.got_power
	pop de
	ld d, c
	pop bc
	ret

INCLUDE "data/moves/low_kick_power.asm"
