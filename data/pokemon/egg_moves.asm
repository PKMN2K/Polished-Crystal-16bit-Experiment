SECTION "Egg Moves", ROMX

INCLUDE "data/pokemon/egg_move_pointers.asm"

EggSpeciesMoves::

BulbasaurEggSpeciesMoves:
	native_species_form BULBASAUR, PLAIN_FORM
if DEF(NATIVE_MOVE_TEST)
	dw WIDE_TEST_MOVE
else
	dw CHARM
endc
	dw PETAL_DANCE
	dw LIGHT_SCREEN
	dw SAFEGUARD
	dw POWER_WHIP
	dw $ffff

CharmanderEggSpeciesMoves:
	native_species_form CHARMANDER, PLAIN_FORM
	dw ANCIENTPOWER
	dw BELLY_DRUM
	dw BITE
	dw CRUNCH
	dw DRAGON_DANCE
	dw DRAGONBREATH
	dw FLARE_BLITZ
	dw OUTRAGE
	dw $ffff

SquirtleEggSpeciesMoves:
	native_species_form SQUIRTLE, PLAIN_FORM
	dw CONFUSION
	dw CRUNCH
	dw FORESIGHT
	dw HAZE
	dw MIRROR_COAT
	dw AQUA_JET
	dw $ffff

CaterpieEggSpeciesMoves:
	native_species_form CATERPIE, PLAIN_FORM
	dw $ffff

WeedleEggSpeciesMoves:
	native_species_form WEEDLE, PLAIN_FORM
	dw $ffff

PidgeyEggSpeciesMoves:
	native_species_form PIDGEY, PLAIN_FORM
	dw PECK
	dw FEINT_ATTACK
	dw FORESIGHT
	dw PURSUIT
	dw AIR_SLASH
	dw STEEL_WING
	dw CHARM
	dw EXTREMESPEED
	dw BRAVE_BIRD
	dw $ffff

RattataPlainEggSpeciesMoves:
	native_species_form RATTATA, PLAIN_FORM
	dw FURY_STRIKES
	dw REVERSAL
	dw SCREECH
	dw BITE
	dw COUNTER
	dw $ffff

RattataAlolanEggSpeciesMoves:
	native_species_form RATTATA, ALOLAN_FORM
	dw FURY_STRIKES
	dw REVERSAL
	dw SCREECH
	dw BITE
	dw COUNTER
	dw $ffff

SpearowEggSpeciesMoves:
	native_species_form SPEAROW, PLAIN_FORM
	dw ASTONISH
	dw FEINT_ATTACK
	dw QUICK_ATTACK
	dw SCARY_FACE
	dw TRI_ATTACK
	dw $ffff

EkansEggSpeciesMoves:
	native_species_form EKANS, NO_FORM
	dw CRUNCH
	dw DISABLE
	dw PURSUIT
	dw SCARY_FACE
	dw $ffff

SandshrewPlainEggSpeciesMoves:
	native_species_form SANDSHREW, PLAIN_FORM
	dw METAL_CLAW
	dw RAPID_SPIN
	dw SAFEGUARD
	dw COUNTER
	dw NIGHT_SLASH
	dw $ffff

SandshrewAlolanEggSpeciesMoves:
	native_species_form SANDSHREW, ALOLAN_FORM
	dw AMNESIA
	dw RAPID_SPIN
	dw SAFEGUARD
	dw REVERSAL ; Flail → similar move
	dw ICICLE_CRASH
	dw ICICLE_SPEAR
	dw NIGHT_SLASH
	dw $ffff

NidoranFEggSpeciesMoves:
	native_species_form NIDORAN_F, PLAIN_FORM
	dw CHARM
	dw DISABLE
	dw FOCUS_ENERGY
	dw PURSUIT
	dw SUPERSONIC
	dw TAKE_DOWN
	dw $ffff

NidoranMEggSpeciesMoves:
	native_species_form NIDORAN_M, PLAIN_FORM
	dw AMNESIA
	dw CONFUSION
	dw DISABLE
	dw SUPERSONIC
	dw TAKE_DOWN
	dw CALM_MIND
	dw COUNTER
	dw $ffff

VulpixPlainEggSpeciesMoves:
	native_species_form VULPIX, PLAIN_FORM
	dw FLAME_CHARGE
	dw DISABLE
	dw FLARE_BLITZ
	dw HYPNOSIS
	dw FEINT_ATTACK
	dw EXTRASENSORY
	dw CHARM
	dw ENERGY_BALL
	dw ROAR
	dw $ffff

