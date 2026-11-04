; Convert constants at runtime; native words are never truncated by an opcode.
MACRO cp_move
	push hl
	push de
	ld de, \1
	call CompareMoveIDToDE
	pop de
	pop hl
ENDM

MACRO ld_move
	if "\1" === "a"
		push hl
		ld hl, \2
		call LoadMoveIDPreservingFlags
		pop hl
	else
		push af
		push hl
		ld hl, \2
		call GetMoveIDFromIndex
		pop hl
		ld \1, a
		pop af
	endc
ENDM

MACRO move_id
; Compact native ID: ordinary IDs use one byte; $00ff..$ffff use an escape + word.
	rept _NARG
		assert (\1) >= 0 && (\1) <= $ffff
		if (\1) < $ff
			db \1
		else
			db $ff
			dw \1
		endc
		shift
	endr
ENDM
