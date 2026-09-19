DEF BOXSAVE_USECURRENT EQU 1

SaveMenu:
	ld c, 4
	call SFXDelayFrames
	call LoadStandardMenuHeader
	farcall DisplaySaveInfoOnSave
	call SpeechTextbox
	call UpdateSprites
	call ApplyTilemap
	ld hl, WouldYouLikeToSaveTheGameText
	ld b, BANK(WouldYouLikeToSaveTheGameText)
	call MapTextbox
	call LoadMenuTextbox
	call YesNoBox
	ld a, [wMenuCursorY]
	dec a
	call CloseWindow
	and a
	jr nz, .refused
	call AskOverwriteSaveFile
	jr c, .refused
	call SetWRAMStateForSave
	call SavedTheGame
	call ClearWRAMStateAfterSave
	call ExitMenu
	and a
	ret

.refused
	call ExitMenu
	call CopyTilemapAtOnce
	scf
	ret

SaveAfterLinkTrade:
	call SetWRAMStateForSave
	call StageRTCTimeForSave
	call SavePokemonData
	call SavePokemonIndexTable
	call SaveChecksum
	call SaveBackupPokemonData
	call SaveBackupPokemonIndexTable
	call SaveBackupChecksum
	farcall BackupPartyMonMail
	call SaveRTC
	; fallthrough

ClearWRAMStateAfterSave:
	xor a
	ld [wGameLogicPaused], a
	ret

Link_SaveGame:
	call AskOverwriteSaveFile
	ret c
ForceGameSave:
	call SetWRAMStateForSave
	call SavedTheGame
	call ClearWRAMStateAfterSave
	and a
	ret

SetWRAMStateForSave:
	ld a, $1
	ld [wGameLogicPaused], a
	ret

AddHallOfFameEntry:
	call EnsureHallOfFameNativeSpecies
	ld a, BANK(sHallOfFame)
	call GetSRAMBank
	ld hl, sHallOfFame + HOF_LENGTH * (NUM_HOF_TEAMS - 1) - 1
	ld de, sHallOfFame + HOF_LENGTH * NUM_HOF_TEAMS - 1
	ld bc, HOF_LENGTH * (NUM_HOF_TEAMS - 1)
.loop
	ld a, [hld]
	ld [de], a
	dec de
	dec bc
	ld a, c
	or b
	jr nz, .loop
	ld hl, wOverworldMapBlocks
	ld de, sHallOfFame
	ld bc, HOF_LENGTH
	rst CopyBytes
	ld hl, sHallOfFameNativeSpecies + HOF_NATIVE_TEAM_LENGTH * (NUM_HOF_TEAMS - 1) - 1
	ld de, sHallOfFameNativeSpecies + HOF_NATIVE_TEAM_LENGTH * NUM_HOF_TEAMS - 1
	ld bc, HOF_NATIVE_TEAM_LENGTH * (NUM_HOF_TEAMS - 1)
.native_shift_loop
	ld a, [hld]
	ld [de], a
	dec de
	dec bc
	ld a, c
	or b
	jr nz, .native_shift_loop
	ld hl, wOverworldMapBlocks + 1
	ld de, sHallOfFameNativeSpecies
	call BuildHallOfFameNativeTeam
	jmp CloseSRAM

DEF HALL_OF_FAME_NATIVE_MAGIC EQU $16f0

EnsureHallOfFameNativeSpecies::
; Build the native-ID shadow for Hall of Fame data written by older versions.
	ld a, BANK(sHallOfFame)
	call GetSRAMBank
	ld a, [sHallOfFameNativeMagic]
	cp LOW(HALL_OF_FAME_NATIVE_MAGIC)
	jr nz, .migrate
	ld a, [sHallOfFameNativeMagic + 1]
	cp HIGH(HALL_OF_FAME_NATIVE_MAGIC)
	jp z, CloseSRAM
.migrate
	ld hl, sHallOfFame + 1
	ld de, sHallOfFameNativeSpecies
	ld c, NUM_HOF_TEAMS
