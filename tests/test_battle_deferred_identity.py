"""CPU regressions for delayed-user decoding, Love Ball roots and armor remapping."""
import argparse
from pathlib import Path
from pyboy import PyBoy


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('rom', type=Path)
    rom = ap.parse_args().rom
    syms = {}
    for line in rom.with_suffix('.sym').read_text().splitlines():
        f = line.split()
        if len(f) == 2 and ':' in f[0]:
            syms[f[1]] = tuple(int(v, 16) for v in f[0].split(':'))
    def addr(s): return syms[s][1]
    p = PyBoy(str(rom), window='null', sound_emulated=False, cgb=True, log_level='ERROR')
    m, r = p.memory, p.register_file
    def put(s, v): m[addr(s)] = v
    def reset(marker):
        for bank in (1, 2):
            m[0xff70] = bank
            m[0xd000:0xe000] = [0] * 4096
        m[0xff70] = 1
        m[addr('wPokemonDataFormat'):addr('wPokemonDataFormat')+2] = list(marker.to_bytes(2, 'little'))
        put('wPlayerFutureSightCount', 0)
        put('wEnemyFutureSightCount', 0)
    def seed(n):
        m[0xff70] = 2
        at = addr('wPokemonIndexTableEntries')+12
        m[at:at+2] = list(n.to_bytes(2, 'little'))
        m[0xff70] = 1
    def call(s, hl=0xc222):
        bank, target = syms[s]
        bank = bank or 1
        m[0x2000] = bank
        put('hROMBank', bank)
        m[0xc100:0xc106] = [0xf3, 0xcd, target & 255, target >> 8, 0x18, 0xfe]
        r.B, r.C, r.D, r.E, r.HL = 0x12, 0x34, 0x56, 0x78, hl
        r.SP, r.PC = 0xc0ff, 0xc100
        p.tick(4, False, False)
        assert (r.PC, r.SP) == (0xc104, 0xc0ff), (s, hex(r.PC))
        assert m[addr('hROMBank')] == bank
        assert m[0xff70] & 7 == 1
    count = 0
    try:
        m[0xff50] = 1
        m[0xffff] = m[0xff0f] = m[0xff40] = 0
        for marker in (0, 0x16bc, 0x00bc, 0x1600):
            for turn in (0, 1):
                for slot in range(6):
                    for deferred in (False, True):
                        for match in (False, True):
                            reset(marker)
                            seed(257)
                            active = (slot+1) % 6 if deferred else slot
                            put('hBattleTurn', turn)
                            put('wCurBattleMon', active if not turn else 0)
                            put('wCurOTMon', active if turn else 0)
                            user = 'wOTPartyMon' if turn else 'wPartyMon'
                            opponent = 'wPartyMon' if turn else 'wOTPartyMon'
                            put(user+str(slot+1)+'Species', 7 if marker == 0x16bc and not turn else 1)
                            put(user+str(slot+1)+'Form', 0xe1)
                            put(opponent+'1Species', (7 if marker == 0x16bc and turn else 1) if match else 25)
                            if not match and turn and marker == 0x16bc:
                                m[0xff70] = 2
                                at = addr('wPokemonIndexTableEntries')+48
                                m[at:at+2] = [25, 0]
                                m[0xff70] = 1
                            put(opponent+'1Form', 0x21 if match else 1)
                            if deferred:
                                put('wEnemyFutureSightCount' if turn else 'wPlayerFutureSightCount', (slot+1)<<4)
                            call('GetTrueUserPartySpeciesAndForm')
                            assert (r.A, r.B, r.C) == (1, 0x21, 1), (marker, turn, slot, deferred, r.A, r.B)
                            assert r.HL == addr(user+str(slot+1)+'Species')
                            assert (r.D, r.E) == (0x56, 0x78)
                            call('BattlePartyRootsMatch')
                            assert bool(r.F & 0x80) == match, (marker, turn, slot, deferred, match)
                            assert (r.B, r.C, r.D, r.E, r.HL) == (0x12, 0x34, 0x56, 0x78, 0xc222)
                            count += 1
        for marker in (0, 0x16bc, 0x00bc, 0x1600):
            for turn in (0, 1):
                for player, enemy in ((133, 133), (150, 133), (133, 150)):
                    for genders in ((0, 0), (0, 0x80), (0x80, 0), (0x80, 0x80)):
                        reset(marker)
                        seed(player)
                        put('hBattleTurn', turn)
                        put('wCurBattleMon', 0)
                        put('wCurOTMon', 0)
                        put('wPartyMon1Species', 7 if marker == 0x16bc else player)
                        put('wPartyMon1Form', 1 | genders[0])
                        put('wOTPartyMon1Species', enemy)
                        put('wOTPartyMon1Form', 1 | genders[1])
                        call('CheckOppositeGender')
                        assert bool(r.F & 0x10) == (150 in (player, enemy))
                        if 150 not in (player, enemy):
                            assert bool(r.F & 0x80) == (genders[0] == genders[1])
                        count += 1
        for marker in (0, 0x16bc):
            for metadata in (0, 0x40, 0x80, 0xc0):
                for slot in range(6):
                    reset(marker)
                    seed(150)
                    name = 'wPartyMon'+str(slot+1)
                    put('wCurPartyMon', slot)
                    put(name+'Species', 7 if marker else 150)
                    put(name+'Form', 1 | metadata)
                    for armor in (True, False):
                        put(name+'Item', 0xbe if armor else 0)
                        call('UpdateMewtwoForm', addr(name+'Item'))
                        assert m[addr(name+'Form')] == (2 if armor else 1) | metadata, (marker, metadata, slot, armor, m[addr(name+'Form')], m[addr('wCurPartySpecies')], m[addr(name+'Item')])
                        if marker:
                            transient = m[addr(name+'Species')]
                            m[0xff70] = 2
                            at = addr('wPokemonIndexTableEntries')+2*(transient-1)
                            n = int.from_bytes(m[at:at+2], 'little')
                            m[0xff70] = 1
                            assert (n > 291) if armor else (n == 150), (slot, armor, n)
                        else:
                            assert m[addr(name+'Species')] == 150
                        count += 1
        print(f'PASS: {count} delayed/ordinary user, species-match, gender and armor-form cases')
    finally:
        p.stop(save=False)


if __name__ == '__main__':
    main()
