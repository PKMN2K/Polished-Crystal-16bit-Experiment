"""CPU tests of RAM migration and primary/backup conversion-table integrity."""
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
    def reset():
        for bank in (1, 2):
            m[0xff70] = bank
            m[0xd000:0xe000] = [0] * 4096
        m[0xff70] = 1
    def call(s, bc=0, hl=0xc222):
        m[0] = 0x0a
        m[0x4000] = syms['sSRAMAccessCount'][0]
        m[addr('sSRAMAccessCount')] = 0
        put('wSRAMAccessCount', 1)
        bank, target = syms[s]
        bank = bank or 1
        m[0x2000] = bank
        put('hROMBank', bank)
        m[0xc100:0xc106] = [0xf3, 0xcd, target & 255, target >> 8, 0x18, 0xfe]
        r.B, r.C, r.HL = bc >> 8, bc & 255, hl
        r.SP, r.PC = 0xc0ff, 0xc100
        p.tick(8, False, False)
        assert (r.PC, r.SP) == (0xc104, 0xc0ff), (s, hex(r.PC))
        assert m[addr('hROMBank')] == bank
        assert m[0xff70] & 7 == 1
    def sram(symbol):
        m[0] = 0x0a
        m[0x4000] = syms[symbol][0]
    def table_entry(slot): return addr('wPokemonIndexTableEntries') + 2*(slot-1)
    count = 0
    try:
        m[0xff50] = 1
        m[0xffff] = m[0xff0f] = m[0xff40] = 0
        for version in (10, 11):
            reset()
            sram('sSaveVersion')
            at = addr('sSaveVersion')
            m[at:at+2] = [0, version]
            call('VerifyGameVersion')
            assert r.F & 0x80
            count += 1
        for marker in (0, 0x00bc, 0x1600):
            for pressure in (False, True):
                for metadata in (0, 0x40, 0x80, 0xc0):
                    reset()
                    m[addr('wPokemonDataFormat'):addr('wPokemonDataFormat')+2] = list(marker.to_bytes(2, 'little'))
                    records = []
                    # Eight distinct identities exceed the recent-ID protection
                    # once other allocations intervene; locks are the invariant.
                    for i, name in enumerate([f'wPartyMon{n}Species' for n in range(1, 7)] + ['wBreedMon1Species', 'wBreedMon2Species']):
                        at = addr(name)
                        species = 25 + i
                        form = 1 | metadata
                        m[at] = species
                        m[at + addr('wPartyMon1Form') - addr('wPartyMon1Species')] = form
                        records.append((at, species, form))
                    put('wPartyCount', 1)  # Contest-hidden records also migrate.
                    if pressure:
                        m[0xff70] = 2
                        for slot in range(1, 101):
                            at = table_entry(slot)
                            m[at:at+2] = list((1000+slot).to_bytes(2, 'little'))
                        # Reuse a low old slot before collection is forced.
                        m[table_entry(1):table_entry(1)+2] = [25, 0]
                        put('wPokemonIndexTableUsedSlots', 100)
                        m[0xff70] = 1
                    call('MigrateLegacyPlayerPokemonData')
                    assert list(m[addr('wPokemonDataFormat'):addr('wPokemonDataFormat')+2]) == [0xbc, 0x16]
                    for at, species, form in records:
                        slot = m[at]
                        assert m[at+addr('wPartyMon1Form')-addr('wPartyMon1Species')] == form
                        m[0xff70] = 2
                        assert int.from_bytes(m[table_entry(slot):table_entry(slot)+2], 'little') == species
                        assert list(m[addr('wPokemonIndexTableLockedEntries'):addr('wPokemonIndexTableLockedEntries')+8]) == [0]*8
                        m[0xff70] = 1
                    before = [m[at] for at, _, _ in records]
                    call('MigrateLegacyPlayerPokemonData')
                    assert [m[at] for at, _, _ in records] == before
                    count += 1
        # Native-word storage must allocate the supplied BC, not the address
        # of the destination. High values here test storage, not game support.
        for n in (25, 257, 337, 513, 0x1234):
            reset()
            at = addr('wRoamMon1Species')
            call('StoreRoamMonNativeSpecies', bc=n, hl=at)
            assert r.HL == at
            slot = m[at]
            m[0xff70] = 2
            assert int.from_bytes(m[table_entry(slot):table_entry(slot)+2], 'little') == n
            m[0xff70] = 1
            count += 1
        for prefix, save, verify, load in (
            ('s', 'SavePokemonIndexTable', 'VerifyPokemonIndexTable', 'LoadPokemonIndexTable'),
            ('sBackup', 'SaveBackupPokemonIndexTable', 'VerifyBackupPokemonIndexTable', 'LoadBackupPokemonIndexTable'),
        ):
            for damaged in (None, 0, 1, 127, 255):
                reset()
                put('wPokemonDataFormat', 0xbc)
                m[addr('wPokemonDataFormat')+1] = 0x16
                put('wPartyMon1Species', 7)
                put('wPartyMon1Form', 1)
                m[0xff70] = 2
                m[table_entry(7):table_entry(7)+2] = [25, 0]
                put('wPokemonIndexTableUsedSlots', 1)
                m[0xff70] = 1
                call('SavePokemonData' if prefix == 's' else 'SaveBackupPokemonData')
                sram('sSaveVersion')
                assert list(m[addr('sSaveVersion'):addr('sSaveVersion')+2]) == [0, 11]
                call(save)
                sram(prefix+'PokemonData')
                at = addr(prefix+'PokemonData') + addr('wPokemonDataFormat')-addr('wPokemonData')
                m[at:at+2] = [0xbc, 0x16]
                if damaged is not None:
                    m[addr(prefix+'PokemonIndexTable')+damaged] ^= 1
                call(verify)
                assert bool(r.F & 0x80) == (damaged is None), (verify, damaged, hex(r.F))
                if damaged is None:
                    m[0xff70] = 2
                    m[0xd000:0xe000] = [0]*4096
                    m[0xff70] = 1
                    call(load)
                    m[0xff70] = 2
                    assert list(m[table_entry(7):table_entry(7)+2]) == [25, 0]
                    m[0xff70] = 1
                count += 1
            for oldmagic in (0, 0x16bd):
                for marker in (0, 0x16bc):
                    sram(prefix+'PokemonIndexTableMagic')
                    at = addr(prefix+'PokemonIndexTableMagic')
                    m[at:at+2] = list(oldmagic.to_bytes(2, 'little'))
                    at = addr(prefix+'PokemonData') + addr('wPokemonDataFormat')-addr('wPokemonData')
                    m[at:at+2] = list(marker.to_bytes(2, 'little'))
                    m[at+2:at+4] = [0, 0]
                    call(verify)
                    assert bool(r.F & 0x80) == (marker == 0), (verify, oldmagic, marker)
                    count += 1
            # Once the envelope version is inside checksummed game data,
            # damaged/missing magic must not be mistaken for an old save.
            for damaged_magic in (0, 0x16bc, 0x16bd, 0xffff, 0x16bf):
                sram(prefix+'PokemonIndexTableMagic')
                at = addr(prefix+'PokemonIndexTableMagic')
                m[at:at+2] = list(damaged_magic.to_bytes(2, 'little'))
                at = addr(prefix+'PokemonData') + addr('wPokemonDataFormat')-addr('wPokemonData')
                m[at:at+4] = [0, 0, 0xbe, 0x16]
                call(verify)
                assert not r.F & 0x80, (verify, damaged_magic)
                count += 1
        print(f'PASS: {count} migration/idempotence/collection-pressure and primary/backup save-integrity cases')
    finally:
        p.stop(save=False)


if __name__ == '__main__':
    main()