VulpixAlolanEggSpeciesMoves:
	native_species_form VULPIX, ALOLAN_FORM
	dw DISABLE
	dw BLIZZARD
	dw HYPNOSIS
	dw FEINT_ATTACK
	dw EXTRASENSORY
	dw CHARM
	dw ICE_BEAM
	dw ROAR
	dw $ffff

ZubatEggSpeciesMoves:
	native_species_form ZUBAT, PLAIN_FORM
	dw FEINT_ATTACK
	dw GUST
	dw HYPNOSIS
	dw NASTY_PLOT
	dw PURSUIT
	dw QUICK_ATTACK
	dw ZEN_HEADBUTT
	dw BRAVE_BIRD
	dw $ffff

OddishEggSpeciesMoves:
	native_species_form ODDISH, PLAIN_FORM
	dw CHARM
	dw RAZOR_LEAF
	dw HEALINGLIGHT
	dw SWORDS_DANCE
	dw $ffff

ParasEggSpeciesMoves:
	native_species_form PARAS, PLAIN_FORM
	dw AGILITY
	dw LEECH_SEED
	dw METAL_CLAW
	dw PSYBEAM
	dw PURSUIT
	dw SCREECH
	dw SHADOW_CLAW
	dw $ffff

VenonatEggSpeciesMoves:
	native_species_form VENONAT, PLAIN_FORM
	dw AGILITY
	dw BATON_PASS
	dw HEALINGLIGHT
	dw SCREECH
	dw TOXIC_SPIKES
	dw $ffff

DiglettPlainEggSpeciesMoves:
	native_species_form DIGLETT, PLAIN_FORM
	dw ANCIENTPOWER
	dw FEINT_ATTACK
	dw HEADBUTT
	dw PURSUIT
	dw REVERSAL
	dw SCREECH
	dw $ffff

DiglettAlolanEggSpeciesMoves:
	native_species_form DIGLETT, ALOLAN_FORM
	dw ANCIENTPOWER
	dw FEINT_ATTACK
	dw HEADBUTT
	dw PURSUIT
	dw REVERSAL
	dw SCREECH
	dw $ffff

MeowthPlainEggSpeciesMoves:
	native_species_form MEOWTH, PLAIN_FORM
	dw CHARM
	dw HYPNOSIS
	dw AMNESIA
	dw LEER
	dw NIGHT_SLASH
	dw $ffff

MeowthAlolanEggSpeciesMoves:
	native_species_form MEOWTH, ALOLAN_FORM
	dw CHARM
	dw HYPNOSIS
	dw AMNESIA
	dw LEER
	dw NIGHT_SLASH
	dw $ffff

MeowthGalarianEggSpeciesMoves:
	native_species_form MEOWTH, GALARIAN_FORM
	dw CHARM
	dw HYPNOSIS
	dw AMNESIA
	dw LEER
	dw NIGHT_SLASH
	dw $ffff

PsyduckEggSpeciesMoves:
	native_species_form PSYDUCK, PLAIN_FORM
	dw CONFUSE_RAY
	dw CROSS_CHOP
	dw ENCORE
	dw FORESIGHT
	dw FUTURE_SIGHT
	dw HYPNOSIS
	dw PSYBEAM
	dw ICE_BEAM
	dw LIGHT_SCREEN
	dw PSYCHIC_M
	dw $ffff

MankeyEggSpeciesMoves:
	native_species_form MANKEY, PLAIN_FORM
	dw ENCORE
	dw FORESIGHT
	dw BULK_UP
	dw REVERSAL
	dw ROCK_SLIDE
	dw COUNTER
	dw GUNK_SHOT
	dw NIGHT_SLASH
	dw CLOSE_COMBAT
	dw $ffff

GrowlithePlainEggSpeciesMoves:
	native_species_form GROWLITHE, PLAIN_FORM
	dw DOUBLE_KICK
	dw FIRE_SPIN
	dw HEALINGLIGHT
	dw THRASH
	dw CRUNCH
	dw FLARE_BLITZ
	dw BODY_SLAM
	dw SAFEGUARD
	dw CLOSE_COMBAT
	dw $ffff

GrowlitheHisuianEggSpeciesMoves:
	native_species_form GROWLITHE, HISUIAN_FORM
	dw DOUBLE_KICK
	dw FIRE_SPIN
	dw HEALINGLIGHT
	dw THRASH
	dw CRUNCH
	dw FLARE_BLITZ
	dw BODY_SLAM
	dw SAFEGUARD
	dw CLOSE_COMBAT
	dw $ffff

PoliwagEggSpeciesMoves:
	native_species_form POLIWAG, PLAIN_FORM
	dw ENCORE
	dw HAZE
	dw SPLASH
	dw BUBBLE_BEAM
	dw WATER_PULSE
	dw $ffff

