; A playable fixture, reached by inspecting the bedroom radio after New Game.
; Only test builds contain this event. All gifts, menus, animations, battles,
; capturing and saving use the normal engine; the CPU test supplies joypad input.
assert DEF(NATIVE_SPECIES_TEST) && DEF(NATIVE_MOVE_TEST)
assert WIDE_TEST_MOVE_ALIAS == EMBER, "Use NATIVE_TEST_MOVE=64769 for this fixture"

NativeGameplayScenario:
	readmem wNativeGameplayStage
	ifequal 3, .Finished
	opentext
	writetext .Welcome
	waitbutton
	givepoke WIDE_TEST_SPECIES, PLAIN_FORM, 20, NO_ITEM, POKE_BALL, WIDE_TEST_MOVE
	giveitems_unsafe MASTER_BALL, 1
	setevent EVENT_GOT_A_POKEMON_FROM_ELM
	closetext
	loadmem wNativeGameplayStage, 1
	loadwildmon WIDE_TEST_SPECIES, PLAIN_FORM, 5
	startbattle
	reloadmapafterbattle
	loadmem wNativeGameplayStage, 2
	opentext
	writetext .Capture
	waitbutton
	closetext
	loadwildmon WIDE_TEST_SPECIES, PLAIN_FORM, 5
	startbattle
	reloadmapafterbattle
	loadmem wNativeGameplayStage, 3
.Finished:
	opentext
	writetext .Complete
	waitbutton
	closetext
	end

.Welcome:
	text "Native battle test."
	para "Win with Ember."
	done
.Capture:
	text "Now catch this one"
	line "with a Master Ball."
	done
.Complete:
	text "Scenario complete."
	para "Save, restart, and"
	line "check your party."
	done
