SECTION "Egg Moves", ROMX

INCLUDE "data/pokemon/egg_move_pointers.asm"

EggSpeciesMoves::

BulbasaurEggSpeciesMoves:
	native_species_form BULBASAUR, PLAIN_FORM
	db CHARM
	db PETAL_DANCE
	db LIGHT_SCREEN
	db SAFEGUARD
	db POWER_WHIP
	db $ff

CharmanderEggSpeciesMoves:
	native_species_form CHARMANDER, PLAIN_FORM
	db ANCIENTPOWER
	db BELLY_DRUM
	db BITE
	db CRUNCH
	db DRAGON_DANCE
	db DRAGONBREATH
	db FLARE_BLITZ
	db OUTRAGE
	db $ff

SquirtleEggSpeciesMoves:
	native_species_form SQUIRTLE, PLAIN_FORM
	db CONFUSION
	db CRUNCH
	db FORESIGHT
	db HAZE
	db MIRROR_COAT
	db AQUA_JET
	db $ff

CaterpieEggSpeciesMoves:
	native_species_form CATERPIE, PLAIN_FORM
	db $ff

WeedleEggSpeciesMoves:
	native_species_form WEEDLE, PLAIN_FORM
	db $ff

PidgeyEggSpeciesMoves:
	native_species_form PIDGEY, PLAIN_FORM
	db PECK
	db FEINT_ATTACK
	db FORESIGHT
	db PURSUIT
	db AIR_SLASH
	db STEEL_WING
	db CHARM
	db EXTREMESPEED
	db BRAVE_BIRD
	db $ff

RattataPlainEggSpeciesMoves:
	native_species_form RATTATA, PLAIN_FORM
	db FURY_STRIKES
	db REVERSAL
	db SCREECH
	db BITE
	db COUNTER
	db $ff

RattataAlolanEggSpeciesMoves:
	native_species_form RATTATA, ALOLAN_FORM
	db FURY_STRIKES
	db REVERSAL
	db SCREECH
	db BITE
	db COUNTER
	db $ff

SpearowEggSpeciesMoves:
	native_species_form SPEAROW, PLAIN_FORM
	db ASTONISH
	db FEINT_ATTACK
	db QUICK_ATTACK
	db SCARY_FACE
	db TRI_ATTACK
	db $ff

EkansEggSpeciesMoves:
	native_species_form EKANS, NO_FORM
	db CRUNCH
	db DISABLE
	db PURSUIT
	db SCARY_FACE
	db $ff

SandshrewPlainEggSpeciesMoves:
	native_species_form SANDSHREW, PLAIN_FORM
	db METAL_CLAW
	db RAPID_SPIN
	db SAFEGUARD
	db COUNTER
	db NIGHT_SLASH
	db $ff

SandshrewAlolanEggSpeciesMoves:
	native_species_form SANDSHREW, ALOLAN_FORM
	db AMNESIA
	db RAPID_SPIN
	db SAFEGUARD
	db REVERSAL ; Flail → similar move
	db ICICLE_CRASH
	db ICICLE_SPEAR
	db NIGHT_SLASH
	db $ff

NidoranFEggSpeciesMoves:
	native_species_form NIDORAN_F, PLAIN_FORM
	db CHARM
	db DISABLE
	db FOCUS_ENERGY
	db PURSUIT
	db SUPERSONIC
	db TAKE_DOWN
	db $ff

NidoranMEggSpeciesMoves:
	native_species_form NIDORAN_M, PLAIN_FORM
	db AMNESIA
	db CONFUSION
	db DISABLE
	db SUPERSONIC
	db TAKE_DOWN
	db CALM_MIND
	db COUNTER
	db $ff

VulpixPlainEggSpeciesMoves:
	native_species_form VULPIX, PLAIN_FORM
	db FLAME_CHARGE
	db DISABLE
	db FLARE_BLITZ
	db HYPNOSIS
	db FEINT_ATTACK
	db EXTRASENSORY
	db CHARM
	db ENERGY_BALL
	db ROAR
	db $ff

VulpixAlolanEggSpeciesMoves:
	native_species_form VULPIX, ALOLAN_FORM
	db DISABLE
	db BLIZZARD
	db HYPNOSIS
	db FEINT_ATTACK
	db EXTRASENSORY
	db CHARM
	db ICE_BEAM
	db ROAR
	db $ff