AbraEggSpeciesMoves:
	native_species_form ABRA, PLAIN_FORM
	dw BARRIER
	dw ENCORE
	dw LIGHT_SCREEN
	dw KNOCK_OFF
	dw $ffff

MachopEggSpeciesMoves:
	native_species_form MACHOP, PLAIN_FORM
	dw BULLET_PUNCH
	dw ENCORE
	dw BULK_UP
	dw LIGHT_SCREEN
	dw MACH_PUNCH
	dw CLOSE_COMBAT
	dw KNOCK_OFF
	dw $ffff

BellsproutEggSpeciesMoves:
	native_species_form BELLSPROUT, PLAIN_FORM
	dw ENCORE
	dw LEECH_LIFE
	dw SWORDS_DANCE
	dw REFLECT
	dw HEALINGLIGHT
	dw POWER_WHIP
	dw $ffff

TentacoolEggSpeciesMoves:
	native_species_form TENTACOOL, PLAIN_FORM
	dw AURORA_BEAM
	dw CONFUSE_RAY
	dw HAZE
	dw MIRROR_COAT
	dw RAPID_SPIN
	dw SAFEGUARD
	dw KNOCK_OFF
	dw $ffff

GeodudePlainEggSpeciesMoves:
	native_species_form GEODUDE, PLAIN_FORM
	dw ROCK_SLIDE
	dw $ffff

GeodudeAlolanEggSpeciesMoves:
	native_species_form GEODUDE, ALOLAN_FORM
	dw ROCK_SLIDE
	dw $ffff

PonytaPlainEggSpeciesMoves:
	native_species_form PONYTA, PLAIN_FORM
	dw CHARM
	dw DOUBLE_KICK
	dw HYPNOSIS
	dw HEALINGLIGHT
	dw THRASH
	dw QUICK_ATTACK
	dw EXTREMESPEED
	dw PLAY_ROUGH
	dw $ffff

PonytaGalarianEggSpeciesMoves:
	native_species_form PONYTA, GALARIAN_FORM
	dw CHARM
	dw DOUBLE_KICK
	dw HYPNOSIS
	dw HEALINGLIGHT
	dw THRASH
	dw QUICK_ATTACK
	dw PSYBEAM
	dw PSYCHIC_M
	dw EXTREMESPEED
	dw PLAY_ROUGH
	dw $ffff

SlowpokePlainEggSpeciesMoves:
	native_species_form SLOWPOKE, PLAIN_FORM
	native_species_form SLOWPOKE, GALARIAN_FORM
	dw BELLY_DRUM
	dw FUTURE_SIGHT
	dw STOMP
	dw SAFEGUARD
	dw ZEN_HEADBUTT
	dw $ffff

SlowpokeGalarianEggSpeciesMoves:
	native_species_form SLOWPOKE, GALARIAN_FORM
	dw BELLY_DRUM
	dw FUTURE_SIGHT
	dw STOMP
	dw SAFEGUARD
	dw ZEN_HEADBUTT
	dw $ffff

MagnemiteEggSpeciesMoves:
	native_species_form MAGNEMITE, PLAIN_FORM
	dw $ffff

FarfetchDGalarianEggSpeciesMoves:
	native_species_form FARFETCH_D, GALARIAN_FORM
	dw COUNTER
	dw FORESIGHT
	dw GUST
	dw QUICK_ATTACK
	dw STEEL_WING
	dw NIGHT_SLASH
	dw ROOST
	dw $ffff

FarfetchDPlainEggSpeciesMoves:
	native_species_form FARFETCH_D, PLAIN_FORM
	dw FORESIGHT
	dw GUST
	dw QUICK_ATTACK
	dw STEEL_WING
	dw NIGHT_SLASH
	dw ROOST
	dw $ffff

DoduoEggSpeciesMoves:
	native_species_form DODUO, PLAIN_FORM
	dw FEINT_ATTACK
	dw HAZE
	dw SUPERSONIC
	dw QUICK_ATTACK
	dw BRAVE_BIRD
	dw $ffff

SeelEggSpeciesMoves:
	native_species_form SEEL, PLAIN_FORM
	dw DISABLE
	dw LICK
	dw PECK
	dw PERISH_SONG
	dw ENCORE
	dw WATER_PULSE
	dw ICICLE_SPEAR
	dw $ffff

GrimerPlainEggSpeciesMoves:
	native_species_form GRIMER, PLAIN_FORM
	dw HAZE
	dw LICK
	dw MEAN_LOOK
	dw SCARY_FACE
	dw SHADOW_CLAW
	dw $ffff