.team_loop
	push bc
	call BuildHallOfFameNativeTeam
	inc hl ; skip the team terminator
	inc hl ; skip the next team's win count
	pop bc
	dec c
	jr nz, .team_loop
	ld a, LOW(HALL_OF_FAME_NATIVE_MAGIC)
	ld [sHallOfFameNativeMagic], a
	ld a, HIGH(HALL_OF_FAME_NATIVE_MAGIC)
	ld [sHallOfFameNativeMagic + 1], a
	jmp CloseSRAM

BuildHallOfFameNativeTeam:
; in: hl = first legacy Hall of Fame mon, de = native-ID shadow destination
; out: hl/de advanced past six records
	ld b, PARTY_LENGTH
.mon_loop
	push bc
	push hl
	push de
	ld a, [hl]
	and a
	jr z, .empty
	cp -1
	jr z, .empty
	ld c, a
	ld de, 4 ; species to encoded form/personality high byte
	add hl, de
	ld b, [hl]
	call GetSpeciesAndFormIndex
	inc bc
	ld a, c
	pop de
	ld [de], a
	inc de
	ld a, b
	ld [de], a
	inc de
	jr .next
.empty
	pop de
	xor a
	ld [de], a
	inc de
	ld [de], a
	inc de
.next
	pop hl
	ld bc, HOF_MON_LENGTH
	add hl, bc
	pop bc
	dec b
	jr nz, .mon_loop
	ret

AskOverwriteSaveFile:
	ld a, [wSaveFileExists]
	and a
	jr z, .erase
	call CompareLoadedAndSavedPlayerID
	jr z, .ok
if !DEF(DEBUG)
	ld a, [wOptions1]
	push af
	and ~(TEXT_DELAY_MASK | AUTOSCROLL_MASK)
	or SLOW_TEXT
	ld [wOptions1], a
endc
	ld hl, AnotherSaveFileText
	ld b, BANK(AnotherSaveFileText)
	call MapTextbox
	call LoadMenuTextbox
if !DEF(DEBUG)
	call NoYesBox
	pop af
	ld [wOptions1], a
	ld a, [wMenuCursorY]
	dec a
	call CloseWindow ; preserves af
	jr z, .refused
else
	call YesNoBox
	ld a, [wMenuCursorY]
	dec a
	call CloseWindow ; preserves af
	jr nz, .refused
endc
.erase
	call ErasePreviousSave
.ok
	and a
	ret

.refused
	scf
	ret

CompareLoadedAndSavedPlayerID:
	push hl
	push de
	push bc
	ld a, BANK(sPlayerData)
	call GetSRAMBank
	ld hl, sPlayerData + (wPlayerID - wPlayerData)
	ld a, [hli]
	ld c, [hl]
	ld b, a
	call CloseSRAM
	ld a, [wPlayerID]
	cp b
	jr nz, .done
	ld a, [wPlayerID + 1]
	cp c
.done
	jmp PopBCDEHL

SavedTheGame:
	call SaveGameData
	call SaveCurrentVersion
	; <PLAYER> saved the game!
	ld hl, SavedTheGameText
	call PrintText
	ld de, SFX_SAVE
	call WaitPlaySFX
	jmp WaitSFX

SaveGameData::
	ldh a, [hVBlank]
	push af
	ld a, 2
	ldh [hVBlank], a
	dec a ; ld a, TRUE
	ld [wSaveFileExists], a
	call StageRTCTimeForSave
	call ValidateSave
	call SaveOptions
	call SavePlayerData
	call SavePokemonData
	call SavePokemonIndexTable

	; This function is never called mid-Battle Tower (only in the beginning).
	; So this is always a safe action, and gets rid of potential old BT state
	; from a previous save. Done before checksum generation in case user resets
	; mid-save.
	ld a, BANK(sBattleTowerChallengeState)
	call GetSRAMBank
	xor a
	ld [sBattleTowerChallengeState], a

	; At this point, there is no longer any harm in setting this. We can't set
	; it earlier, because it might confuse the load routine into using bad
	; box/mail data, and we can't set it later because we need to set it
	; before our main save copy is valid.
	ld a, 1
	call SetSavePhase

	call SaveChecksum
	call WriteBackupSave
	call SaveRTC
	call CloseSRAM ; just in case
	pop af
	ldh [hVBlank], a
	ret