ZubatEggSpeciesMoves:
	native_species_form ZUBAT, PLAIN_FORM
	db FEINT_ATTACK
	db GUST
	db HYPNOSIS
	db NASTY_PLOT
	db PURSUIT
	db QUICK_ATTACK
	db ZEN_HEADBUTT
	db BRAVE_BIRD
	db $ff

OddishEggSpeciesMoves:
	native_species_form ODDISH, PLAIN_FORM
	db CHARM
	db RAZOR_LEAF
	db HEALINGLIGHT
	db SWORDS_DANCE
	db $ff

ParasEggSpeciesMoves:
	native_species_form PARAS, PLAIN_FORM
	db AGILITY
	db LEECH_SEED
	db METAL_CLAW
	db PSYBEAM
	db PURSUIT
	db SCREECH
	db SHADOW_CLAW
	db $ff

VenonatEggSpeciesMoves:
	native_species_form VENONAT, PLAIN_FORM
	db AGILITY
	db BATON_PASS
	db HEALINGLIGHT
	db SCREECH
	db TOXIC_SPIKES
	db $ff

DiglettPlainEggSpeciesMoves:
	native_species_form DIGLETT, PLAIN_FORM
	db ANCIENTPOWER
	db FEINT_ATTACK
	db HEADBUTT
	db PURSUIT
	db REVERSAL
	db SCREECH
	db $ff

DiglettAlolanEggSpeciesMoves:
	native_species_form DIGLETT, ALOLAN_FORM
	db ANCIENTPOWER
	db FEINT_ATTACK
	db HEADBUTT
	db PURSUIT
	db REVERSAL
	db SCREECH
	db $ff

MeowthPlainEggSpeciesMoves:
	native_species_form MEOWTH, PLAIN_FORM
	db CHARM
	db HYPNOSIS
	db AMNESIA
	db LEER
	db NIGHT_SLASH
	db $ff

MeowthAlolanEggSpeciesMoves:
	native_species_form MEOWTH, ALOLAN_FORM
	db CHARM
	db HYPNOSIS
	db AMNESIA
	db LEER
	db NIGHT_SLASH
	db $ff

MeowthGalarianEggSpeciesMoves:
	native_species_form MEOWTH, GALARIAN_FORM
	db CHARM
	db HYPNOSIS
	db AMNESIA
	db LEER
	db NIGHT_SLASH
	db $ff

PsyduckEggSpeciesMoves:
	native_species_form PSYDUCK, PLAIN_FORM
	db CONFUSE_RAY
	db CROSS_CHOP
	db ENCORE
	db FORESIGHT
	db FUTURE_SIGHT
	db HYPNOSIS
	db PSYBEAM
	db ICE_BEAM
	db LIGHT_SCREEN
	db PSYCHIC_M
	db $ff

MankeyEggSpeciesMoves:
	native_species_form MANKEY, PLAIN_FORM
	db ENCORE
	db FORESIGHT
	db BULK_UP
	db REVERSAL
	db ROCK_SLIDE
	db COUNTER
	db GUNK_SHOT
	db NIGHT_SLASH
	db CLOSE_COMBAT
	db $ff

GrowlithePlainEggSpeciesMoves:
	native_species_form GROWLITHE, PLAIN_FORM
	db DOUBLE_KICK
	db FIRE_SPIN
	db HEALINGLIGHT
	db THRASH
	db CRUNCH
	db FLARE_BLITZ
	db BODY_SLAM
	db SAFEGUARD
	db CLOSE_COMBAT
	db $ff

GrowlitheHisuianEggSpeciesMoves:
	native_species_form GROWLITHE, HISUIAN_FORM
	db DOUBLE_KICK
	db FIRE_SPIN
	db HEALINGLIGHT
	db THRASH
	db CRUNCH
	db FLARE_BLITZ
	db BODY_SLAM
	db SAFEGUARD
	db CLOSE_COMBAT
	db $ff

PoliwagEggSpeciesMoves:
	native_species_form POLIWAG, PLAIN_FORM
	db ENCORE
	db HAZE
	db SPLASH
	db BUBBLE_BEAM
	db WATER_PULSE
	db $ff

AbraEggSpeciesMoves:
	native_species_form ABRA, PLAIN_FORM
	db BARRIER
	db ENCORE
	db LIGHT_SCREEN
	db KNOCK_OFF
	db $ff