GrimerAlolanEggSpeciesMoves:
	native_species_form GRIMER, ALOLAN_FORM
	dw HAZE
	dw LICK
	dw MEAN_LOOK
	dw SCARY_FACE
	dw PURSUIT
	dw $ffff

ShellderEggSpeciesMoves:
	native_species_form SHELLDER, PLAIN_FORM
	dw BARRIER
	dw BUBBLE_BEAM
	dw RAPID_SPIN
	dw SCREECH
	dw TAKE_DOWN
	dw WATER_PULSE
	dw ICICLE_SPEAR
	dw ROCK_BLAST
	dw $ffff

GastlyEggSpeciesMoves:
	native_species_form GASTLY, PLAIN_FORM
	dw ASTONISH
	dw DISABLE
	dw HAZE
	dw PERISH_SONG
	dw SCARY_FACE
	dw NASTY_PLOT
	dw FEINT_ATTACK
	dw $ffff

OnixEggSpeciesMoves:
	native_species_form ONIX, PLAIN_FORM
	dw DEFENSE_CURL
	dw ROCK_SLIDE
	dw EARTHQUAKE
	dw ROCK_BLAST
	dw $ffff

DrowzeeEggSpeciesMoves:
	native_species_form DROWZEE, PLAIN_FORM
	dw BARRIER
	dw LIGHT_SCREEN
	dw BELLY_DRUM
	dw $ffff

KrabbyEggSpeciesMoves:
	native_species_form KRABBY, PLAIN_FORM
	dw AGILITY
	dw HAZE
	dw AMNESIA
	dw DIG
	dw CALM_MIND
	dw KNOCK_OFF
	dw $ffff

VoltorbPlainEggSpeciesMoves:
	native_species_form VOLTORB, PLAIN_FORM
	dw $ffff

VoltorbHisuianEggSpeciesMoves:
	native_species_form VOLTORB, HISUIAN_FORM
	dw $ffff

ExeggcuteEggSpeciesMoves:
	native_species_form EXEGGCUTE, PLAIN_FORM
	dw MEGA_DRAIN
	dw HEALINGLIGHT
	dw ANCIENTPOWER
	dw REFLECT
	dw $ffff

CuboneEggSpeciesMoves:
	native_species_form CUBONE, PLAIN_FORM
	dw ANCIENTPOWER
	dw BELLY_DRUM
	dw DOUBLE_KICK
	dw PERISH_SONG
	dw SCREECH
	dw ROCK_SLIDE
	dw SWORDS_DANCE
	dw IRON_HEAD
	dw $ffff

LickitungEggSpeciesMoves:
	native_species_form LICKITUNG, PLAIN_FORM
	dw THRASH
	dw $ffff

KoffingEggSpeciesMoves:
	native_species_form KOFFING, PLAIN_FORM
	dw PSYBEAM
	dw SCREECH
	dw DESTINY_BOND
	dw PAIN_SPLIT
	dw $ffff

RhyhornEggSpeciesMoves:
	native_species_form RHYHORN, PLAIN_FORM
	dw CRUNCH
	dw MAGNITUDE
	dw PURSUIT
	dw REVERSAL
	dw THRASH
	dw ROCK_SLIDE
	dw COUNTER
	dw $ffff

TangelaEggSpeciesMoves:
	native_species_form TANGELA, PLAIN_FORM
	dw CONFUSION
	dw AMNESIA
	dw LEECH_SEED
	dw $ffff

KangaskhanEggSpeciesMoves:
	native_species_form KANGASKHAN, PLAIN_FORM
	dw DISABLE
	dw FOCUS_ENERGY
	dw FORESIGHT
	dw STOMP
	dw SAFEGUARD
	dw $ffff

HorseaEggSpeciesMoves:
	native_species_form HORSEA, PLAIN_FORM
	dw AURORA_BEAM
	dw DISABLE
	dw DRAGON_RAGE
	dw DRAGONBREATH
	dw OCTAZOOKA
	dw SPLASH
	dw HAZE
	dw WATER_PULSE
	dw $ffff

GoldeenEggSpeciesMoves:
	native_species_form GOLDEEN, PLAIN_FORM
	dw AQUA_TAIL
	dw HYDRO_PUMP
	dw PSYBEAM
	dw QUICK_ATTACK
	dw $ffff

StaryuEggSpeciesMoves:
	native_species_form STARYU, PLAIN_FORM
	dw $ffff

ScytherEggSpeciesMoves:
	native_species_form SCYTHER, PLAIN_FORM
	dw BATON_PASS
	dw BUG_BUZZ
	dw REVERSAL
	dw COUNTER
	dw SAFEGUARD
	dw LIGHT_SCREEN
	dw NIGHT_SLASH
	dw $ffff

