; Used by CheckSleepingTreeMon

AsleepTreeMons:
	table_width 1
	dr .Morn
	dr .Day
	dr .Nite
	dr .Eve
	assert_table_length NUM_DAYTIMES
.Nite
.Eve
	native_species_entry CATERPIE
	native_species_entry METAPOD
	native_species_entry BUTTERFREE
	native_species_entry WEEDLE
	native_species_entry KAKUNA
	native_species_entry BEEDRILL
	native_species_entry SPEAROW
	native_species_entry EKANS
	native_species_entry EXEGGCUTE
	native_species_entry LEDYBA
	dw 0 ; end

.Morn
.Day
	native_species_entry VENONAT
	native_species_entry HOOTHOOT
	native_species_entry NOCTOWL
	native_species_entry SPINARAK
	native_species_entry HERACROSS
	dw 0 ; end
