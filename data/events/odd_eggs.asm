DEF NUM_ODD_EGGS EQU 10
DEF ODD_EGG_LENGTH EQU 11

MACRO special_egg_mon
	resolve_trainer_native_species \1, \2
	dw _tr_native_species
	db \2
ENDM

OddEggProbabilities:
	table_width 1
	db 10
	db 24
	db 38
	db 48
	db 60
	db 72
	db 84
	db 91
	db 93
	db 100
	assert_table_length NUM_ODD_EGGS

OddEggs:
	table_width ODD_EGG_LENGTH
	special_egg_mon PICHU, IS_EGG_MASK | PLAIN_FORM
	db THUNDERSHOCK, CHARM, DIZZY_PUNCH, NO_MOVE
	db $BB, $BB, $BB ; DVs
	db SHINY_MASK | HIDDEN_ABILITY | QUIRKY ; Personality

	special_egg_mon CLEFFA, IS_EGG_MASK | PLAIN_FORM
	db TACKLE, CHARM, DIZZY_PUNCH, NO_MOVE
	db $BB, $BB, $BB ; DVs
	db SHINY_MASK | HIDDEN_ABILITY | QUIRKY ; Personality

	special_egg_mon IGGLYBUFF, IS_EGG_MASK | PLAIN_FORM
	db SING, CHARM, DIZZY_PUNCH, NO_MOVE
	db $BB, $BB, $BB ; DVs
	db SHINY_MASK | HIDDEN_ABILITY | QUIRKY ; Personality

	special_egg_mon TYROGUE, IS_EGG_MASK | PLAIN_FORM
	db TACKLE, RAGE, FORESIGHT, DIZZY_PUNCH
	db $BB, $BB, $BB ; DVs
	db SHINY_MASK | HIDDEN_ABILITY | QUIRKY ; Personality

	special_egg_mon SMOOCHUM, IS_EGG_MASK | PLAIN_FORM
	db TACKLE, LICK, DIZZY_PUNCH, NO_MOVE
	db $BB, $BB, $BB ; DVs
	db SHINY_MASK | HIDDEN_ABILITY | QUIRKY ; Personality

	special_egg_mon ELEKID, IS_EGG_MASK | PLAIN_FORM
	db QUICK_ATTACK, LEER, DIZZY_PUNCH, NO_MOVE
	db $BB, $BB, $BB ; DVs
	db SHINY_MASK | HIDDEN_ABILITY | QUIRKY ; Personality

	special_egg_mon MAGBY, IS_EGG_MASK | PLAIN_FORM
	db HAZE, LEER, DIZZY_PUNCH, NO_MOVE
	db $BB, $BB, $BB ; DVs
	db SHINY_MASK | HIDDEN_ABILITY | QUIRKY ; Personality

	special_egg_mon MIME_JR_, IS_EGG_MASK | PLAIN_FORM
	db BARRIER, CONFUSION, TACKLE, DIZZY_PUNCH
	db $BB, $BB, $BB ; DVs
	db SHINY_MASK | HIDDEN_ABILITY | QUIRKY ; Personality

	special_egg_mon HAPPINY, IS_EGG_MASK | PLAIN_FORM
	db MINIMIZE, TACKLE, METRONOME, DIZZY_PUNCH
	db $BB, $BB, $BB ; DVs
	db SHINY_MASK | HIDDEN_ABILITY | QUIRKY ; Personality

	special_egg_mon MUNCHLAX, IS_EGG_MASK | PLAIN_FORM
	db SWEET_KISS, METRONOME, TACKLE, DIZZY_PUNCH
	db $BB, $BB, $BB ; DVs
	db SHINY_MASK | HIDDEN_ABILITY | QUIRKY ; Personality

	assert_table_length NUM_ODD_EGGS

MystriEgg:
	special_egg_mon TOGEPI, FEMALE | IS_EGG_MASK | PLAIN_FORM
	db GROWL, CHARM, MOONBLAST, AEROBLAST
	db $FF, $FF, $FF ; DVs
	db SHINY_MASK | HIDDEN_ABILITY | QUIRKY ; Personality
