; Data tables that vary for forms list normal species data up to 255 (EGG),
; then continue with entries for these species+form combinations.

CosmeticSpeciesAndFormTable:
	table_width 2
	dp UNOWN,      UNOWN_B_FORM
	dp UNOWN,      UNOWN_C_FORM
	dp UNOWN,      UNOWN_D_FORM
	dp UNOWN,      UNOWN_E_FORM
	dp UNOWN,      UNOWN_F_FORM
	dp UNOWN,      UNOWN_G_FORM
	dp UNOWN,      UNOWN_H_FORM
	dp UNOWN,      UNOWN_I_FORM
	dp UNOWN,      UNOWN_J_FORM
	dp UNOWN,      UNOWN_K_FORM
	dp UNOWN,      UNOWN_L_FORM
	dp UNOWN,      UNOWN_M_FORM
	dp UNOWN,      UNOWN_N_FORM
	dp UNOWN,      UNOWN_O_FORM
	dp UNOWN,      UNOWN_P_FORM
	dp UNOWN,      UNOWN_Q_FORM
	dp UNOWN,      UNOWN_R_FORM
	dp UNOWN,      UNOWN_S_FORM
	dp UNOWN,      UNOWN_T_FORM
	dp UNOWN,      UNOWN_U_FORM
	dp UNOWN,      UNOWN_V_FORM
	dp UNOWN,      UNOWN_W_FORM
	dp UNOWN,      UNOWN_X_FORM
	dp UNOWN,      UNOWN_Y_FORM
	dp UNOWN,      UNOWN_Z_FORM
	dp UNOWN,      UNOWN_EXCLAMATION_FORM
	dp UNOWN,      UNOWN_QUESTION_FORM
	dp ARBOK,      ARBOK_KANTO_FORM
	dp ARBOK,      ARBOK_ORANGE_FORM
	dp ARBOK,      ARBOK_KOGA_FORM
	dp ARBOK,      ARBOK_AGATHA_FORM
	dp ARBOK,      ARBOK_ARIANA_FORM
	dp PIKACHU,    PIKACHU_FLY_FORM
	dp PIKACHU,    PIKACHU_SURF_FORM
	dp PIKACHU,    PIKACHU_RED_FORM
	dp PIKACHU,    PIKACHU_YELLOW_FORM
	dp PIKACHU,    PIKACHU_SPARK_FORM
	dp PICHU,      PICHU_SPIKY_EARED_FORM
	dp MAGIKARP,   MAGIKARP_SKELLY_FORM
	dp MAGIKARP,   MAGIKARP_CALICO1_FORM
	dp MAGIKARP,   MAGIKARP_CALICO2_FORM
	dp MAGIKARP,   MAGIKARP_CALICO3_FORM
	dp MAGIKARP,   MAGIKARP_TWO_TONE_FORM
	dp MAGIKARP,   MAGIKARP_ORCA_FORM
	dp MAGIKARP,   MAGIKARP_DAPPLES_FORM
	dp MAGIKARP,   MAGIKARP_TIGER_FORM
	dp MAGIKARP,   MAGIKARP_ZEBRA_FORM
	dp MAGIKARP,   MAGIKARP_STRIPE_FORM
	dp MAGIKARP,   MAGIKARP_BUBBLES_FORM
	dp MAGIKARP,   MAGIKARP_DIAMONDS_FORM
	dp MAGIKARP,   MAGIKARP_PATCHES_FORM
	dp MAGIKARP,   MAGIKARP_FOREHEAD1_FORM
	dp MAGIKARP,   MAGIKARP_MASK1_FORM
	dp MAGIKARP,   MAGIKARP_FOREHEAD2_FORM
	dp MAGIKARP,   MAGIKARP_MASK2_FORM
	dp MAGIKARP,   MAGIKARP_SAUCY_FORM
	dp MAGIKARP,   MAGIKARP_RAINDROP_FORM
	assert_table_length NUM_COSMETIC_FORMS
	; fallthrough