MachopEggSpeciesMoves:
	native_species_form MACHOP, PLAIN_FORM
	db BULLET_PUNCH
	db ENCORE
	db BULK_UP
	db LIGHT_SCREEN
	db MACH_PUNCH
	db CLOSE_COMBAT
	db KNOCK_OFF
	db $ff

BellsproutEggSpeciesMoves:
	native_species_form BELLSPROUT, PLAIN_FORM
	db ENCORE
	db LEECH_LIFE
	db SWORDS_DANCE
	db REFLECT
	db HEALINGLIGHT
	db POWER_WHIP
	db $ff

TentacoolEggSpeciesMoves:
	native_species_form TENTACOOL, PLAIN_FORM
	db AURORA_BEAM
	db CONFUSE_RAY
	db HAZE
	db MIRROR_COAT
	db RAPID_SPIN
	db SAFEGUARD
	db KNOCK_OFF
	db $ff

GeodudePlainEggSpeciesMoves:
	native_species_form GEODUDE, PLAIN_FORM
	db ROCK_SLIDE
	db $ff

GeodudeAlolanEggSpeciesMoves:
	native_species_form GEODUDE, ALOLAN_FORM
	db ROCK_SLIDE
	db $ff

PonytaPlainEggSpeciesMoves:
	native_species_form PONYTA, PLAIN_FORM
	db CHARM
	db DOUBLE_KICK
	db HYPNOSIS
	db HEALINGLIGHT
	db THRASH
	db QUICK_ATTACK
	db EXTREMESPEED
	db PLAY_ROUGH
	db $ff

PonytaGalarianEggSpeciesMoves:
	native_species_form PONYTA, GALARIAN_FORM
	db CHARM
	db DOUBLE_KICK
	db HYPNOSIS
	db HEALINGLIGHT
	db THRASH
	db QUICK_ATTACK
	db PSYBEAM
	db PSYCHIC_M
	db EXTREMESPEED
	db PLAY_ROUGH
	db $ff

SlowpokePlainEggSpeciesMoves:
	native_species_form SLOWPOKE, PLAIN_FORM
	native_species_form SLOWPOKE, GALARIAN_FORM
	db BELLY_DRUM
	db FUTURE_SIGHT
	db STOMP
	db SAFEGUARD
	db ZEN_HEADBUTT
	db $ff

SlowpokeGalarianEggSpeciesMoves:
	native_species_form SLOWPOKE, GALARIAN_FORM
	db BELLY_DRUM
	db FUTURE_SIGHT
	db STOMP
	db SAFEGUARD
	db ZEN_HEADBUTT
	db $ff

MagnemiteEggSpeciesMoves:
	native_species_form MAGNEMITE, PLAIN_FORM
	db $ff

FarfetchDGalarianEggSpeciesMoves:
	native_species_form FARFETCH_D, GALARIAN_FORM
	db COUNTER
	db FORESIGHT
	db GUST
	db QUICK_ATTACK
	db STEEL_WING
	db NIGHT_SLASH
	db ROOST
	db $ff

FarfetchDPlainEggSpeciesMoves:
	native_species_form FARFETCH_D, PLAIN_FORM
	db FORESIGHT
	db GUST
	db QUICK_ATTACK
	db STEEL_WING
	db NIGHT_SLASH
	db ROOST
	db $ff

DoduoEggSpeciesMoves:
	native_species_form DODUO, PLAIN_FORM
	db FEINT_ATTACK
	db HAZE
	db SUPERSONIC
	db QUICK_ATTACK
	db BRAVE_BIRD
	db $ff

SeelEggSpeciesMoves:
	native_species_form SEEL, PLAIN_FORM
	db DISABLE
	db LICK
	db PECK
	db PERISH_SONG
	db ENCORE
	db WATER_PULSE
	db ICICLE_SPEAR
	db $ff

GrimerPlainEggSpeciesMoves:
	native_species_form GRIMER, PLAIN_FORM
	db HAZE
	db LICK
	db MEAN_LOOK
	db SCARY_FACE
	db SHADOW_CLAW
	db $ff

GrimerAlolanEggSpeciesMoves:
	native_species_form GRIMER, ALOLAN_FORM
	db HAZE
	db LICK
	db MEAN_LOOK
	db SCARY_FACE
	db PURSUIT
	db $ff

