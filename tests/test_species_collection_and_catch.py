"""Run conversion-table collection and caught-party copy CPU regressions.

Usage: python tests/test_species_collection_and_catch.py ROM.gbc
Requires PyBoy 2.7.0 and the ROM's matching .sym file; never uses a game save.
"""
import argparse
from pathlib import Path
from pyboy import PyBoy


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    args = parser.parse_args()
    symbols = {}
    for line in args.rom.with_suffix('.sym').read_text().splitlines():
        fields = line.split()
        if len(fields) == 2 and ':' in fields[0]:
            symbols[fields[1]] = tuple(int(x, 16) for x in fields[0].split(':'))
    def addr(name):
        return symbols[name][1]
    p = PyBoy(str(args.rom), window='null', sound_emulated=False, cgb=True, log_level='ERROR')
    m, r = p.memory, p.register_file
    def write(name, value):
        bank, address = symbols[name]
        if 0xD000 <= address < 0xE000:
            m[0xFF70] = bank
        m[address] = value
    def call(name, *, wram=1, a=0, hl=0, de=0xBEEF):
        bank, target = symbols[name]
        bank = bank or 1
        m[0x2000] = bank
        m[addr('hROMBank')] = bank
        m[0xFF70] = wram
        m[0xC100:0xC106] = [0xF3, 0xCD, target & 255, target >> 8, 0x18, 0xFE]
        r.A, r.HL, r.D, r.E = a, hl, de >> 8, de & 255
        r.SP, r.PC = 0xC0FF, 0xC100
        p.tick(1, False, False)
        assert r.PC == 0xC104, (name, hex(r.PC))
        assert r.SP == 0xC0FF
        assert m[addr('hROMBank')] == bank
        assert m[0xFF70] & 7 == wram
    def entry(slot):
        m[0xFF70] = 2
        address = addr('wPokemonIndexTableEntries') + 2 * (slot - 1)
        return int.from_bytes(m[address:address + 2], 'little')
    def reset(marker, full):
        # Clear all roots including overlapping scratch workspaces.
        for bank in (1, 2):
            m[0xFF70] = bank
            m[0xD000:0xE000] = [0] * 0x1000
        for name in ('wTempMonSpecies', 'wBattleMonSpecies', 'wEnemyMonSpecies', 'wOddEggSpecies', 'wCurSpecies'):
            write(name, 0)
        write('wPokemonDataFormat', marker & 255)
        m[addr('wPokemonDataFormat') + 1] = marker >> 8
        m[0xFF70] = 2
        if full:
            start = addr('wPokemonIndexTableEntries')
            for slot in range(1, 101):
                m[start + 2 * (slot - 1):start + 2 * slot] = list((0x400 + slot).to_bytes(2, 'little'))
            write('wPokemonIndexTableUsedSlots', 100)
        write('wPokemonIndexTableLockedEntries', 16 if full else 0)
        write('wPokemonIndexTableLastAllocated', 17 if full else 0)
    try:
        m[0xFF50] = 1
        m[0xFFFF] = m[0xFF0F] = m[0xFF40] = 0
        markers = (0, 0x16BC, 0x00BC, 0x1600)
        gc_cases = 0
        for marker in markers:
            for allocation in (False, True):
                reset(marker, True)
                for slot in range(6):
                    write(f'wPartyMon{slot + 1}Species', slot + 1)
                write('wPartyCount', 1)  # Contest-hidden slots must survive.
                write('wBreedMon1Species', 7)
                write('wBreedMon2Species', 8)
                for slot in range(3):
                    write(f'wRoamMon{slot + 1}Species', 9 + slot)
                for slot, label in enumerate(('FirstPlace', 'SecondPlace', 'ThirdPlace', 'Temp')):
                    write(f'wBugContest{label}Mon', 12 + slot)
                legacy = ('wOTPartyMon1Species', 'wTempMonSpecies', 'wContestMonSpecies',
                          'wBattleMonSpecies', 'wEnemyMonSpecies', 'wOddEggSpecies', 'wCurSpecies')
                for slot, label in enumerate(legacy, 18):
                    write(label, slot)
                if allocation:
                    call('GetPokemonIDFromIndex', hl=25)
                    allocated = r.A
                    assert entry(allocated) == 25
                else:
                    call('PokemonTableGarbageCollection', wram=2)
                    assert (r.D, r.E) == (0xBE, 0xEF)
                    allocated = None
                retained = set(range(9, 18))
                if marker == 0x16BC:
                    retained.update(range(1, 9))
                for slot in range(1, 101):
                    expected = 0x400 + slot if slot in retained else 0
                    if slot == allocated:
                        expected = 25
                    assert entry(slot) == expected, (hex(marker), allocation, slot, entry(slot), expected)
                assert m[addr('wPokemonIndexTableUsedSlots')] == len(retained) + int(allocation)
                gc_cases += 1

        rom = args.rom.read_bytes()
        bank, address = symbols['NativeVariantIdentityTable']
        offset = bank * 0x4000 + address - 0x4000
        alolan = next(int.from_bytes(rom[pos:pos + 2], 'little')
                      for pos in range(offset, offset + 500, 5)
                      if int.from_bytes(rom[pos + 2:pos + 4], 'little') == 26 and rom[pos + 4] == 2)
        stride = addr('wPartyMon2Species') - addr('wPartyMon1Species')
        form_offset = addr('wPartyMon1Form') - addr('wPartyMon1Species')
        catch_cases = 0
        for marker in markers:
            for full in (False, True):
                for native, species, form in ((25, 25, 1), (257, 1, 0x21), (alolan, 26, 2)):
                    for slot in range(6):
                        for metadata in (0, 0x40, 0x80, 0xC0):
                            reset(marker, full)
                            write('wPartyCount', slot + 1)
                            m[0xFF70] = 1
                            source = addr('wOTPartyMon1Species')
                            original = [(i * 7 + 3) & 255 for i in range(stride)]
                            original[0], original[form_offset] = species, form | metadata
                            m[source:source + stride] = original
                            dest = addr('wPartyMon1Species') + stride * slot
                            call('CopyCaughtPokemonToParty', a=slot)
                            copied = m[dest:dest + stride]
                            assert copied[1:] == original[1:]
                            assert m[source:source + stride] == original
                            assert m[addr('wPartyCount')] == slot + 1
                            if marker == 0x16BC:
                                assert entry(copied[0]) == native, (native, copied[0], entry(copied[0]))
                            else:
                                assert copied == original
                            if full:
                                assert entry(16) == 0x410 and entry(17) == 0x411
                            catch_cases += 1
        print(f'PASS: {gc_cases} collection/allocation cases and {catch_cases} caught-record copies, including full-table collection, hidden party slots, locks, recent IDs, marker variants, forms and metadata')
    finally:
        p.stop(save=False)


if __name__ == '__main__':
    main()
