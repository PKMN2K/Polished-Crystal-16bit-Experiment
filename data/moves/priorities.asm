MovePriorities:
	; no move is for explicit switch-out
	dw NO_MOVE
	db 10
	dw ENDURE
	db 4
	dw PROTECT
	db 4
	dw EXTREMESPEED
	db 2
	dw AQUA_JET
	db 1
	dw BULLET_PUNCH
	db 1
	dw ICE_SHARD
	db 1
	dw MACH_PUNCH
	db 1
	dw QUICK_ATTACK
	db 1
	dw SUCKER_PUNCH
	db 1
	; everything else 0
	dw AVALANCHE
	db -4
	dw COUNTER
	db -5
	dw MIRROR_COAT
	db -5
	dw ROAR
	db -6
	dw TELEPORT
	db -6
	dw TRICK_ROOM
	db -7
	dw -1
