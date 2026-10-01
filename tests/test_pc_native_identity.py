"""CPU regression tests for party/PC identity boundaries and native box records."""
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
    cases = ((25, 25, 1), (257, 1, 0x21), (alolan, 26, 2))
    p = PyBoy(str(rom), window='null', sound_emulated=False, cgb=True, log_level='ERROR')
    m, r = p.memory, p.register_file
    def put(s, v): m[addr(s)] = v
    def reset(marker):
        for bank in (1, 2):
            m[0xff70] = bank
            m[0xd000:0xe000] = [0] * 4096
        m[0xff70] = 1
        m[addr('wPokemonDataFormat'):addr('wPokemonDataFormat')+2] = list(marker.to_bytes(2, 'little'))
    def call(s, b=0, c=0):
        bank, target = syms[s]
        bank = bank or 1
        m[0x2000] = bank
        put('hROMBank', bank)
        m[0xc100:0xc106] = [0xf3, 0xcd, target & 255, target >> 8, 0x18, 0xfe]
        r.B, r.C, r.SP, r.PC = b, c, 0xc0ff, 0xc100
        p.tick(4, False, False)
        assert (r.PC, r.SP) == (0xc104, 0xc0ff), (s, hex(r.PC))
        assert m[addr('hROMBank')] == bank
        assert m[0xff70] & 7 == 1
    def native(slot):
        m[0xff70] = 2
        at = addr('wPokemonIndexTableEntries') + 2 * (slot - 1)
        value = int.from_bytes(m[at:at+2], 'little')
        m[0xff70] = 1
        return value
    def seed(n):
        m[0xff70] = 2
        at = addr('wPokemonIndexTableEntries') + 12
        m[at:at+2] = list(n.to_bytes(2, 'little'))
        m[0xff70] = 1
    stride = addr('wPartyMon2Species') - addr('wPartyMon1Species')
    formoff = addr('wTempMonForm') - addr('wTempMonSpecies')
    transfer_count = box_count = 0
    try:
        m[0xff50] = 1
        m[0xffff] = m[0xff0f] = m[0xff40] = 0
        for marker in (0, 0x16bc, 0x00bc, 0x1600):
            for n, species, form in cases:
                for metadata in (0, 0x40, 0x80, 0xc0):
                    for flags in (0, 1, 0x80, 0x81):
                        for slot in range(6):
                            reset(marker)
                            seed(n)
                            prefix = 'wOTPartyMon1' if flags & 0x80 else 'wPartyMon1'
                            party = addr(prefix+'Species') + stride * slot
                            temp = addr('wTempMonSpecies')
                            record = [(i * 17 + 9) & 255 for i in range(stride)]
                            record[0] = species
                            record[formoff] = form | metadata
                            encoded = record.copy()
                            if marker == 0x16bc and not flags & 0x80:
                                encoded[0] = 7
                            source, dest = (party, temp) if flags & 1 else (temp, party)
                            m[source:source+stride] = encoded if flags & 1 else record
                            call('CopyBetweenPartyAndTemp', flags, slot+1)
                            result = list(m[dest:dest+stride])
                            if not flags & 1 and marker == 0x16bc and not flags & 0x80:
                                assert native(result[0]) == n
                                result[0] = species
                            assert result == record, (marker, n, metadata, flags, slot, result, record)
                            transfer_count += 1
        for n, species, form in cases:
            for metadata in (0, 0x40, 0x80, 0xc0):
                for mode in ('native', 'legacy', 'corrupt', 'zero', 'unused', 'out_of_range'):
                    reset(0x16bc)
                    put('wTempMonSpecies', species)
                    put('wTempMonForm', form | metadata)
                    put('wTempMonLevel', 20)
                    put('wTempMonExtra', 0xfc)
                    for name, size in (('wTempMonNickname', 11), ('wTempMonOT', 8)):
                        m[addr(name):addr(name)+size] = [0x80] * (size-1) + [0x50]
                    call('EncodeTempMon')
                    assert m[addr('wEncodedTempMonSpecies')] == 0
                    at = addr('wEncodedTempMonExtra')
                    assert int.from_bytes(m[at+1:at+3], 'little') == n
                    assert m[at] == 0xfc
                    if mode == 'legacy':
                        put('wEncodedTempMonSpecies', species)
                        m[at+1:at+3] = [0, 0]
                        call('ChecksumTempMon')
                    elif mode in ('zero', 'unused', 'out_of_range'):
                        m[at+1:at+3] = {'zero': [0, 0], 'unused': [0, 1], 'out_of_range': [255, 255]}[mode]
                        call('ChecksumTempMon')
                    elif mode == 'corrupt':
                        m[addr('wEncodedTempMonItem')] ^= 1
                    call('DecodeTempMon')
                    if mode in ('native', 'legacy'):
                        assert not r.F & 0x10, (n, metadata, mode)
                        assert m[addr('wTempMonSpecies')] == species
                        assert m[addr('wTempMonForm')] == form | metadata
                        assert m[addr('wTempMonExtra')] == 0xfc
                    else:
                        assert r.F & 0x10, (n, metadata, mode)
                    box_count += 1
        print(f'PASS: {transfer_count} party/temp transfers and {box_count} full native/legacy/corrupt box round-trips')
    finally:
        p.stop(save=False)


if __name__ == '__main__':
    main()
