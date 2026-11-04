; Test-only shortcut to the unchanged Cable Club and its receptionists.
; Different gift orders establish independently allocated native handles.
assert DEF(NATIVE_SPECIES_TEST) && DEF(NATIVE_MOVE_TEST)
assert WIDE_TEST_MOVE_ALIAS == EMBER
assert !DEF(NATIVE_GAMEPLAY_TEST)

NativeLinkScenario:
	opentext
	writetext .ChoosePeer
	yesorno
	iffalsefwd .PeerB
	givepoke PIKACHU, PLAIN_FORM, 5
	givepoke WIDE_TEST_SPECIES, PLAIN_FORM, 20, NO_ITEM, POKE_BALL, WIDE_TEST_MOVE
	sjumpfwd .Club
.PeerB:
	givepoke WIDE_TEST_SPECIES, PLAIN_FORM, 10, NO_ITEM, POKE_BALL, WIDE_TEST_MOVE
	givepoke PIKACHU, PLAIN_FORM, 5
.Club:
	setevent EVENT_GOT_A_POKEMON_FROM_ELM
	setevent EVENT_GAVE_MYSTERY_EGG_TO_ELM
	closetext
	warp POKECENTER_2F, 5, 3
	end
.ChoosePeer:
	text "Prepare peer A?"
	done
