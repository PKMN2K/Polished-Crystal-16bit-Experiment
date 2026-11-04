"""Post-battle berry cleanup visits exactly the active party after species decoding."""
import argparse
from pathlib import Path
from pyboy import PyBoy


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('rom', type=Path)
    rom = ap.parse_args().rom
    s = {}
    for line in rom.with_suffix('.sym').read_text().splitlines():
        f = line.split()
        if len(f) == 2 and ':' in f[0]: s[f[1]] = tuple(int(x, 16) for x in f[0].split(':'))
    def at(n): return s[n][1]
    data = rom.read_bytes()
    wide = None
    if 'NativeWideTestIdentity' in s:
        bank, addr = s['NativeWideTestIdentity']; addr = bank*0x4000+addr%0x4000
        wide = int.from_bytes(data[addr:addr+2], 'little')
    p = PyBoy(str(rom), window='null', sound_emulated=False, cgb=True, log_level='ERROR')
    p.set_emulation_speed(0)
    m, r = p.memory, p.register_file
    def call(name, a=0, bc=0, hl=0xc280):
        bank, target = s[name]; bank = bank or 1
        m[0x2000] = bank; m[at('hROMBank')] = bank
        m[0xc100:0xc106] = [0xf3, 0xcd, target&255, target>>8, 0x18, 0xfe]
        r.A, r.B, r.C, r.HL = a, bc>>8, bc&255, hl
        r.SP, r.PC = 0xc0ff, 0xc100
        for _ in range(40):
            p.tick(1, False, False)
            if (r.PC, r.SP) == (0xc104, 0xc0ff): break
        assert (r.PC, r.SP) == (0xc104, 0xc0ff), (name, hex(r.PC), hex(r.SP))
        assert m[at('hROMBank')] == bank and m[0xff70]&7 == 1
    try:
        cases = 0
        for transient in (False, True):
            for count in range(1, 7):
                for roster in ([25, 213, 257, 201, 1, wide or 277], [213]*6):
                    m[0xff50] = 1
                    m[0xffff] = m[0xff0f] = m[0xff40] = 0
                    m[0xc000:0xd000] = [0]*0x1000
                    for bank in (1,2):
                        m[0xff70] = bank; m[0xd000:0xe000] = [0]*0x1000
                    m[0xff70] = 1
                    if transient: call('InitializeNativePokemonDataForNewGame')
                    m[at('wPartyCount')] = count
                    for i, native in enumerate(roster, 1):
                        if transient:
                            call('GetPokemonIDFromIndex', hl=native)
                            species, form = r.A, 1
                        else:
                            call('GetLegacySpeciesAndFormFromNativeIDBC', a=1, bc=native)
                            species, form = r.A, r.B
                        m[at(f'wPartyMon{i}Species')] = species
                        m[at(f'wPartyMon{i}Form')] = form
                        m[at(f'wPartyMon{i}Item')] = 0x44  # Oran Berry
                    before = bytes(m[at('wPartyMons'):at('wPartyMon6') + at('wPartyMon2')-at('wPartyMon1')])
                    visited = []
                    label = 'GivePokerusAndConvertBerries.berries_loop'
                    p.hook_register(*s[label], lambda _: visited.append(r.HL), None)
                    try: call('GivePokerusAndConvertBerries')
                    finally: p.hook_deregister(*s[label])
                    expected = [at(f'wPartyMon{i}Species') for i in range(1, count+1)]
                    assert visited == expected, ('party traversal', transient, count, visited, expected)
                    size = at('wPartyMon2')-at('wPartyMon1')
                    after = bytes(m[at('wPartyMons'):at('wPartyMons')+6*size])
                    assert after[count*size:] == before[count*size:], 'inactive party changed'
                    for i, native in enumerate(roster[:count], 1):
                        item = m[at(f'wPartyMon{i}Item')]
                        assert item in ((0x44, 0x5c) if native == 213 else (0x44,)), ('wrong berry conversion', native, item)
                    cases += 1
        print(f'PASS {cases} post-battle party traversals (sizes 1-6, legacy/native, mixed/Shuckle); no ROM stubs')
    finally:
        p.stop(save=False)


if __name__ == '__main__': main()