ShellderEggSpeciesMoves:
	native_species_form SHELLDER, PLAIN_FORM
	db BARRIER
	db BUBBLE_BEAM
	db RAPID_SPIN
	db SCREECH
	db TAKE_DOWN
	db WATER_PULSE
	db ICICLE_SPEAR
	db ROCK_BLAST
	db $ff

GastlyEggSpeciesMoves:
	native_species_form GASTLY, PLAIN_FORM
	db ASTONISH
	db DISABLE
	db HAZE
	db PERISH_SONG
	db SCARY_FACE
	db NASTY_PLOT
	db FEINT_ATTACK
	db $ff

OnixEggSpeciesMoves:
	native_species_form ONIX, PLAIN_FORM
	db DEFENSE_CURL
	db ROCK_SLIDE
	db EARTHQUAKE
	db ROCK_BLAST
	db $ff

DrowzeeEggSpeciesMoves:
	native_species_form DROWZEE, PLAIN_FORM
	db BARRIER
	db LIGHT_SCREEN
	db BELLY_DRUM
	db $ff

KrabbyEggSpeciesMoves:
	native_species_form KRABBY, PLAIN_FORM
	db AGILITY
	db HAZE
	db AMNESIA
	db DIG
	db CALM_MIND
	db KNOCK_OFF
	db $ff

VoltorbPlainEggSpeciesMoves:
	native_species_form VOLTORB, PLAIN_FORM
	db $ff

VoltorbHisuianEggSpeciesMoves:
	native_species_form VOLTORB, HISUIAN_FORM
	db $ff

ExeggcuteEggSpeciesMoves:
	native_species_form EXEGGCUTE, PLAIN_FORM
	db MEGA_DRAIN
	db HEALINGLIGHT
	db ANCIENTPOWER
	db REFLECT
	db $ff

CuboneEggSpeciesMoves:
	native_species_form CUBONE, PLAIN_FORM
	db ANCIENTPOWER
	db BELLY_DRUM
	db DOUBLE_KICK
	db PERISH_SONG
	db SCREECH
	db ROCK_SLIDE
	db SWORDS_DANCE
	db IRON_HEAD
	db $ff

LickitungEggSpeciesMoves:
	native_species_form LICKITUNG, PLAIN_FORM
	db THRASH
	db $ff

KoffingEggSpeciesMoves:
	native_species_form KOFFING, PLAIN_FORM
	db PSYBEAM
	db SCREECH
	db DESTINY_BOND
	db PAIN_SPLIT
	db $ff

RhyhornEggSpeciesMoves:
	native_species_form RHYHORN, PLAIN_FORM
	db CRUNCH
	db MAGNITUDE
	db PURSUIT
	db REVERSAL
	db THRASH
	db ROCK_SLIDE
	db COUNTER
	db $ff

TangelaEggSpeciesMoves:
	native_species_form TANGELA, PLAIN_FORM
	db CONFUSION
	db AMNESIA
	db LEECH_SEED
	db $ff

KangaskhanEggSpeciesMoves:
	native_species_form KANGASKHAN, PLAIN_FORM
	db DISABLE
	db FOCUS_ENERGY
	db FORESIGHT
	db STOMP
	db SAFEGUARD
	db $ff

HorseaEggSpeciesMoves:
	native_species_form HORSEA, PLAIN_FORM
	db AURORA_BEAM
	db DISABLE
	db DRAGON_RAGE
	db DRAGONBREATH
	db OCTAZOOKA
	db SPLASH
	db HAZE
	db WATER_PULSE
	db $ff

GoldeenEggSpeciesMoves:
	native_species_form GOLDEEN, PLAIN_FORM
	db AQUA_TAIL
	db HYDRO_PUMP
	db PSYBEAM
	db QUICK_ATTACK
	db $ff

StaryuEggSpeciesMoves:
	native_species_form STARYU, PLAIN_FORM
	db $ff

ScytherEggSpeciesMoves:
	native_species_form SCYTHER, PLAIN_FORM
	db BATON_PASS
	db BUG_BUZZ
	db REVERSAL
	db COUNTER
	db SAFEGUARD
	db LIGHT_SCREEN
	db NIGHT_SLASH
	db $ff

