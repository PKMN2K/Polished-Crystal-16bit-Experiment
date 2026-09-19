; Canonical identity records for mechanically distinct variants.
; Each record contains the native ID, root species ID, and presentation form.
MACRO native_variant_identity
	resolve_trainer_native_species \2, \3
	assert _tr_native_species == \1
	dw \1
	dw \2
	db \3
	assert \1 == NUM_SPECIES + (@ - NativeVariantIdentityTable) / 5
ENDM

NativeVariantIdentityTable:
	table_width 5
	native_variant_identity RED_GYARADOS, GYARADOS, GYARADOS_RED_FORM
	native_variant_identity ARMORED_MEWTWO, MEWTWO, MEWTWO_ARMORED_FORM
	native_variant_identity DUDUNSPARCE_THREE_SEGMENT, DUDUNSPARCE, DUDUNSPARCE_THREE_SEGMENT_FORM
	native_variant_identity ALOLAN_RATTATA, RATTATA, ALOLAN_FORM
	native_variant_identity ALOLAN_RATICATE, RATICATE, ALOLAN_FORM
	native_variant_identity ALOLAN_RAICHU, RAICHU, ALOLAN_FORM
	native_variant_identity ALOLAN_SANDSHREW, SANDSHREW, ALOLAN_FORM
	native_variant_identity ALOLAN_SANDSLASH, SANDSLASH, ALOLAN_FORM
	native_variant_identity ALOLAN_VULPIX, VULPIX, ALOLAN_FORM
	native_variant_identity ALOLAN_NINETALES, NINETALES, ALOLAN_FORM
	native_variant_identity ALOLAN_DIGLETT, DIGLETT, ALOLAN_FORM
	native_variant_identity ALOLAN_DUGTRIO, DUGTRIO, ALOLAN_FORM
	native_variant_identity ALOLAN_MEOWTH, MEOWTH, ALOLAN_FORM
	native_variant_identity ALOLAN_PERSIAN, PERSIAN, ALOLAN_FORM
	native_variant_identity ALOLAN_GEODUDE, GEODUDE, ALOLAN_FORM
	native_variant_identity ALOLAN_GRAVELER, GRAVELER, ALOLAN_FORM
	native_variant_identity ALOLAN_GOLEM, GOLEM, ALOLAN_FORM
	native_variant_identity ALOLAN_GRIMER, GRIMER, ALOLAN_FORM
	native_variant_identity ALOLAN_MUK, MUK, ALOLAN_FORM
	native_variant_identity ALOLAN_EXEGGUTOR, EXEGGUTOR, ALOLAN_FORM
	native_variant_identity ALOLAN_MAROWAK, MAROWAK, ALOLAN_FORM
	native_variant_identity GALARIAN_MEOWTH, MEOWTH, GALARIAN_FORM
	native_variant_identity GALARIAN_PONYTA, PONYTA, GALARIAN_FORM
	native_variant_identity GALARIAN_RAPIDASH, RAPIDASH, GALARIAN_FORM
	native_variant_identity GALARIAN_SLOWPOKE, SLOWPOKE, GALARIAN_FORM
	native_variant_identity GALARIAN_SLOWBRO, SLOWBRO, GALARIAN_FORM
	native_variant_identity GALARIAN_FARFETCH_D, FARFETCH_D, GALARIAN_FORM
	native_variant_identity GALARIAN_WEEZING, WEEZING, GALARIAN_FORM
	native_variant_identity GALARIAN_MR__MIME, MR__MIME, GALARIAN_FORM
	native_variant_identity GALARIAN_ARTICUNO, ARTICUNO, GALARIAN_FORM
	native_variant_identity GALARIAN_ZAPDOS, ZAPDOS, GALARIAN_FORM
	native_variant_identity GALARIAN_MOLTRES, MOLTRES, GALARIAN_FORM
	native_variant_identity GALARIAN_SLOWKING, SLOWKING, GALARIAN_FORM
	native_variant_identity GALARIAN_CORSOLA, CORSOLA, GALARIAN_FORM
	native_variant_identity HISUIAN_GROWLITHE, GROWLITHE, HISUIAN_FORM
	native_variant_identity HISUIAN_ARCANINE, ARCANINE, HISUIAN_FORM
	native_variant_identity HISUIAN_VOLTORB, VOLTORB, HISUIAN_FORM
	native_variant_identity HISUIAN_ELECTRODE, ELECTRODE, HISUIAN_FORM
	native_variant_identity HISUIAN_TYPHLOSION, TYPHLOSION, HISUIAN_FORM
	native_variant_identity HISUIAN_QWILFISH, QWILFISH, HISUIAN_FORM
	native_variant_identity HISUIAN_SNEASEL, SNEASEL, HISUIAN_FORM
	native_variant_identity PALDEAN_WOOPER, WOOPER, PALDEAN_FORM
	native_variant_identity PALDEAN_TAUROS_COMBAT, TAUROS, PALDEAN_FORM
	native_variant_identity PALDEAN_TAUROS_BLAZE, TAUROS, TAUROS_PALDEAN_FIRE_FORM
	native_variant_identity PALDEAN_TAUROS_AQUA, TAUROS, TAUROS_PALDEAN_WATER_FORM
	native_variant_identity BLOODMOON_URSALUNA, URSALUNA, URSALUNA_BLOODMOON_FORM
	assert_table_length NUM_NATIVE_SPECIES - NUM_SPECIES
