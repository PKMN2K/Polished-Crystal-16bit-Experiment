"""CPU tests for direct native party/daycare identity and base-data lookup."""
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
    data = rom.read_bytes()
    bank, at = syms['NativeVariantIdentityTable']
    start = bank*0x4000 + at - 0x4000
    alolan = next(int.from_bytes(data[i:i+2], 'little') for i in range(start, start+230, 5)
                  if int.from_bytes(data[i+2:i+4], 'little') == 26 and data[i+4] == 2)
    base_size = addr('wCurBaseDataEnd') - addr('wCurBaseData')
    bank, at = syms['BaseDataRecords']
    base_start = bank*0x4000 + at - 0x4000
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
    def call(s, hl=0xc222, de=0x5678):
        bank, target = syms[s]
        bank = bank or 1
        m[0x2000] = bank
        put('hROMBank', bank)
        m[0xc100:0xc106] = [0xf3, 0xcd, target & 255, target >> 8, 0x18, 0xfe]
        r.B, r.C, r.D, r.E, r.HL = 0x12, 0x34, de >> 8, de & 255, hl
        r.SP, r.PC = 0xc0ff, 0xc100
        p.tick(4, False, False)
        assert (r.PC, r.SP) == (0xc104, 0xc0ff), (s, hex(r.PC))
        assert m[addr('hROMBank')] == bank
        assert m[0xff70] & 7 == 1
    count = 0
    form_offset = addr('wPartyMon1Form') - addr('wPartyMon1Species')
    records = [f'wPartyMon{i}Species' for i in range(1, 7)] + ['wBreedMon1Species', 'wBreedMon2Species']
    globals_ = ('wCurSpecies', 'wCurPartySpecies', 'wCurForm')
    def snapshot_table():
        m[0xff70] = 2
        result = list(m[addr('wPokemonIndexTable'):addr('wPokemonIndexTableEnd')])
        m[0xff70] = 1
        return result
    try:
        m[0xff50] = 1
        m[0xffff] = m[0xff0f] = m[0xff40] = 0
        for marker in (0, 0x16bc, 0x00bc, 0x1600):
            for native, root, form in ((25, 25, 1), (257, 1, 0x21), (alolan, 26, 2)):
                for metadata in (0, 0x40, 0x80, 0xc0):
                    for name in records:
                        reset(marker)
                        seed(native)
                        source = addr(name)
                        m[source] = 7 if marker == 0x16bc else root
                        m[source+form_offset] = form | metadata
                        for g, v in zip(globals_, (91, 92, 3)):
                            put(g, v)
                        before = snapshot_table()
                        call('GetNativeSpeciesIDFromPokemonDataStruct', source, form_offset)
                        assert (r.B << 8) | r.C == native
                        assert r.HL == source and (r.D << 8) | r.E == form_offset
                        call('GetBaseDataFromPokemonDataStruct', source)
                        expected = list(data[base_start+(native-1)*base_size:base_start+native*base_size])
                        assert list(m[addr('wCurBaseData'):addr('wCurBaseDataEnd')]) == expected, (marker, native, name)
                        assert (r.B, r.C, r.D, r.E, r.HL) == (0x12, 0x34, 0x56, 0x78, source)
                        assert not r.F & 0x10
                        assert [m[addr(g)] for g in globals_] == [91, 92, 3]
                        assert snapshot_table() == before
                        assert m[source] == (7 if marker == 0x16bc else root)
                        assert m[source+form_offset] == form | metadata
                        count += 1
        for name in records:
            for marker in (0, 0x16bc, 0x00bc, 0x1600):
                reset(marker)
                m[addr('wCurBaseData'):addr('wCurBaseDataEnd')] = [0xa5]*base_size
                call('GetBaseDataFromPokemonDataStruct', addr(name))
                assert r.F & 0x10
                assert list(m[addr('wCurBaseData'):addr('wCurBaseDataEnd')]) == [0xa5]*base_size
                count += 1
            # Deliberately disagree with the stored form to prove lookup uses
            # the native identity, not a legacy root/form reconstruction.
            for metadata in (0, 0x40, 0x80, 0xc0):
                reset(0x16bc)
                seed(alolan)
                put(name, 7)
                m[addr(name)+form_offset] = 1 | metadata
                call('GetBaseDataFromPokemonDataStruct', addr(name))
                expected = list(data[base_start+(alolan-1)*base_size:base_start+alolan*base_size])
                assert list(m[addr('wCurBaseData'):addr('wCurBaseDataEnd')]) == expected
                count += 1
            # Word-preservation only: these are not playable catalog entries.
            for native in (0x0201, 0x1234):
                for metadata in (0, 0x40, 0x80, 0xc0):
                    reset(0x16bc)
                    seed(native)
                    put(name, 7)
                    m[addr(name)+form_offset] = 1 | metadata
                    call('GetNativeSpeciesIDFromPokemonDataStruct', addr(name), form_offset)
                    assert (r.B << 8) | r.C == native
                    assert r.HL == addr(name)
                    count += 1
        print(f'PASS: {count} direct native identity/base-data cases; all player/daycare slots, markers, metadata, exact ROM data, empty records and high-word preservation')
    finally:
        p.stop(save=False)


if __name__ == '__main__':
    main()
