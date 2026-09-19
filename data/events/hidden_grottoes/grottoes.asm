HiddenGrottoData:
	table_width 15

MACRO hidden_grotto_mon
	if _NARG == 1
		resolve_trainer_native_species \1, NO_FORM
		dw _tr_native_species
		db NO_FORM
	else
		resolve_trainer_native_species \1, \2
		dw _tr_native_species
		db \2
	endc
ENDM

	; db warp number, rare item, level
	; hidden_grotto_mon common mon 1
	; hidden_grotto_mon common mon 2
	; hidden_grotto_mon uncommon mon
	; hidden_grotto_mon rare mon

; HIDDENGROTTO_ROUTE_32
	db 5, EVERSTONE, 5
	hidden_grotto_mon MAREEP
	hidden_grotto_mon WOOPER
	hidden_grotto_mon EKANS, ARBOK_JOHTO_FORM
	hidden_grotto_mon GASTLY

; HIDDENGROTTO_ILEX_FOREST
	db 4, LEAF_STONE, 9
	hidden_grotto_mon PARAS
	hidden_grotto_mon ODDISH
	hidden_grotto_mon PSYDUCK
	hidden_grotto_mon PINECO

; HIDDENGROTTO_ROUTE_35
	db 4, SUN_STONE, 15
	hidden_grotto_mon SNUBBULL
	hidden_grotto_mon JIGGLYPUFF
	hidden_grotto_mon YANMA
	hidden_grotto_mon DITTO

; HIDDENGROTTO_ROUTE_36
	db 7, FIRE_STONE, 16
	hidden_grotto_mon STANTLER
	hidden_grotto_mon GROWLITHE
	hidden_grotto_mon VULPIX
	hidden_grotto_mon HOUNDOUR

; HIDDENGROTTO_CHERRYGROVE_BAY
	db 1, SHINY_STONE, LEVEL_FROM_BADGES + 0
	hidden_grotto_mon EXEGGCUTE
	hidden_grotto_mon SKIPLOOM
	hidden_grotto_mon SUNFLORA
	hidden_grotto_mon CORSOLA

; HIDDENGROTTO_VIOLET_OUTSKIRTS
	db 1, DUSK_STONE, LEVEL_FROM_BADGES - 0
	hidden_grotto_mon RATTATA, ALOLAN_FORM
	hidden_grotto_mon BELLSPROUT
	hidden_grotto_mon NOCTOWL
	hidden_grotto_mon MISDREAVUS

; HIDDENGROTTO_ROUTE_32_COAST
	db 3, WATER_STONE, LEVEL_FROM_BADGES + 3
	hidden_grotto_mon AIPOM
	hidden_grotto_mon WEEPINBELL
	hidden_grotto_mon RATICATE
	hidden_grotto_mon ARBOK, ARBOK_JOHTO_FORM

; HIDDENGROTTO_STORMY_BEACH
	db 3, WATER_STONE, LEVEL_FROM_BADGES + 3
	hidden_grotto_mon GRIMER, ALOLAN_FORM
	hidden_grotto_mon HAUNTER
	hidden_grotto_mon GOLBAT
	hidden_grotto_mon VENOMOTH

; HIDDENGROTTO_ROUTE_35_COAST
	db 3, THUNDERSTONE, LEVEL_FROM_BADGES + 3
	hidden_grotto_mon MILTANK
	hidden_grotto_mon TAUROS
	hidden_grotto_mon MAGNEMITE
	hidden_grotto_mon VOLTORB

; HIDDENGROTTO_RUINS_OF_ALPH
	db 14, MOON_STONE, 25
	hidden_grotto_mon SANDSHREW
	hidden_grotto_mon NATU
	hidden_grotto_mon QUAGSIRE
	hidden_grotto_mon SMEARGLE

; HIDDENGROTTO_ROUTE_47
	db 7, SHINY_STONE, LEVEL_FROM_BADGES + 0
	hidden_grotto_mon FARFETCH_D, GALARIAN_FORM
	hidden_grotto_mon CUBONE
	hidden_grotto_mon MACHOP
	hidden_grotto_mon LARVITAR

; HIDDENGROTTO_YELLOW_FOREST
	db 3, THUNDERSTONE, LEVEL_FROM_BADGES + 0
	hidden_grotto_mon LEDYBA
	hidden_grotto_mon SPINARAK
	hidden_grotto_mon MEOWTH
	hidden_grotto_mon PIKACHU

; HIDDENGROTTO_RUGGED_ROAD_NORTH
	db 2, FIRE_STONE, LEVEL_FROM_BADGES + 1
	hidden_grotto_mon GRAVELER
	hidden_grotto_mon GROWLITHE, HISUIAN_FORM
	hidden_grotto_mon SKARMORY
	hidden_grotto_mon DUNSPARCE

; HIDDENGROTTO_SNOWTOP_MOUNTAIN_INSIDE
	db 3, ICE_STONE, LEVEL_FROM_BADGES + 4
	hidden_grotto_mon SWINUB
	hidden_grotto_mon MR__MIME, GALARIAN_FORM
	hidden_grotto_mon DELIBIRD
	hidden_grotto_mon SNEASEL

; HIDDENGROTTO_ROUTE_42
	db 6, DUSK_STONE, 25
	hidden_grotto_mon MANKEY
	hidden_grotto_mon MARILL
	hidden_grotto_mon MACHOP
	hidden_grotto_mon GRAVELER

; HIDDENGROTTO_LAKE_OF_RAGE
	db 3, WATER_STONE, 26
	hidden_grotto_mon PIDGEOTTO
	hidden_grotto_mon GIRAFARIG
	hidden_grotto_mon FARFETCH_D
	hidden_grotto_mon FLAAFFY

; HIDDENGROTTO_BELLCHIME_TRAIL
	db 4, SUN_STONE, 20
	hidden_grotto_mon SENTRET
	hidden_grotto_mon HOOTHOOT
	hidden_grotto_mon MAGBY
	hidden_grotto_mon EEVEE

; HIDDENGROTTO_ROUTE_44
	db 2, LEAF_STONE, 34
	hidden_grotto_mon TANGELA
	hidden_grotto_mon LICKITUNG
	hidden_grotto_mon GLIGAR
	hidden_grotto_mon ONIX

; HIDDENGROTTO_ROUTE_45
	db 2, MOON_STONE, 36
	hidden_grotto_mon DONPHAN
	hidden_grotto_mon URSARING
	hidden_grotto_mon GLIGAR
	hidden_grotto_mon SKARMORY

; HIDDENGROTTO_ROUTE_46
	db 4, LEAF_STONE, 24
	hidden_grotto_mon PHANPY
	hidden_grotto_mon TEDDIURSA
	hidden_grotto_mon ZUBAT
	hidden_grotto_mon DUNSPARCE

; HIDDENGROTTO_SINJOH_RUINS
	db 3, ICE_STONE, LEVEL_FROM_BADGES + 5
	hidden_grotto_mon VULPIX, ALOLAN_FORM
	hidden_grotto_mon MR__MIME, GALARIAN_FORM
	hidden_grotto_mon GROWLITHE, HISUIAN_FORM
	hidden_grotto_mon SNEASEL, HISUIAN_FORM

; HIDDENGROTTO_SILVER_CAVE
	db 3, FIRE_STONE, 70
	hidden_grotto_mon RAPIDASH
	hidden_grotto_mon SNEASEL
	hidden_grotto_mon STEELIX
	hidden_grotto_mon PUPITAR

	assert_table_length NUM_HIDDEN_GROTTOES