MACRO variant_visual_entry
	resolve_trainer_native_species \1, \2
	assert _tr_native_species == NUM_SPECIES + 1 + (@ - VariantVisualSpeciesAndFormTable) / 2
	dp \1, \2
ENDM

VariantVisualSpeciesAndFormTable:
	table_width 2
	variant_visual_entry GYARADOS,   GYARADOS_RED_FORM
	variant_visual_entry MEWTWO,     MEWTWO_ARMORED_FORM
	variant_visual_entry DUDUNSPARCE, DUDUNSPARCE_THREE_SEGMENT_FORM
	variant_visual_entry RATTATA,    ALOLAN_FORM
	variant_visual_entry RATICATE,   ALOLAN_FORM
	variant_visual_entry RAICHU,     ALOLAN_FORM
	variant_visual_entry SANDSHREW,  ALOLAN_FORM
	variant_visual_entry SANDSLASH,  ALOLAN_FORM
	variant_visual_entry VULPIX,     ALOLAN_FORM
	variant_visual_entry NINETALES,  ALOLAN_FORM
	variant_visual_entry DIGLETT,    ALOLAN_FORM
	variant_visual_entry DUGTRIO,    ALOLAN_FORM
	variant_visual_entry MEOWTH,     ALOLAN_FORM
	variant_visual_entry PERSIAN,    ALOLAN_FORM
	variant_visual_entry GEODUDE,    ALOLAN_FORM
	variant_visual_entry GRAVELER,   ALOLAN_FORM
	variant_visual_entry GOLEM,      ALOLAN_FORM
	variant_visual_entry GRIMER,     ALOLAN_FORM
	variant_visual_entry MUK,        ALOLAN_FORM
	variant_visual_entry EXEGGUTOR,  ALOLAN_FORM
	variant_visual_entry MAROWAK,    ALOLAN_FORM
	variant_visual_entry MEOWTH,     GALARIAN_FORM
	variant_visual_entry PONYTA,     GALARIAN_FORM
	variant_visual_entry RAPIDASH,   GALARIAN_FORM
	variant_visual_entry SLOWPOKE,   GALARIAN_FORM
	variant_visual_entry SLOWBRO,    GALARIAN_FORM
	variant_visual_entry FARFETCH_D, GALARIAN_FORM
	variant_visual_entry WEEZING,    GALARIAN_FORM
	variant_visual_entry MR__MIME,   GALARIAN_FORM
	variant_visual_entry ARTICUNO,   GALARIAN_FORM
	variant_visual_entry ZAPDOS,     GALARIAN_FORM
	variant_visual_entry MOLTRES,    GALARIAN_FORM
	variant_visual_entry SLOWKING,   GALARIAN_FORM
	variant_visual_entry CORSOLA,    GALARIAN_FORM
	variant_visual_entry GROWLITHE,  HISUIAN_FORM
	variant_visual_entry ARCANINE,   HISUIAN_FORM
	variant_visual_entry VOLTORB,    HISUIAN_FORM
	variant_visual_entry ELECTRODE,  HISUIAN_FORM
	variant_visual_entry TYPHLOSION, HISUIAN_FORM
	variant_visual_entry QWILFISH,   HISUIAN_FORM
	variant_visual_entry SNEASEL,    HISUIAN_FORM
	variant_visual_entry WOOPER,     PALDEAN_FORM
	variant_visual_entry TAUROS,     PALDEAN_FORM
	variant_visual_entry TAUROS,     TAUROS_PALDEAN_FIRE_FORM
	variant_visual_entry TAUROS,     TAUROS_PALDEAN_WATER_FORM
	variant_visual_entry URSALUNA,   URSALUNA_BLOODMOON_FORM
	assert_table_length NUM_VARIANT_FORMS

	db 0 ; end