WriteBackupSave:
; Runs after saving the main copy. Writes the "pseudo-WRAM" copies of storage
; and mail, then creates the backup save. This process is automatically run
; on game load if we have a valid main save but not a backup save.
	; Save storage and mail to backup
	farcall BackupPartyMonMail
	call SaveStorageSystem

	; Save the backup copy of game data.
	call ValidateBackupSave
	call SaveBackupOptions
	call SaveBackupPlayerData
	call SaveBackupPokemonData
	call SaveBackupPokemonIndexTable
	call SaveBackupChecksum

	; Finished saving.
	xor a
	call SetSavePhase
	jmp CloseSRAM

LoadStorageSystem:
; Copy backup storage system to active.
	ld hl, sBackupNewBox1
	ld de, sNewBox1
	call CopyStorageSystem

	; Initialize allocation information.
	farjp FlushStorageSystem

SaveStorageSystem:
; Copy active storage system to backup.
	ld hl, sNewBox1
	ld de, sBackupNewBox1
	; fallthrough
CopyStorageSystem:
	ld a, BANK(sNewBox1)
	call GetSRAMBank
	ld bc, sNewBoxEnd - sNewBox1
	rst CopyBytes
	jmp CloseSRAM

HallOfFame_InitSaveIfNeeded:
	ld a, [wSavedAtLeastOnce]
	and a
	ret nz
	; fallthrough

ErasePreviousSave:
	call EraseHallOfFame
	call EraseLinkBattleStats
	call EraseBattleTowerStatus
	ld a, $1
	ld [wSavedAtLeastOnce], a
	ret

EraseLinkBattleStats:
	ld a, BANK(sLinkBattleStats)
	call GetSRAMBank
	ld hl, sLinkBattleStats
	ld bc, sLinkBattleStatsEnd - sLinkBattleStats
	xor a
	rst ByteFill
	jmp CloseSRAM

EraseHallOfFame:
	ld a, BANK(sHallOfFame)
	call GetSRAMBank
	ld hl, sHallOfFame
	ld bc, sHallOfFameNativeMagic + 2 - sHallOfFame
	xor a
	rst ByteFill
	ld a, LOW(HALL_OF_FAME_NATIVE_MAGIC)
	ld [sHallOfFameNativeMagic], a
	ld a, HIGH(HALL_OF_FAME_NATIVE_MAGIC)
	ld [sHallOfFameNativeMagic + 1], a
	jmp CloseSRAM

EraseBattleTowerStatus:
	ld a, BANK(sBattleTowerChallengeState)
	call GetSRAMBank
	xor a
	ld [sBattleTowerChallengeState], a
	jmp CloseSRAM

ValidateSave:
	ld a, BANK(sCheckValue1)
	call GetSRAMBank
	ld a, SAVE_CHECK_VALUE_1
	ld [sCheckValue1], a
	ld a, SAVE_CHECK_VALUE_2
	ld [sCheckValue2], a
	jmp CloseSRAM

SaveOptions:
	ld a, BANK(sOptions)
	call GetSRAMBank
	ld hl, wOptions
	ld de, sOptions
	ld bc, wOptionsEnd - wOptions
	rst CopyBytes
	ld a, [wOptions3]
	ld [sOptions3], a
	ld a, [wOptions1]
	and ~(1 << NO_TEXT_SCROLL)
	ld [sOptions + wOptions1 - wOptions], a
	jmp CloseSRAM

SavePlayerData:
	ld a, BANK(sPlayerData)
	call GetSRAMBank
	ld hl, wPlayerData
	ld de, sPlayerData
	ld bc, wPlayerDataEnd - wPlayerData
	rst CopyBytes
	ld hl, wCurMapData
	ld de, sMapData
	ld bc, wCurMapDataEnd - wCurMapData
	rst CopyBytes
	jmp CloseSRAM