PinsirEggSpeciesMoves:
	native_species_form PINSIR, PLAIN_FORM
	db FEINT_ATTACK
	db FURY_STRIKES
	db QUICK_ATTACK
	db CLOSE_COMBAT
	db $ff

MagikarpEggSpeciesMoves:
	native_species_form MAGIKARP, NO_FORM
	db $ff

LaprasEggSpeciesMoves:
	native_species_form LAPRAS, PLAIN_FORM
	db AURORA_BEAM
	db DRAGON_DANCE
	db FORESIGHT
	db FUTURE_SIGHT
	db HEAL_BELL
	db $ff

EeveeEggSpeciesMoves:
	native_species_form EEVEE, PLAIN_FORM
	db CHARM
	db $ff

PorygonEggSpeciesMoves:
	native_species_form PORYGON, PLAIN_FORM
	db $ff

OmanyteEggSpeciesMoves:
	native_species_form OMANYTE, PLAIN_FORM
	db AURORA_BEAM
	db BUBBLE_BEAM
	db HAZE
	db SPIKES
	db TOXIC_SPIKES
	db SUPERSONIC
	db WATER_PULSE
	db KNOCK_OFF
	db $ff

KabutoEggSpeciesMoves:
	native_species_form KABUTO, PLAIN_FORM
	db AURORA_BEAM
	db BUBBLE_BEAM
	db CONFUSE_RAY
	db FORESIGHT
	db RAPID_SPIN
	db SCREECH
	db TAKE_DOWN
	db DIG
	db KNOCK_OFF
	db $ff

AerodactylEggSpeciesMoves:
	native_species_form AERODACTYL, PLAIN_FORM
	db FORESIGHT
	db PURSUIT
	db STEEL_WING
	db ROOST
	db $ff

DratiniEggSpeciesMoves:
	native_species_form DRATINI, PLAIN_FORM
	db EXTREMESPEED ; requires Dragon Shrine Dratini
	db HAZE
	db SUPERSONIC
	db WATER_PULSE
	db AQUA_JET
	db $ff

ChikoritaEggSpeciesMoves:
	native_species_form CHIKORITA, PLAIN_FORM
	db LEECH_SEED
	db VINE_WHIP
	db ANCIENTPOWER
	db COUNTER
	db SWORDS_DANCE
	db CHARM
	db HEAL_BELL
	db $ff

CyndaquilEggSpeciesMoves:
	native_species_form CYNDAQUIL, PLAIN_FORM
	db DOUBLE_KICK
	db EXTRASENSORY
	db FLARE_BLITZ
	db FORESIGHT
	db FURY_STRIKES
	db REVERSAL
	db CLOSE_COMBAT
	db THRASH
	db QUICK_ATTACK
	db $ff

TotodileEggSpeciesMoves:
	native_species_form TOTODILE, PLAIN_FORM
	db DRAGON_DANCE
	db METAL_CLAW
	db CRUNCH
	db THRASH
	db HYDRO_PUMP
	db ANCIENTPOWER
	db ROCK_SLIDE
	db WATER_PULSE
	db AQUA_JET
	db $ff

SentretEggSpeciesMoves:
	native_species_form SENTRET, PLAIN_FORM
	db CHARM
	db FOCUS_ENERGY
	db PURSUIT
	db REVERSAL
	db SLASH
	db DOUBLE_EDGE
	db TRICK
	db $ff

HoothootEggSpeciesMoves:
	native_species_form HOOTHOOT, PLAIN_FORM
	db AGILITY
	db FEINT_ATTACK
	db NIGHT_SHADE
	db SUPERSONIC
	db WING_ATTACK
	db BRAVE_BIRD
	db HURRICANE
	db $ff

LedybaEggSpeciesMoves:
	native_species_form LEDYBA, PLAIN_FORM
	db DIZZY_PUNCH
	db ENCORE
	db PSYBEAM
	db SCREECH
	db LIGHT_SCREEN
	db KNOCK_OFF
	db DRAIN_PUNCH
	db $ff

SpinarakEggSpeciesMoves:
	native_species_form SPINARAK, PLAIN_FORM
	db BATON_PASS
	db DISABLE
	db MEGAHORN
	db PSYBEAM
	db PURSUIT
	db SONIC_BOOM
	db POISON_JAB
	db NIGHT_SLASH
	db TOXIC_SPIKES
	db $ff

