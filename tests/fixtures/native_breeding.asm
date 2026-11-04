; Test-only parents and travel shortcut. Deposit, breeding steps, Egg collection,
; inheritance, withdrawal, hatching and saving use the unchanged gameplay code.
assert DEF(NATIVE_SPECIES_TEST) && DEF(NATIVE_MOVE_TEST)
assert WIDE_TEST_MOVE_ALIAS == EMBER
assert !DEF(NATIVE_GAMEPLAY_TEST) && !DEF(NATIVE_LINK_TEST)

NativeBreedingScenario:
	opentext
	givepoke WIDE_TEST_SPECIES, PLAIN_FORM, 20, NO_ITEM, GREAT_BALL, WIDE_TEST_MOVE
	givepoke DITTO, PLAIN_FORM, 20
	givepoke PIKACHU, PLAIN_FORM, 5
	givemoney YOUR_MONEY, 10000
	setevent EVENT_GOT_A_POKEMON_FROM_ELM
	setevent EVENT_GOT_ODD_EGG
	setevent EVENT_LYRA_DAYCARE
	setevent EVENT_LYRA_ROUTE_34
	setmapscene DAYCARE, SCENE_DAYCARE_NOOP
	setmapscene ROUTE_34, SCENE_ROUTE34_NOOP
	closetext
	warp DAYCARE, 3, 5
	end