SavePokemonData:
	ld a, BANK(sPokemonData)
	call GetSRAMBank
	ld hl, wPokemonData
	ld de, sPokemonData
	ld bc, wPokemonDataEnd - wPokemonData
	rst CopyBytes
	jmp CloseSRAM

; Bumped when roaming Pokémon became persistent transient IDs. Saves made by
; earlier migration checkpoints are upgraded through the same legacy path.
DEF POKEMON_INDEX_TABLE_MAGIC EQU $16bd

SavePokemonIndexTable:
	ld a, BANK(sPokemonIndexTable)
	call GetSRAMBank
	ld a, LOW(POKEMON_INDEX_TABLE_MAGIC)
	ld [sPokemonIndexTableMagic], a
	ld a, HIGH(POKEMON_INDEX_TABLE_MAGIC)
	ld [sPokemonIndexTableMagic + 1], a
	ldh a, [rSVBK]
	push af
	ld a, BANK(wPokemonIndexTable)
	ldh [rSVBK], a
	farcall PokemonTableGarbageCollection
	ld hl, wPokemonIndexTable
	ld de, sPokemonIndexTable
	ld bc, wPokemonIndexTableEnd - wPokemonIndexTable
	rst CopyBytes
	pop af
	ldh [rSVBK], a
	jmp CloseSRAM

SaveChecksum:
	ld hl, sGameData
	ld bc, sGameDataEnd - sGameData
	ld a, BANK(sGameData)
	call GetSRAMBank
	call Checksum
	ld a, e
	ld [sChecksum + 0], a
	ld a, d
	ld [sChecksum + 1], a
	jmp CloseSRAM

ValidateBackupSave:
	ld a, BANK(sBackupCheckValue1)
	call GetSRAMBank
	ld a, SAVE_CHECK_VALUE_1
	ld [sBackupCheckValue1], a
	ld a, SAVE_CHECK_VALUE_2
	ld [sBackupCheckValue2], a
	jmp CloseSRAM

SaveBackupOptions:
	ld a, BANK(sBackupOptions)
	call GetSRAMBank
	ld hl, wOptions
	ld de, sBackupOptions
	ld bc, wOptionsEnd - wOptions
	rst CopyBytes
	ld a, [wOptions3]
	ld [sBackupOptions3], a
	jmp CloseSRAM

SaveBackupPlayerData:
	ld a, BANK(sBackupPlayerData)
	call GetSRAMBank
	ld hl, wPlayerData
	ld de, sBackupPlayerData
	ld bc, wPlayerDataEnd - wPlayerData
	rst CopyBytes
	ld hl, wCurMapData
	ld de, sBackupMapData
	ld bc, wCurMapDataEnd - wCurMapData
	rst CopyBytes
	jmp CloseSRAM

SaveBackupPokemonData:
	ld a, BANK(sBackupPokemonData)
	call GetSRAMBank
	ld hl, wPokemonData
	ld de, sBackupPokemonData
	ld bc, wPokemonDataEnd - wPokemonData
	rst CopyBytes
	jmp CloseSRAM

SaveBackupPokemonIndexTable:
	ld a, BANK(sBackupPokemonIndexTable)
	call GetSRAMBank
	ld a, LOW(POKEMON_INDEX_TABLE_MAGIC)
	ld [sBackupPokemonIndexTableMagic], a
	ld a, HIGH(POKEMON_INDEX_TABLE_MAGIC)
	ld [sBackupPokemonIndexTableMagic + 1], a
	ldh a, [rSVBK]
	push af
	ld a, BANK(wPokemonIndexTable)
	ldh [rSVBK], a
	ld hl, wPokemonIndexTable
	ld de, sBackupPokemonIndexTable
	ld bc, wPokemonIndexTableEnd - wPokemonIndexTable
	rst CopyBytes
	pop af
	ldh [rSVBK], a
	jmp CloseSRAM

