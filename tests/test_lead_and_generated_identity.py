"""CPU tests for lead abilities and complete generated-party insertion.

Usage: python tests/test_lead_and_generated_identity.py ROM.gbc
Requires PyBoy 2.7.0 and matching RGBDS symbols; no game saves are used.
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
    rom = args.rom.read_bytes()
    bank, address = symbols['NativeVariantIdentityTable']
    offset = bank * 0x4000 + address - 0x4000
    alolan = next(int.from_bytes(rom[pos:pos + 2], 'little') for pos in range(offset, offset + 500, 5)
                  if int.from_bytes(rom[pos + 2:pos + 4], 'little') == 26 and rom[pos + 4] == 2)
    cases = ((63, 63, 1), (257, 1, 0x21), (alolan, 26, 2))
    p = PyBoy(str(args.rom), window='null', sound_emulated=False, cgb=True, log_level='ERROR')
    m, r = p.memory, p.register_file
    def write(name, value):
        m[addr(name)] = value
    def reset(marker):
        for bank in (1, 2):
            m[0xFF70] = bank
            m[0xD000:0xE000] = [0] * 4096
        m[0xFF70] = 1
        write('wPokemonDataFormat', marker & 255)
        m[addr('wPokemonDataFormat') + 1] = marker >> 8
    def seed(native):
        m[0xFF70] = 2
        at = addr('wPokemonIndexTableEntries') + 12  # transient ID 7
        m[at:at + 2] = list(native.to_bytes(2, 'little'))
        write('wPokemonIndexTableUsedSlots', 1)
        m[0xFF70] = 1
    def call(name, *, c=0x34, hl=0xC222):
        bank, target = symbols[name]
        bank = bank or 1
        m[0x2000] = bank
        write('hROMBank', bank)
        m[0xFF70] = 1
        m[0xC100:0xC106] = [0xF3, 0xCD, target & 255, target >> 8, 0x18, 0xFE]
        r.B, r.C, r.D, r.E, r.HL = 0x12, c, 0x56, 0x78, hl
        r.SP, r.PC = 0xC0FF, 0xC100
        p.tick(20 if name == 'TryAddMonToParty' else 2, False, False)
        assert r.PC == 0xC104, (name, hex(r.PC), m[addr('hROMBank')], m[addr('wMonType')], m[addr('wCurPartySpecies')])
        assert r.SP == 0xC0FF
        assert m[addr('hROMBank')] == bank
        assert m[0xFF70] & 7 == 1
    try:
        m[0xFF50] = 1
        m[0xFFFF] = m[0xFF0F] = m[0xFF40] = 0
        ability_cases = 0
        for marker in (0, 0x16BC, 0x00BC, 0x1600):
            for native, species, form in cases:
                for ability in (0x20, 0x40, 0x60):
                    for enabled in (False, True):
                        for metadata in (0, 0x40, 0x80, 0xC0):
                            reset(marker)
                            seed(native)
                            write('wInitialOptions', 255 if enabled else 0)
                            # Independent legacy oracle through the established
                            # ability lookup; never use a transient species here.
                            m[0xC200:0xC202] = [ability, form | metadata]
                            call('GetAbility', c=species, hl=0xC200)
                            expected = 0 if metadata & 0x40 else r.A
                            write('wPartyMon1Species', 7 if marker == 0x16BC else species)
                            write('wPartyMon1Personality', ability)
                            write('wPartyMon1Form', form | metadata)
                            globals_ = ('wCurSpecies', 'wCurPartySpecies', 'wCurForm')
                            for name, value in zip(globals_, (91, 92, 3)):
                                write(name, value)
                            call('GetLeadAbility')
                            assert r.A == expected, (hex(marker), native, ability, metadata, r.A, expected)
                            assert (r.B, r.C, r.D, r.E, r.HL) == (0x12, 0x34, 0x56, 0x78, 0xC222)
                            assert [m[addr(name)] for name in globals_] == [91, 92, 3]
                            ability_cases += 1
        generated_cases = 0
        stride = addr('wPartyMon2Species') - addr('wPartyMon1Species')
        for marker in (0, 0x16BC, 0x00BC, 0x1600):
            for enemy in (False, True):
                for native, species, form in cases:
                    for slot in range(6):
                        reset(marker)
                        seed(25)
                        write('wInitialOptions', 0)
                        write('wPartyCount', slot)
                        write('wOTPartyCount', slot)
                        if slot:
                            write('wPartyMon1Species', 7 if marker == 0x16BC else 25)
                            write('wPartyMon1Form', 1)
                        write('wMonType', int(enemy))
                        write('wBattleMode', 1)  # Wild-generation path for either destination.
                        write('wBattleType', 0)
                        write('wCurPartySpecies', species)
                        write('wCurForm', form)
                        write('wCurPartyLevel', 20)
                        call('TryAddMonToParty')
                        assert r.F & 0x10, (marker, enemy, native, slot)
                        prefix = 'wOTPartyMon1' if enemy else 'wPartyMon1'
                        dest = addr(prefix + 'Species') + slot * stride
                        result = m[dest]
                        assert m[addr('wOTPartyCount' if enemy else 'wPartyCount')] == slot + 1
                        assert m[addr(prefix + 'Level') + slot * stride] == 20
                        assert m[addr(prefix + 'Form') + slot * stride] & 0x3F == form
                        hp = addr(prefix + 'MaxHP') + slot * stride
                        assert int.from_bytes(m[hp:hp + 2], 'big') > 0
                        if marker == 0x16BC and not enemy:
                            m[0xFF70] = 2
                            at = addr('wPokemonIndexTableEntries') + 2 * (result - 1)
                            assert int.from_bytes(m[at:at + 2], 'little') == native, (marker, enemy, native, slot, result)
                            m[0xFF70] = 1
                        else:
                            assert result == species, (marker, enemy, native, slot, result)
                        generated_cases += 1
        print(f'PASS: {ability_cases} lead-ability cases and {generated_cases} full generated-party insertions; marker variants, forms, ability slots/options, Egg/gender flags, all party slots and both destinations')
    finally:
        p.stop(save=False)


if __name__ == '__main__':
    main()