ChinchouEggSpeciesMoves:
	native_species_form CHINCHOU, PLAIN_FORM
	db AGILITY
	db HAZE
	db PSYBEAM
	db SCREECH
	db SUPERSONIC
	db WATER_PULSE
	db $ff

PichuEggSpeciesMoves:
	native_species_form PICHU, PLAIN_FORM
	db DISARM_VOICE
	db DOUBLE_SLAP
	db ENCORE
	db REVERSAL
	db $ff

CleffaEggSpeciesMoves:
	native_species_form CLEFFA, PLAIN_FORM
	db CALM_MIND
	db BELLY_DRUM
	db AMNESIA
	db SPLASH
	db FRESH_SNACK
	db $ff

IgglybuffEggSpeciesMoves:
	native_species_form IGGLYBUFF, PLAIN_FORM
	db FEINT_ATTACK
	db PERISH_SONG
	db MOONBLAST
	db $ff

TogepiEggSpeciesMoves:
	native_species_form TOGEPI, PLAIN_FORM
	db EXTRASENSORY
	db FORESIGHT
	db FUTURE_SIGHT
	db HEALINGLIGHT
	db NASTY_PLOT
	db PECK
	db $ff

NatuEggSpeciesMoves:
	native_species_form NATU, PLAIN_FORM
	db DRILL_PECK
	db FEINT_ATTACK
	db HAZE
	db QUICK_ATTACK
	db STEEL_WING
	db ZEN_HEADBUTT
	db ROOST
	db $ff

MareepEggSpeciesMoves:
	native_species_form MAREEP, PLAIN_FORM
	db AGILITY
	db REFLECT
	db MUD_SLAP
	db SCREECH
	db THUNDERBOLT
	db TAKE_DOWN
	db BODY_SLAM
	db SAFEGUARD
	db $ff

HoppipEggSpeciesMoves:
	native_species_form HOPPIP, PLAIN_FORM
	db ENCORE
	db SEED_BOMB
	db $ff

AipomEggSpeciesMoves:
	native_species_form AIPOM, PLAIN_FORM
	db COUNTER
	db PURSUIT
	db $ff

SunkernEggSpeciesMoves:
	native_species_form SUNKERN, PLAIN_FORM
	db $ff

YanmaEggSpeciesMoves:
	native_species_form YANMA, PLAIN_FORM
	db FEINT_ATTACK
	db LEECH_LIFE
	db REVERSAL
	db $ff

WooperPlainEggSpeciesMoves:
	native_species_form WOOPER, PLAIN_FORM
	db COUNTER
	db DOUBLE_KICK
	db ENCORE
	db RECOVER
	db BODY_SLAM
	db ANCIENTPOWER
	db SAFEGUARD
	db $ff

WooperPaldeanEggSpeciesMoves:
	native_species_form WOOPER, PALDEAN_FORM
	db COUNTER
	db DOUBLE_KICK
	db ENCORE
	db RECOVER
	db BODY_SLAM
	db ANCIENTPOWER
	db SAFEGUARD
	db $ff

MurkrowEggSpeciesMoves:
	native_species_form MURKROW, PLAIN_FORM
	db CONFUSE_RAY
	db DRILL_PECK
	db PERISH_SONG
	db QUICK_ATTACK
	db SCREECH
	db WING_ATTACK
	db BRAVE_BIRD
	db ROOST
	db $ff

MisdreavusEggSpeciesMoves:
	native_species_form MISDREAVUS, PLAIN_FORM
	db DESTINY_BOND
	db NASTY_PLOT
	db SCREECH
	db $ff

GirafarigEggSpeciesMoves:
	native_species_form GIRAFARIG, PLAIN_FORM
	db DOUBLE_KICK
	db FORESIGHT
	db FUTURE_SIGHT
	db MEAN_LOOK
	db MIRROR_COAT
	db TAKE_DOWN
	db AMNESIA
	db CALM_MIND
	db $ff

PinecoEggSpeciesMoves:
	native_species_form PINECO, PLAIN_FORM
	db PIN_MISSILE
	db SWIFT
	db REFLECT
	db TOXIC_SPIKES
	db $ff

DunsparceEggSpeciesMoves:
	native_species_form DUNSPARCE, NO_FORM
	db AGILITY
	db ASTONISH
	db BITE
	db RAGE
	db ANCIENTPOWER
	db ROCK_SLIDE
	db HEX
	db $ff