SaveBackupChecksum:
	ld hl, sBackupGameData
	ld bc, sBackupGameDataEnd - sBackupGameData
	ld a, BANK(sBackupGameData)
	call GetSRAMBank
	call Checksum
	ld a, e
	ld [sBackupChecksum + 0], a
	ld a, d
	ld [sBackupChecksum + 1], a
	jmp CloseSRAM

WasMidSaveAborted:
; Returns z if the system was reset mid-saving.
	ld a, BANK(sWritingBackup)
	call GetSRAMBank
	ld a, [sWritingBackup]
	dec a
	jmp CloseSRAM

SetSavePhase:
; set current save phase: 1 (saving), 0 (not saving).
	push af
	ld a, BANK(sWritingBackup)
	call GetSRAMBank
	pop af
	ld [sWritingBackup], a
	jmp CloseSRAM

TryLoadSaveFile:
	call VerifyGameVersion
	call VerifyChecksum
	jr nz, .backup
	call LoadPlayerData
	call LoadPokemonData
	call LoadPokemonIndexTable

	; If a mid-save was aborted but main save data is good, finish it.
	call WasMidSaveAborted
	call z, WriteBackupSave
	farcall RestorePartyMonMail
	call LoadStorageSystem

	; Just in case
	call WriteBackupSave
	and a
	ret

.backup
	call VerifyBackupChecksum
	jr nz, .corrupt
	call LoadBackupPlayerData
	call LoadBackupPokemonData
	call LoadBackupPokemonIndexTable
	farcall RestorePartyMonMail
	call LoadStorageSystem
	call SaveGameData
	and a
	ret

.corrupt
	ld a, [wOptions1]
	push af
	set NO_TEXT_SCROLL, a
	ld [wOptions1], a
	ld hl, SaveFileCorruptedText
	call PrintText
	pop af
	ld [wOptions1], a
	scf
	ret

TryLoadSaveData:
	xor a
	ld [wSaveFileExists], a
	call CheckPrimarySaveFile
	ld a, [wSaveFileExists]
	and a
	jr z, .backup

	ld a, BANK(sPlayerData)
	call GetSRAMBank
	ld hl, sPlayerData + wStartDay - wPlayerData
	ld de, wStartDay
	ld bc, 8
	rst CopyBytes
	ld hl, sPlayerData + wStatusFlags - wPlayerData
	ld de, wStatusFlags
	ld a, [hl]
	ld [de], a
	jmp CloseSRAM

.backup
	call CheckBackupSaveFile
	ld a, [wSaveFileExists]
	and a
	jr z, .corrupt

	ld a, BANK(sBackupPlayerData)
	call GetSRAMBank
	ld hl, sBackupPlayerData + wStartDay - wPlayerData
	ld de, wStartDay
	ld bc, 8
	rst CopyBytes
	ld hl, sBackupPlayerData + wStatusFlags - wPlayerData
	ld de, wStatusFlags
	ld a, [hl]
	ld [de], a
	jmp CloseSRAM

.corrupt
	ld hl, DefaultOptions
	assert wOptions3 < wOptions ; for legacy reasons
	ld de, wOptions3
	ld bc, wOptionsEnd - wOptions3
	rst CopyBytes
	jmp PanicResetClock

INCLUDE "data/options/default_options.asm"

CheckPrimarySaveFile:
	ld a, BANK(sCheckValue1)
	call GetSRAMBank
	ld a, [sCheckValue1]
	cp SAVE_CHECK_VALUE_1
	jr z, .yes
	cp SAVE_CHECK_VALUE_1_OLD
	jr nz, .nope
.yes
	ld a, [sCheckValue2]
	cp SAVE_CHECK_VALUE_2
	jr nz, .nope
	ld hl, sOptions
	ld de, wOptions
	ld bc, wOptionsEnd - wOptions
	rst CopyBytes
	ld a, [sOptions3]
	ld [wOptions3], a
	call CloseSRAM
	ld a, $1
	ld [wSaveFileExists], a

