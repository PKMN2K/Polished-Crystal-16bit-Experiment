"""Real daycare compatibility and egg generation from native parent records.

No ROM routines are patched. Exercises register preservation across both
parent decoders, native hatchling records, forms, inherited balls and PP.
"""
import argparse
from pathlib import Path
from pyboy import PyBoy


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('rom', type=Path)
    rom = ap.parse_args().rom
    syms = {}
    for line in rom.with_suffix('.sym').read_text().splitlines():
        fields = line.split()
        if len(fields) == 2 and ':' in fields[0]:
            syms[fields[1]] = tuple(int(v, 16) for v in fields[0].split(':'))
    def addr(label): return syms[label][1]
    data = rom.read_bytes()
    bank, at = syms['NativeVariantIdentityTable']
    offset = bank * 0x4000 + at - 0x4000
    # Find the canonical native ID for Alolan Vulpix in the compiled manifest.
    alolan_vulpix = next(int.from_bytes(data[i:i+2], 'little')
                         for i in range(offset, offset+46*5, 5)
                         if data[i+2:i+5] == bytes((37, 0, 2)))
    p = PyBoy(str(rom), window='null', sound_emulated=False, cgb=True, log_level='ERROR')
    m, r = p.memory, p.register_file
    def put(label, value): m[addr(label)] = value
    def invoke(label, *, a=0, bc=0, hl=0xc280, de=0xc380, ticks=6):
        bank, target = syms[label]
        bank = bank or 1
        m[0x2000] = bank
        put('hROMBank', bank)
        m[0xc100:0xc106] = [0xf3, 0xcd, target & 255, target >> 8, 0x18, 0xfe]
        r.A, r.B, r.C, r.HL, r.D, r.E = a, bc >> 8, bc & 255, hl, de >> 8, de & 255
        r.SP, r.PC = 0xc0ff, 0xc100
        p.tick(ticks, False, False)
        assert (r.PC, r.SP) == (0xc104, 0xc0ff), (label, hex(r.PC), hex(r.SP))
        assert m[addr('hROMBank')] == bank and m[0xff70] & 7 == 1
    try:
        m[0xff50] = 1
        m[0xffff] = m[0xff0f] = m[0xff40] = 0
        cases = ((25, 1, 172, 1), (alolan_vulpix, 2, alolan_vulpix, 2),
                 (0x123, 0x21, 56, 1), (129, 20, 129, 20))
        for native, form, child, child_form in cases:
            for bank in (1, 2):
                m[0xff70] = bank
                m[0xd000:0xe000] = [0]*4096
            m[0xff70] = 1
            put('wPokemonDataFormat', 0xbc)
            m[addr('wPokemonDataFormat')+1] = 0x16
            invoke('GetPokemonIDFromIndex', hl=native)
            slot = r.A
            for parent in (1, 2):
                put(f'wBreedMon{parent}Species', slot)
                put(f'wBreedMon{parent}Form', form)
                put(f'wBreedMon{parent}CaughtBall', 4+parent)
                put(f'wBreedMon{parent}Level', 30)
            invoke('CheckBreedmonCompatibility')
            assert m[addr('wBreedingCompatibility')] == 0, (native, 'same gender')
            put('wBreedMon1Form', form | 0x80)
            invoke('CheckBreedmonCompatibility')
            assert m[addr('wBreedingCompatibility')] == 2, (native, 'opposite gender')
            invoke('DayCare_GenerateEgg', ticks=80)
            assert m[addr('wTempMonForm')] & 0x3f == child_form, (native, hex(m[addr('wTempMonForm')]))
            assert m[addr('wTempMonForm')] & 0x40
            assert m[addr('wTempMonCaughtBall')] in (5, 6), native
            assert m[addr('wTempMonLevel')] == 1
            assert m[addr('wTempMonHappiness')] > 0
            assert m[addr('wTempMonMoves')] and m[addr('wTempMonPP')]
            invoke('GetNativeSpeciesIDFromLegacyPokemonDataStruct', hl=addr('wTempMonSpecies'),
                   de=addr('wTempMonForm')-addr('wTempMonSpecies'))
            assert r.B*256+r.C == child, (native, hex(r.B*256+r.C), hex(child))
            for parent in (1, 2):
                assert m[addr(f'wBreedMon{parent}Species')] == slot
                assert m[addr(f'wBreedMon{parent}CaughtBall')] == 4+parent
        print('PASS: native daycare compatibility and complete egg generation; baby species, regional and cosmetic forms, extended roots, inherited balls and PP; no ROM stubs')
    finally:
        p.stop(save=False)


if __name__ == '__main__':
    main()