PinsirEggSpeciesMoves:
	native_species_form PINSIR, PLAIN_FORM
	dw FEINT_ATTACK
	dw FURY_STRIKES
	dw QUICK_ATTACK
	dw CLOSE_COMBAT
	dw $ffff

MagikarpEggSpeciesMoves:
	native_species_form MAGIKARP, NO_FORM
	dw $ffff

LaprasEggSpeciesMoves:
	native_species_form LAPRAS, PLAIN_FORM
	dw AURORA_BEAM
	dw DRAGON_DANCE
	dw FORESIGHT
	dw FUTURE_SIGHT
	dw HEAL_BELL
	dw $ffff

EeveeEggSpeciesMoves:
	native_species_form EEVEE, PLAIN_FORM
	dw CHARM
	dw $ffff

PorygonEggSpeciesMoves:
	native_species_form PORYGON, PLAIN_FORM
	dw $ffff

OmanyteEggSpeciesMoves:
	native_species_form OMANYTE, PLAIN_FORM
	dw AURORA_BEAM
	dw BUBBLE_BEAM
	dw HAZE
	dw SPIKES
	dw TOXIC_SPIKES
	dw SUPERSONIC
	dw WATER_PULSE
	dw KNOCK_OFF
	dw $ffff

KabutoEggSpeciesMoves:
	native_species_form KABUTO, PLAIN_FORM
	dw AURORA_BEAM
	dw BUBBLE_BEAM
	dw CONFUSE_RAY
	dw FORESIGHT
	dw RAPID_SPIN
	dw SCREECH
	dw TAKE_DOWN
	dw DIG
	dw KNOCK_OFF
	dw $ffff

AerodactylEggSpeciesMoves:
	native_species_form AERODACTYL, PLAIN_FORM
	dw FORESIGHT
	dw PURSUIT
	dw STEEL_WING
	dw ROOST
	dw $ffff

DratiniEggSpeciesMoves:
	native_species_form DRATINI, PLAIN_FORM
	dw EXTREMESPEED ; requires Dragon Shrine Dratini
	dw HAZE
	dw SUPERSONIC
	dw WATER_PULSE
	dw AQUA_JET
	dw $ffff

ChikoritaEggSpeciesMoves:
	native_species_form CHIKORITA, PLAIN_FORM
	dw LEECH_SEED
	dw VINE_WHIP
	dw ANCIENTPOWER
	dw COUNTER
	dw SWORDS_DANCE
	dw CHARM
	dw HEAL_BELL
	dw $ffff

CyndaquilEggSpeciesMoves:
	native_species_form CYNDAQUIL, PLAIN_FORM
	dw DOUBLE_KICK
	dw EXTRASENSORY
	dw FLARE_BLITZ
	dw FORESIGHT
	dw FURY_STRIKES
	dw REVERSAL
	dw CLOSE_COMBAT
	dw THRASH
	dw QUICK_ATTACK
	dw $ffff

TotodileEggSpeciesMoves:
	native_species_form TOTODILE, PLAIN_FORM
	dw DRAGON_DANCE
	dw METAL_CLAW
	dw CRUNCH
	dw THRASH
	dw HYDRO_PUMP
	dw ANCIENTPOWER
	dw ROCK_SLIDE
	dw WATER_PULSE
	dw AQUA_JET
	dw $ffff

SentretEggSpeciesMoves:
	native_species_form SENTRET, PLAIN_FORM
	dw CHARM
	dw FOCUS_ENERGY
	dw PURSUIT
	dw REVERSAL
	dw SLASH
	dw DOUBLE_EDGE
	dw TRICK
	dw $ffff

HoothootEggSpeciesMoves:
	native_species_form HOOTHOOT, PLAIN_FORM
	dw AGILITY
	dw FEINT_ATTACK
	dw NIGHT_SHADE
	dw SUPERSONIC
	dw WING_ATTACK
	dw BRAVE_BIRD
	dw HURRICANE
	dw $ffff

LedybaEggSpeciesMoves:
	native_species_form LEDYBA, PLAIN_FORM
	dw DIZZY_PUNCH
	dw ENCORE
	dw PSYBEAM
	dw SCREECH
	dw LIGHT_SCREEN
	dw KNOCK_OFF
	dw DRAIN_PUNCH
	dw $ffff

SpinarakEggSpeciesMoves:
	native_species_form SPINARAK, PLAIN_FORM
	dw BATON_PASS
	dw DISABLE
	dw MEGAHORN
	dw PSYBEAM
	dw PURSUIT
	dw SONIC_BOOM
	dw POISON_JAB
	dw NIGHT_SLASH
	dw TOXIC_SPIKES
	dw $ffff