.nope
	jmp CloseSRAM

CheckBackupSaveFile:
	ld a, BANK(sBackupCheckValue1)
	call GetSRAMBank
	ld a, [sBackupCheckValue1]
	cp SAVE_CHECK_VALUE_1
	jr z, .yes
	cp SAVE_CHECK_VALUE_1_OLD
	jr nz, .nope
.yes
	ld a, [sBackupCheckValue2]
	cp SAVE_CHECK_VALUE_2
	jr nz, .nope
	ld hl, sBackupOptions
	ld de, wOptions
	ld bc, wOptionsEnd - wOptions
	rst CopyBytes
	ld a, [sBackupOptions3]
	ld [wOptions3], a
	ld a, $2
	ld [wSaveFileExists], a

.nope
	jmp CloseSRAM

LoadPlayerData:
	ld a, BANK(sPlayerData)
	call GetSRAMBank
	ld hl, sPlayerData
	ld de, wPlayerData
	ld bc, wPlayerDataEnd - wPlayerData
	rst CopyBytes
	ld hl, sMapData
	ld de, wCurMapData
	ld bc, wCurMapDataEnd - wCurMapData
	rst CopyBytes
	jmp CloseSRAM

LoadPokemonData:
	ld a, BANK(sPokemonData)
	call GetSRAMBank
	ld hl, sPokemonData
	ld de, wPokemonData
	ld bc, wPokemonDataEnd - wPokemonData
	rst CopyBytes
	jmp CloseSRAM

LoadPokemonIndexTable:
	ld a, BANK(sPokemonIndexTable)
	call GetSRAMBank
	ld a, [sPokemonIndexTableMagic]
	cp LOW(POKEMON_INDEX_TABLE_MAGIC)
	jr nz, .missing
	ld a, [sPokemonIndexTableMagic + 1]
	cp HIGH(POKEMON_INDEX_TABLE_MAGIC)
	jr nz, .missing
	ld hl, sPokemonIndexTable
	jr LoadPokemonIndexTableFromHL
.missing
	ld hl, 0
	call LoadPokemonIndexTableFromHL
	farjp MigrateLegacyRoamMons

LoadBackupPokemonIndexTable:
	ld a, BANK(sBackupPokemonIndexTable)
	call GetSRAMBank
	ld a, [sBackupPokemonIndexTableMagic]
	cp LOW(POKEMON_INDEX_TABLE_MAGIC)
	jr nz, .missing
	ld a, [sBackupPokemonIndexTableMagic + 1]
	cp HIGH(POKEMON_INDEX_TABLE_MAGIC)
	jr nz, .missing
	ld hl, sBackupPokemonIndexTable
	jr LoadPokemonIndexTableFromHL
.missing
	ld hl, 0
	call LoadPokemonIndexTableFromHL
	farjp MigrateLegacyRoamMons

LoadPokemonIndexTableFromHL:
	ldh a, [rSVBK]
	push af
	ld a, BANK(wPokemonIndexTable)
	ldh [rSVBK], a
	ld de, wPokemonIndexTable
	ld bc, wPokemonIndexTableEnd - wPokemonIndexTable
	ld a, h
	or l
	jr z, .clear
	rst CopyBytes
	jr .done
.clear
	ld h, d
	ld l, e
	xor a
	rst ByteFill
.done
	pop af
	ldh [rSVBK], a
	jmp CloseSRAM

VerifyChecksum:
	ld hl, sGameData
	ld bc, sGameDataEnd - sGameData
	ld a, BANK(sGameData)
	call GetSRAMBank
	call Checksum
	ld a, [sChecksum + 0]
	cp e
	jr nz, .fail
	ld a, [sChecksum + 1]
	cp d
.fail
	push af
	call CloseSRAM
	pop af
	ret

