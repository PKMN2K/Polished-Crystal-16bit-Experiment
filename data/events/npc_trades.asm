MACRO npc_trade_mon
	resolve_trainer_native_species \1, \2
	dw _tr_native_species
	db \2
ENDM

NPCTrades:
	table_width NPCTRADE_STRUCT_LENGTH
; NPC_TRADE_MIKE in Goldenrod City
	db TRADE_DIALOGSET_COLLECTOR
	npc_trade_mon ABRA, NO_FORM  ; wants
	npc_trade_mon MACHOP, FEMALE ; gives
	rawchar "Muscle@@@@@"
	db $EE, $EE, $EE, HIDDEN_ABILITY | NAT_ATK_UP_SATK_DOWN,  LEVEL_BALL,   SITRUS_BERRY
	dw 37460
	rawchar "Mike@@@", $00
; NPC_TRADE_KYLE in Violet City
	db TRADE_DIALOGSET_COLLECTOR
	npc_trade_mon POLIWAG, NO_FORM ; wants
	npc_trade_mon VOLTORB, MALE    ; gives
	rawchar "Mimic@@@@@@"
	db $EE, $EE, $EE, HIDDEN_ABILITY | NAT_SPE_UP_DEF_DOWN,   PREMIER_BALL, PERSIM_BERRY
	dw 48926
	rawchar "Kyle@@@", $00
; NPC_TRADE_TIM in Olivine City
	db TRADE_DIALOGSET_HAPPY
	npc_trade_mon STEELIX, NO_FORM ; wants
	npc_trade_mon KANGASKHAN, MALE ; gives
	rawchar "Joey@@@@@@@"
	db $EE, $EE, $EE, HIDDEN_ABILITY | NAT_ATK_UP_SPE_DOWN,   HEAVY_BALL,   SILK_SCARF
	dw 29189
	rawchar "Tim@@@@", $00
; NPC_TRADE_EMY in Blackthorn City
	db TRADE_DIALOGSET_GIRL
	npc_trade_mon JYNX, NO_FORM    ; wants
	npc_trade_mon MR__MIME, FEMALE ; gives
	rawchar "Doris@@@@@@"
	db $EE, $EE, $EE, HIDDEN_ABILITY | NAT_SPE_UP_ATK_DOWN,   LOVE_BALL,    FAIRYFEATHER
	dw 00283
	rawchar "Emy@@@@", $00
; NPC_TRADE_CHRIS in Pewter City
	db TRADE_DIALOGSET_NEWBIE
	npc_trade_mon PINSIR, NO_FORM ; wants
	npc_trade_mon HERACROSS, MALE ; gives
	rawchar "Paul@@@@@@@"
	db $EE, $EE, $EE, HIDDEN_ABILITY | NAT_SPE_UP_SATK_DOWN,  PARK_BALL,    SILVERPOWDER
	dw 15616
	rawchar "Chris@@", $00
; NPC_TRADE_KIM in Route 14
	db TRADE_DIALOGSET_GIRL
	npc_trade_mon WOBBUFFET, NO_FORM ; wants
	npc_trade_mon CHANSEY, FEMALE    ; gives
	rawchar "Chance@@@@@"
	db $EE, $EE, $EE, HIDDEN_ABILITY | NAT_SDEF_UP_ATK_DOWN,  HEAL_BALL,    LUCKY_EGG
	dw 26491
	rawchar "Kim@@@@", $00
; NPC_TRADE_JACQUES in Goldenrod Harbor
	db TRADE_DIALOGSET_HAPPY
	npc_trade_mon TENTACOOL, NO_FORM ; wants
	npc_trade_mon GRIMER, FEMALE     ; gives
	rawchar "Gail@@@@@@@"
	db $EE, $EE, $EE, HIDDEN_ABILITY | NAT_SDEF_UP_SATK_DOWN, LURE_BALL,    EVIOLITE
	dw 50082
	rawchar "Jacques", $00
; NPC_TRADE_HARI in Ecruteak City
	db TRADE_DIALOGSET_COLLECTOR
	npc_trade_mon FARFETCH_D, NO_FORM ; wants
	npc_trade_mon DODUO, MALE         ; gives
	rawchar "Clarence@@@"
	db $EE, $EE, $EE, HIDDEN_ABILITY | NAT_SPE_UP_DEF_DOWN,   FAST_BALL,    GOLD_LEAF
	dw 43972
	rawchar "Hari@@@", $00
; NPC_TRADE_JEEVES
	db TRADE_DIALOGSET_COLLECTOR
	npc_trade_mon PONYTA, NO_FORM               ; wants
	npc_trade_mon WEEZING, GALARIAN_FORM | MALE ; gives
	rawchar "Batty@@@@@@"
	db $EE, $EE, $EE, HIDDEN_ABILITY | NAT_DEF_UP_ATK_DOWN,   DREAM_BALL,   CHARCOAL
	dw 08922
	rawchar "Jeeves@", $00
	assert_table_length NUM_NPC_TRADES