ChinchouEggSpeciesMoves:
	native_species_form CHINCHOU, PLAIN_FORM
	dw AGILITY
	dw HAZE
	dw PSYBEAM
	dw SCREECH
	dw SUPERSONIC
	dw WATER_PULSE
	dw $ffff

PichuEggSpeciesMoves:
	native_species_form PICHU, PLAIN_FORM
	dw DISARM_VOICE
	dw DOUBLE_SLAP
	dw ENCORE
	dw REVERSAL
	dw $ffff

CleffaEggSpeciesMoves:
	native_species_form CLEFFA, PLAIN_FORM
	dw CALM_MIND
	dw BELLY_DRUM
	dw AMNESIA
	dw SPLASH
	dw FRESH_SNACK
	dw $ffff

IgglybuffEggSpeciesMoves:
	native_species_form IGGLYBUFF, PLAIN_FORM
	dw FEINT_ATTACK
	dw PERISH_SONG
	dw MOONBLAST
	dw $ffff

TogepiEggSpeciesMoves:
	native_species_form TOGEPI, PLAIN_FORM
	dw EXTRASENSORY
	dw FORESIGHT
	dw FUTURE_SIGHT
	dw HEALINGLIGHT
	dw NASTY_PLOT
	dw PECK
	dw $ffff

NatuEggSpeciesMoves:
	native_species_form NATU, PLAIN_FORM
	dw DRILL_PECK
	dw FEINT_ATTACK
	dw HAZE
	dw QUICK_ATTACK
	dw STEEL_WING
	dw ZEN_HEADBUTT
	dw ROOST
	dw $ffff

MareepEggSpeciesMoves:
	native_species_form MAREEP, PLAIN_FORM
	dw AGILITY
	dw REFLECT
	dw MUD_SLAP
	dw SCREECH
	dw THUNDERBOLT
	dw TAKE_DOWN
	dw BODY_SLAM
	dw SAFEGUARD
	dw $ffff

HoppipEggSpeciesMoves:
	native_species_form HOPPIP, PLAIN_FORM
	dw ENCORE
	dw SEED_BOMB
	dw $ffff

AipomEggSpeciesMoves:
	native_species_form AIPOM, PLAIN_FORM
	dw COUNTER
	dw PURSUIT
	dw $ffff

SunkernEggSpeciesMoves:
	native_species_form SUNKERN, PLAIN_FORM
	dw $ffff

YanmaEggSpeciesMoves:
	native_species_form YANMA, PLAIN_FORM
	dw FEINT_ATTACK
	dw LEECH_LIFE
	dw REVERSAL
	dw $ffff

WooperPlainEggSpeciesMoves:
	native_species_form WOOPER, PLAIN_FORM
	dw COUNTER
	dw DOUBLE_KICK
	dw ENCORE
	dw RECOVER
	dw BODY_SLAM
	dw ANCIENTPOWER
	dw SAFEGUARD
	dw $ffff

WooperPaldeanEggSpeciesMoves:
	native_species_form WOOPER, PALDEAN_FORM
	dw COUNTER
	dw DOUBLE_KICK
	dw ENCORE
	dw RECOVER
	dw BODY_SLAM
	dw ANCIENTPOWER
	dw SAFEGUARD
	dw $ffff

MurkrowEggSpeciesMoves:
	native_species_form MURKROW, PLAIN_FORM
	dw CONFUSE_RAY
	dw DRILL_PECK
	dw PERISH_SONG
	dw QUICK_ATTACK
	dw SCREECH
	dw WING_ATTACK
	dw BRAVE_BIRD
	dw ROOST
	dw $ffff

MisdreavusEggSpeciesMoves:
	native_species_form MISDREAVUS, PLAIN_FORM
	dw DESTINY_BOND
	dw NASTY_PLOT
	dw SCREECH
	dw $ffff

GirafarigEggSpeciesMoves:
	native_species_form GIRAFARIG, PLAIN_FORM
	dw DOUBLE_KICK
	dw FORESIGHT
	dw FUTURE_SIGHT
	dw MEAN_LOOK
	dw MIRROR_COAT
	dw TAKE_DOWN
	dw AMNESIA
	dw CALM_MIND
	dw $ffff

PinecoEggSpeciesMoves:
	native_species_form PINECO, PLAIN_FORM
	dw PIN_MISSILE
	dw SWIFT
	dw REFLECT
	dw TOXIC_SPIKES
	dw $ffff

DunsparceEggSpeciesMoves:
	native_species_form DUNSPARCE, NO_FORM
	dw AGILITY
	dw ASTONISH
	dw BITE
	dw RAGE
	dw ANCIENTPOWER
	dw ROCK_SLIDE
	dw HEX
	dw $ffff