LoadBackupPlayerData:
	ld a, BANK(sBackupPlayerData)
	call GetSRAMBank
	ld hl, sBackupPlayerData
	ld de, wPlayerData
	ld bc, wPlayerDataEnd - wPlayerData
	rst CopyBytes
	ld hl, sBackupMapData
	ld de, wCurMapData
	ld bc, wCurMapDataEnd - wCurMapData
	rst CopyBytes
	jmp CloseSRAM

LoadBackupPokemonData:
	ld a, BANK(sBackupPokemonData)
	call GetSRAMBank
	ld hl, sBackupPokemonData
	ld de, wPokemonData
	ld bc, wPokemonDataEnd - wPokemonData
	rst CopyBytes
	jmp CloseSRAM

VerifyBackupChecksum:
	ld hl, sBackupGameData
	ld bc, sBackupGameDataEnd - sBackupGameData
	ld a, BANK(sBackupGameData)
	call GetSRAMBank
	call Checksum
	ld a, [sBackupChecksum + 0]
	cp e
	jr nz, .fail
	ld a, [sBackupChecksum + 1]
	cp d
.fail
	push af
	call CloseSRAM
	pop af
	ret

Checksum:
	ld de, 0
.loop
	ld a, [hli]
	; de += a
	add e
	ld e, a
	adc d
	sub e
	ld d, a
	dec bc
	ld a, b
	or c
	jr nz, .loop
	ret

WouldYouLikeToSaveTheGameText:
	; Would you like to save the game?
	text_farend _WouldYouLikeToSaveTheGameText
SavedTheGameText:
	; saved the game.
	text_farend _SavedTheGameText
AnotherSaveFileText:
	; There is another save file. Is it OK to overwrite?
	text_farend _AnotherSaveFileText
SaveFileCorruptedText:
	; The save file is corrupted!
	text_farend _SaveFileCorruptedText
VerifyGameVersion:
; Verify that the current game version matches the one in the save file.
	; [wStringBuffer1:2] = SAVE_VERSION; hl = wStringBuffer1
	ld hl, wStringBuffer1
	ld a, HIGH(SAVE_VERSION)
	ld [hli], a
	ld a, LOW(SAVE_VERSION)
	ld [hld], a

	; [wStringBuffer2:2] = [sSaveVersion:2]; de = wStringBuffer2
	ld a, BANK(sSaveVersion)
	call GetSRAMBank
	ld de, wStringBuffer2 + 1
	push hl
	ld hl, sSaveVersion + 1
	ld a, [hld]
	ld [de], a
	dec de
	ld a, [hl]
	ld [de], a
	pop hl
	call CloseSRAM

	; needs upgrade if [hl:2] != [de:2]
	ld a, [de]
	cp [hl]
	jr nz, .needs_upgrade
	inc hl
	inc de
	ld a, [de]
	cp [hl]
	ret z

.needs_upgrade
	call ClearScreen
	hlcoord 0, 0
	ld de, .SaveUpgradeScreen
	rst PlaceString
	ld de, wStringBuffer1
	hlcoord 14, 11
	lb bc, PRINTNUM_LEADINGZEROS | 2, 5
	call PrintNum
	ld de, wStringBuffer2
	hlcoord 14, 13
	lb bc, PRINTNUM_LEADINGZEROS | 2, 5
	call PrintNum

.infinite_loop
	halt
	nop
	jr .infinite_loop

.SaveUpgradeScreen:
	text  "Your save file does"
	next1 "not match the game"
	next1 "version of this ROM."
	next1 ""
	next1 "If your save is old,"
	next1 "please consult the"
	next1 "documentation for"
	next1 "this game release"
	next1 "for instructions to"
	next1 "upgrade your save."
	next1 ""
	next1 "Game version:"
	next1 ""
	next1 "Save version:"
	done

SaveCurrentVersion:
; Writes current save version into the save.
	ld a, BANK(sSaveVersion)
	call GetSRAMBank
	ld a, HIGH(SAVE_VERSION)
	ld [sSaveVersion], a
	ld a, LOW(SAVE_VERSION)
	ld [sSaveVersion + 1], a
	jmp CloseSRAM
