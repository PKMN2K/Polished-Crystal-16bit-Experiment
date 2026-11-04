"""Native Pokédex records: full roster, three orders, cursor and form changes."""
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
    def order(label):
        bank, at = syms[label]
        offset = bank*0x4000+at-0x4000
        return [int.from_bytes(data[i:i+2], 'little') for i in range(offset, offset+289*2, 2)]
    national = list(range(1, 255)) + list(range(257, 292))
    johto, alphabetical = order('NewPokedexOrder'), order('AlphabeticalPokedexOrder')
    assert sorted(johto) == sorted(alphabetical) == national
    p = PyBoy(str(rom), window='null', sound_emulated=False, cgb=True, log_level='ERROR')
    m, r = p.memory, p.register_file
    def put(label, value): m[addr(label)] = value
    def invoke(label, *, a=0, bc=0, hl=0xc280, ticks=6):
        bank, target = syms[label]
        bank = bank or 1
        m[0x2000] = bank
        put('hROMBank', bank)
        m[0xc100:0xc106] = [0xf3, 0xcd, target & 255, target >> 8, 0x18, 0xfe]
        r.A, r.B, r.C, r.HL = a, bc >> 8, bc & 255, hl
        r.SP, r.PC = 0xc0ff, 0xc100
        p.tick(ticks, False, False)
        assert (r.PC, r.SP) == (0xc104, 0xc0ff), (label, hex(r.PC), hex(r.SP))
        assert m[addr('hROMBank')] == bank and m[0xff70] & 7 == 1
    def rows():
        m[0xff70] = syms['wDexMons'][0]
        start, end = addr('wDexMons'), addr('wDexMonsEnd')
        records = [(int.from_bytes(m[i:i+2], 'little'), m[i+2]) for i in range(start, end, 3)]
        m[0xff70] = 1
        assert records[289] == (0, 0)
        return records[:289]
    try:
        m[0xff50] = 1
        m[0xffff] = m[0xff0f] = m[0xff40] = 0
        for bank in range(1, 8):
            m[0xff70] = bank
            m[0xd000:0xe000] = [0]*4096
        m[0xff70] = 1
        for start, end in (('wPokedexSeen', 'wEndPokedexSeen'), ('wPokedexCaught', 'wEndPokedexCaught')):
            m[addr(start):addr(end)] = [255]*(addr(end)-addr(start))
        # The LCD setup normally builds this native-root -> Johto-number cache.
        m[0xff70] = syms['wDexConversionTable'][0]
        for position, native in enumerate(johto, 1):
            offset = addr('wDexConversionTable')+2*national.index(native)
            m[offset:offset+2] = list(position.to_bytes(2, 'big'))
        m[0xff70] = 1
        for mode, expected in ((1, national), (0, johto)):
            put('wPokedexMode', mode)
            invoke('Pokedex_InitData', ticks=240)
            records = rows()
            assert [native for native, _ in records] == expected, mode
            for index, (native, form) in enumerate(records):
                put('wPokedex_DisplayMode', 0)
                put('wPokedex_Offset', index//5)
                put('wPokedex_CursorPos', index % 5)
                invoke('Pokedex_GetCursorSpecies', ticks=1)
                assert r.B == form
                invoke('GetNativeRootFromRuntimeBC', bc=r.B*256+r.C, ticks=1)
                assert r.B*256+r.C == native, (mode, index)
        put('wPokedexMode', 1)
        put('wPokedex_SearchOrder', 1)
        m[addr('wPokedex_SearchData'):addr('wPokedex_SearchDataEnd')] = [0]*6
        invoke('Pokedex_GetSearchResults', ticks=240)
        assert not r.F & 0x80
        assert [native for native, _ in rows()] == alphabetical
        # Form cycling must update byte three, preserving the complete root word.
        index = alphabetical.index(129)
        put('wPokedex_Offset', index//5)
        put('wPokedex_CursorPos', index % 5)
        before = rows()[index]
        invoke('Pokedex_ChangeForm')
        after = rows()[index]
        assert before[0] == after[0] == 129 and before[1] != after[1]
        print('PASS: 289 native Pokédex records in national/Johto/alphabetical order; every cursor slot, blank padding and cosmetic form cycling')
    finally:
        p.stop(save=False)


if __name__ == '__main__':
    main()