GligarEggSpeciesMoves:
	native_species_form GLIGAR, PLAIN_FORM
	dw AGILITY
	dw BATON_PASS
	dw METAL_CLAW
	dw WING_ATTACK
	dw COUNTER
	dw NIGHT_SLASH
	dw $ffff

SnubbullEggSpeciesMoves:
	native_species_form SNUBBULL, PLAIN_FORM
	dw FEINT_ATTACK
	dw LEER
	dw METRONOME
	dw REFLECT
	dw CRUNCH
	dw HEAL_BELL
	dw LICK
	dw CLOSE_COMBAT
	dw $ffff

QwilfishEggSpeciesMoves:
	native_species_form QWILFISH, PLAIN_FORM
	dw BUBBLE_BEAM
	dw HAZE
	dw SUPERSONIC
	dw POISON_JAB
	dw WATER_PULSE
	dw $ffff

QwilfishHisuianEggSpeciesMoves:
	native_species_form QWILFISH, HISUIAN_FORM
	dw $ffff

ShuckleEggSpeciesMoves:
	native_species_form SHUCKLE, PLAIN_FORM
	dw ROLLOUT
	dw ACID
	dw KNOCK_OFF
	dw MUD_SLAP
	dw ROCK_BLAST
	dw $ffff

HeracrossEggSpeciesMoves:
	native_species_form HERACROSS, PLAIN_FORM
	dw ROCK_BLAST
	dw DEFENSE_CURL
	dw PURSUIT
	dw $ffff

SneaselEggSpeciesMoves:
	native_species_form SNEASEL, PLAIN_FORM
	dw BITE
	dw FORESIGHT
	dw PURSUIT
	dw COUNTER
	dw REFLECT
	dw ICICLE_CRASH
	dw ICE_SHARD
	dw $ffff

SneaselHisuianEggSpeciesMoves:
	native_species_form SNEASEL, HISUIAN_FORM
	dw $ffff

TeddiursaEggSpeciesMoves:
	native_species_form TEDDIURSA, PLAIN_FORM
	dw BELLY_DRUM
	dw CROSS_CHOP
	dw CRUNCH
	dw FOCUS_ENERGY
	dw METAL_CLAW
	dw PLAY_ROUGH
	dw TAKE_DOWN
	dw SEISMIC_TOSS
	dw COUNTER
	dw GUNK_SHOT
	dw NIGHT_SLASH
	dw CLOSE_COMBAT
	dw $ffff

SlugmaEggSpeciesMoves:
	native_species_form SLUGMA, PLAIN_FORM
	dw SMOKESCREEN
	dw CURSE
	dw $ffff

SwinubEggSpeciesMoves:
	native_species_form SWINUB, PLAIN_FORM
	dw AVALANCHE
	dw BITE
	dw TAKE_DOWN
	dw BODY_SLAM
	dw ROCK_SLIDE
	dw ANCIENTPOWER
	dw ICICLE_CRASH
	dw ICICLE_SPEAR
	dw $ffff

CorsolaPlainEggSpeciesMoves:
	native_species_form CORSOLA, PLAIN_FORM
	dw BARRIER
	dw CONFUSE_RAY
	dw HAZE
	dw AMNESIA
	dw SCREECH
	dw ROCK_SLIDE
	dw SAFEGUARD
	dw CALM_MIND
	dw WATER_PULSE
	dw ICICLE_SPEAR
	dw $ffff

CorsolaGalarianEggSpeciesMoves:
	native_species_form CORSOLA, GALARIAN_FORM
	dw BARRIER
	dw CONFUSE_RAY
	dw HAZE
	dw AMNESIA
	dw SCREECH
	dw ROCK_SLIDE
	dw SAFEGUARD
	dw CALM_MIND
	dw WATER_PULSE
	dw ICICLE_SPEAR
	dw $ffff

RemoraidEggSpeciesMoves:
	native_species_form REMORAID, PLAIN_FORM
	dw SPLASH
	dw HAZE
	dw OCTAZOOKA
	dw ROCK_BLAST
	dw SCREECH
	dw SUPERSONIC
	dw AURORA_BEAM
	dw GUNK_SHOT
	dw WATER_PULSE
	dw $ffff

DelibirdEggSpeciesMoves:
	native_species_form DELIBIRD, PLAIN_FORM
	dw AURORA_BEAM
	dw DESTINY_BOND
	dw ICE_PUNCH
	dw ICY_WIND
	dw QUICK_ATTACK
	dw RAPID_SPIN
	dw SPLASH
	dw $ffff

