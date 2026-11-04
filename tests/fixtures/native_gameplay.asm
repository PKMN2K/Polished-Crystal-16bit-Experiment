; Start at the bedroom radio; use its PC after the first cold Continue.
; Only test builds contain this event. All gifts, menus, animations, battles,
; capturing and saving use the normal engine; the CPU test supplies joypad input.
assert DEF(NATIVE_SPECIES_TEST) && DEF(NATIVE_MOVE_TEST)
assert WIDE_TEST_MOVE_ALIAS == EMBER, "Use NATIVE_TEST_MOVE=64769 for this fixture"

NativeGameplayLifecycle:
	readmem wNativeGameplayStage
	iftruefwd NativeGameplayScenario
	; The fixture stage is intentionally volatile across a cartridge reload.
	readmem wPartyCount
	ifgreater 2, NativeGameplayScenario.FinalPC
	loadmem wNativeGameplayStage, 3
	; fallthrough
NativeGameplayScenario:
	readmem wNativeGameplayStage
	ifequalfwd 3, .Trainer
	ifequalfwd 4, .PC
	ifequalfwd 5, .DayCare
	ifequalfwd 6, .DayCare
	ifequalfwd 7, .Lessons
	ifequalfwd 8, .FinalPC
	ifgreater 7, .Finished
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

.Trainer:
	winlosstext .TrainerWin, 0
	loadtrainer CAL, 2
	startbattle
	reloadmapafterbattle
	loadmem wNativeGameplayStage, 4
	end

.PC:
	scall .OpenPC
	loadmem wNativeGameplayStage, 5
	end

.FinalPC:
	scall .OpenPC
	loadmem wNativeGameplayStage, 8
	end

.OpenPC:
	opentext
	special PokemonCenterPC
	closetext
	end

.DayCare:
	opentext
	special Special_DayCareMan
	waitbutton
	closetext
	readmem wNativeGameplayStage
	addval 1
	writemem wNativeGameplayStage
	end

.Lessons:
	opentext
	givepoke ANNIHILAPE, PLAIN_FORM, 19
	giveitems_unsafe RARE_CANDY, 2
	giveegg WIDE_TEST_SPECIES
	loadmem wNativeGameplayStage, 8
	writetext .LearnAndHatch
	waitbutton
	closetext
	end

.TrainerWin:
	text "Native trainer"
	line "battle complete."
	done
.LearnAndHatch:
	text "Use both Candies"
	line "on the new gift."
	para "Then hatch the Egg."
	done

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
