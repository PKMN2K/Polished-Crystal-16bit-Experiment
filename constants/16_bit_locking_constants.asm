; Reserved Pokémon conversion-table slots are declared here as they are needed.
const_def
DEF MON_LOCK_SAVE_MIGRATION_START EQU const_value
	const_skip PARTY_LENGTH + 2
DEF MON_LOCK_SAVE_MIGRATION_END EQU const_value

if const_value > MON_TABLE_LOCKED_ENTRIES
	fail "Too many locked Pokémon IDs"
endc