SkarmoryEggSpeciesMoves:
	native_species_form SKARMORY, PLAIN_FORM
	dw DRILL_PECK
	dw PURSUIT
	dw BRAVE_BIRD
	dw $ffff

HoundourEggSpeciesMoves:
	native_species_form HOUNDOUR, PLAIN_FORM
	dw DESTINY_BOND
	dw FIRE_SPIN
	dw PURSUIT
	dw RAGE
	dw REVERSAL
	dw COUNTER
	dw WILL_O_WISP
	dw $ffff

PhanpyEggSpeciesMoves:
	native_species_form PHANPY, PLAIN_FORM
	dw FOCUS_ENERGY
	dw PLAY_ROUGH
	dw WATER_GUN
	dw BODY_SLAM
	dw ANCIENTPOWER
	dw GUNK_SHOT
	dw ICE_SHARD
	dw ENCORE
	dw $ffff

StantlerEggSpeciesMoves:
	native_species_form STANTLER, PLAIN_FORM
	dw BITE
	dw DOUBLE_KICK
	dw EXTRASENSORY
	dw RAGE
	dw $ffff

TyrogueEggSpeciesMoves:
	native_species_form TYROGUE, PLAIN_FORM
	dw BULLET_PUNCH
	dw HI_JUMP_KICK
	dw MACH_PUNCH
	dw PURSUIT
	dw RAPID_SPIN
	dw $ffff

SmoochumEggSpeciesMoves:
	native_species_form SMOOCHUM, PLAIN_FORM
	dw BULK_UP
	dw NASTY_PLOT
	dw $ffff

ElekidEggSpeciesMoves:
	native_species_form ELEKID, PLAIN_FORM
	dw BARRIER
	dw CROSS_CHOP
	dw KARATE_CHOP
	dw BULK_UP
	dw $ffff

MagbyEggSpeciesMoves:
	native_species_form MAGBY, PLAIN_FORM
	dw BARRIER
	dw BELLY_DRUM
	dw CROSS_CHOP
	dw FLARE_BLITZ
	dw FOCUS_ENERGY
	dw KARATE_CHOP
	dw MACH_PUNCH
	dw SCREECH
	dw $ffff

MiltankEggSpeciesMoves:
	native_species_form MILTANK, PLAIN_FORM
	dw DIZZY_PUNCH
	dw REVERSAL
	dw SEISMIC_TOSS
	dw $ffff

LarvitarEggSpeciesMoves:
	native_species_form LARVITAR, PLAIN_FORM
	dw DRAGON_DANCE
	dw FOCUS_ENERGY
	dw PURSUIT
	dw STOMP
	dw OUTRAGE
	dw ANCIENTPOWER
	dw IRON_HEAD
	dw $ffff

AzurillEggSpeciesMoves:
	native_species_form AZURILL, PLAIN_FORM
	dw BELLY_DRUM
	dw FORESIGHT
	dw FUTURE_SIGHT
	dw PERISH_SONG
	dw SUPERSONIC
	dw LIGHT_SCREEN
	dw AMNESIA
	dw CALM_MIND
	dw $ffff

WynautEggSpeciesMoves:
	native_species_form WYNAUT, PLAIN_FORM
	dw CHARM
	dw ENCORE
	dw $ffff

BonslyEggSpeciesMoves:
	native_species_form BONSLY, PLAIN_FORM
	dw DEFENSE_CURL
	dw EXPLOSION
	dw $ffff

MimeJrEggSpeciesMoves:
	native_species_form MIME_JR_, PLAIN_FORM
	dw CONFUSE_RAY
	dw FUTURE_SIGHT
	dw HYPNOSIS
	dw NASTY_PLOT
	dw TRICK
	dw $ffff

HappinyEggSpeciesMoves:
	native_species_form HAPPINY, PLAIN_FORM
	dw HEAL_BELL
	dw $ffff

MantykeEggSpeciesMoves:
	native_species_form MANTYKE, PLAIN_FORM
	dw HAZE
	dw MIRROR_COAT
	dw SPLASH
	dw HYDRO_PUMP
	dw GUNK_SHOT
	dw $ffff

MunchlaxEggSpeciesMoves:
	native_species_form MUNCHLAX, PLAIN_FORM
	dw CHARM
	dw COUNTER
	dw CURSE
	dw DOUBLE_EDGE
	dw LICK
	dw GUNK_SHOT
	dw $ffff

NoEggSpeciesMoves:
	dw 0 ; no hatchling species
	dw NO_FORM
	dw $ffff

if DEF(NATIVE_SPECIES_TEST)
WideTestEggSpeciesMoves:
	native_species_form WIDE_TEST_SPECIES, PLAIN_FORM
	dw TACKLE, $ff
endc