GligarEggSpeciesMoves:
	native_species_form GLIGAR, PLAIN_FORM
	db AGILITY
	db BATON_PASS
	db METAL_CLAW
	db WING_ATTACK
	db COUNTER
	db NIGHT_SLASH
	db $ff

SnubbullEggSpeciesMoves:
	native_species_form SNUBBULL, PLAIN_FORM
	db FEINT_ATTACK
	db LEER
	db METRONOME
	db REFLECT
	db CRUNCH
	db HEAL_BELL
	db LICK
	db CLOSE_COMBAT
	db $ff

QwilfishEggSpeciesMoves:
	native_species_form QWILFISH, PLAIN_FORM
	db BUBBLE_BEAM
	db HAZE
	db SUPERSONIC
	db POISON_JAB
	db WATER_PULSE
	db $ff

QwilfishHisuianEggSpeciesMoves:
	native_species_form QWILFISH, HISUIAN_FORM
	db $ff

ShuckleEggSpeciesMoves:
	native_species_form SHUCKLE, PLAIN_FORM
	db ROLLOUT
	db ACID
	db KNOCK_OFF
	db MUD_SLAP
	db ROCK_BLAST
	db $ff

HeracrossEggSpeciesMoves:
	native_species_form HERACROSS, PLAIN_FORM
	db ROCK_BLAST
	db DEFENSE_CURL
	db PURSUIT
	db $ff

SneaselEggSpeciesMoves:
	native_species_form SNEASEL, PLAIN_FORM
	db BITE
	db FORESIGHT
	db PURSUIT
	db COUNTER
	db REFLECT
	db ICICLE_CRASH
	db ICE_SHARD
	db $ff

SneaselHisuianEggSpeciesMoves:
	native_species_form SNEASEL, HISUIAN_FORM
	db $ff

TeddiursaEggSpeciesMoves:
	native_species_form TEDDIURSA, PLAIN_FORM
	db BELLY_DRUM
	db CROSS_CHOP
	db CRUNCH
	db FOCUS_ENERGY
	db METAL_CLAW
	db PLAY_ROUGH
	db TAKE_DOWN
	db SEISMIC_TOSS
	db COUNTER
	db GUNK_SHOT
	db NIGHT_SLASH
	db CLOSE_COMBAT
	db $ff

SlugmaEggSpeciesMoves:
	native_species_form SLUGMA, PLAIN_FORM
	db SMOKESCREEN
	db CURSE
	db $ff

SwinubEggSpeciesMoves:
	native_species_form SWINUB, PLAIN_FORM
	db AVALANCHE
	db BITE
	db TAKE_DOWN
	db BODY_SLAM
	db ROCK_SLIDE
	db ANCIENTPOWER
	db ICICLE_CRASH
	db ICICLE_SPEAR
	db $ff

CorsolaPlainEggSpeciesMoves:
	native_species_form CORSOLA, PLAIN_FORM
	db BARRIER
	db CONFUSE_RAY
	db HAZE
	db AMNESIA
	db SCREECH
	db ROCK_SLIDE
	db SAFEGUARD
	db CALM_MIND
	db WATER_PULSE
	db ICICLE_SPEAR
	db $ff

CorsolaGalarianEggSpeciesMoves:
	native_species_form CORSOLA, GALARIAN_FORM
	db BARRIER
	db CONFUSE_RAY
	db HAZE
	db AMNESIA
	db SCREECH
	db ROCK_SLIDE
	db SAFEGUARD
	db CALM_MIND
	db WATER_PULSE
	db ICICLE_SPEAR
	db $ff

RemoraidEggSpeciesMoves:
	native_species_form REMORAID, PLAIN_FORM
	db SPLASH
	db HAZE
	db OCTAZOOKA
	db ROCK_BLAST
	db SCREECH
	db SUPERSONIC
	db AURORA_BEAM
	db GUNK_SHOT
	db WATER_PULSE
	db $ff

DelibirdEggSpeciesMoves:
	native_species_form DELIBIRD, PLAIN_FORM
	db AURORA_BEAM
	db DESTINY_BOND
	db ICE_PUNCH
	db ICY_WIND
	db QUICK_ATTACK
	db RAPID_SPIN
	db SPLASH
	db $ff

SkarmoryEggSpeciesMoves:
	native_species_form SKARMORY, PLAIN_FORM
	db DRILL_PECK
	db PURSUIT
	db BRAVE_BIRD
	db $ff

HoundourEggSpeciesMoves:
	native_species_form HOUNDOUR, PLAIN_FORM
	db DESTINY_BOND
	db FIRE_SPIN
	db PURSUIT
	db RAGE
	db REVERSAL
	db COUNTER
	db WILL_O_WISP
	db $ff

PhanpyEggSpeciesMoves:
	native_species_form PHANPY, PLAIN_FORM
	db FOCUS_ENERGY
	db PLAY_ROUGH
	db WATER_GUN
	db BODY_SLAM
	db ANCIENTPOWER
	db GUNK_SHOT
	db ICE_SHARD
	db ENCORE
	db $ff

StantlerEggSpeciesMoves:
	native_species_form STANTLER, PLAIN_FORM
	db BITE
	db DOUBLE_KICK
	db EXTRASENSORY
	db RAGE
	db $ff

TyrogueEggSpeciesMoves:
	native_species_form TYROGUE, PLAIN_FORM
	db BULLET_PUNCH
	db HI_JUMP_KICK
	db MACH_PUNCH
	db PURSUIT
	db RAPID_SPIN
	db $ff

SmoochumEggSpeciesMoves:
	native_species_form SMOOCHUM, PLAIN_FORM
	db BULK_UP
	db NASTY_PLOT
	db $ff

ElekidEggSpeciesMoves:
	native_species_form ELEKID, PLAIN_FORM
	db BARRIER
	db CROSS_CHOP
	db KARATE_CHOP
	db BULK_UP
	db $ff

MagbyEggSpeciesMoves:
	native_species_form MAGBY, PLAIN_FORM
	db BARRIER
	db BELLY_DRUM
	db CROSS_CHOP
	db FLARE_BLITZ
	db FOCUS_ENERGY
	db KARATE_CHOP
	db MACH_PUNCH
	db SCREECH
	db $ff

MiltankEggSpeciesMoves:
	native_species_form MILTANK, PLAIN_FORM
	db DIZZY_PUNCH
	db REVERSAL
	db SEISMIC_TOSS
	db $ff

LarvitarEggSpeciesMoves:
	native_species_form LARVITAR, PLAIN_FORM
	db DRAGON_DANCE
	db FOCUS_ENERGY
	db PURSUIT
	db STOMP
	db OUTRAGE
	db ANCIENTPOWER
	db IRON_HEAD
	db $ff

AzurillEggSpeciesMoves:
	native_species_form AZURILL, PLAIN_FORM
	db BELLY_DRUM
	db FORESIGHT
	db FUTURE_SIGHT
	db PERISH_SONG
	db SUPERSONIC
	db LIGHT_SCREEN
	db AMNESIA
	db CALM_MIND
	db $ff

WynautEggSpeciesMoves:
	native_species_form WYNAUT, PLAIN_FORM
	db CHARM
	db ENCORE
	db $ff

BonslyEggSpeciesMoves:
	native_species_form BONSLY, PLAIN_FORM
	db DEFENSE_CURL
	db EXPLOSION
	db $ff

MimeJrEggSpeciesMoves:
	native_species_form MIME_JR_, PLAIN_FORM
	db CONFUSE_RAY
	db FUTURE_SIGHT
	db HYPNOSIS
	db NASTY_PLOT
	db TRICK
	db $ff

HappinyEggSpeciesMoves:
	native_species_form HAPPINY, PLAIN_FORM
	db HEAL_BELL
	db $ff

MantykeEggSpeciesMoves:
	native_species_form MANTYKE, PLAIN_FORM
	db HAZE
	db MIRROR_COAT
	db SPLASH
	db HYDRO_PUMP
	db GUNK_SHOT
	db $ff

MunchlaxEggSpeciesMoves:
	native_species_form MUNCHLAX, PLAIN_FORM
	db CHARM
	db COUNTER
	db CURSE
	db DOUBLE_EDGE
	db LICK
	db GUNK_SHOT
	db $ff

NoEggSpeciesMoves:
	dw 0 ; no hatchling species
	db NO_FORM
	db $ff

if DEF(NATIVE_SPECIES_TEST)
WideTestEggSpeciesMoves:
	native_species_form WIDE_TEST_SPECIES, PLAIN_FORM
	db TACKLE, $ff
endc
