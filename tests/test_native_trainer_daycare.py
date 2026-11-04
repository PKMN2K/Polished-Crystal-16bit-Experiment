"""Trainer streams, phone names and daycare growth on real compiled CPU code.

Synthetic input records are placed in WRAM; no ROM routines are stubbed.
The gameplay fixture separately covers compiled trainer data and daycare menus.
"""
import argparse
from pathlib import Path
from pyboy import PyBoy


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    rom = parser.parse_args().rom
    syms = {}
    for line in rom.with_suffix('.sym').read_text().splitlines():
        fields = line.split()
        if len(fields) == 2 and ':' in fields[0]:
            syms[fields[1]] = tuple(int(x, 16) for x in fields[0].split(':'))
    data = rom.read_bytes()
    def addr(label): return syms[label][1]
    def rb(label, size):
        bank, at = syms[label]
        start = bank * 0x4000 + at % 0x4000
        return data[start:start + size]
    variants = rb('NativeVariantIdentityTable', 46 * 5)
    first_variant = int.from_bytes(variants[:2], 'little')
    identities = [(n, 1) for n in range(1, first_variant) if n not in (255, 256)]
    identities += [(int.from_bytes(variants[i:i+2], 'little'), variants[i+4])
                   for i in range(0, len(variants), 5)]
    wide = int.from_bytes(rb('NativeWideTestIdentity', 2), 'little') if 'NativeWideTestIdentity' in syms else None
    if wide: identities.insert(0, (wide, 1))
    p = PyBoy(str(rom), window='null', sound_emulated=False, cgb=True, log_level='ERROR')
    p.set_emulation_speed(0)
    m, r = p.memory, p.register_file
    def write(label, values):
        if isinstance(values, int): m[addr(label)] = values
        else: m[addr(label):addr(label)+len(values)] = list(values)
    def read(label, size=1): return bytes(m[addr(label):addr(label)+size])
    def call(label, a=0, bc=0, de=0xc380, hl=0xc300):
        bank, target = syms[label]
        bank = bank or 1
        m[0x2000] = bank; write('hROMBank', bank)
        m[0xc100:0xc106] = [0xf3, 0xcd, target & 255, target >> 8, 0x18, 0xfe]
        r.A, r.B, r.C, r.D, r.E, r.HL = a, bc >> 8, bc & 255, de >> 8, de & 255, hl
        r.SP, r.PC = 0xc0ff, 0xc100
        for _ in range(80):
            p.tick(1, False, False)
            if (r.PC, r.SP) == (0xc104, 0xc0ff): break
        assert (r.PC, r.SP) == (0xc104, 0xc0ff), (label, hex(r.PC), hex(r.SP))
        assert m[addr('hROMBank')] == bank and m[0xff70] & 7 == 1, label
    def native_struct(prefix, legacy=False):
        call('GetNativeSpeciesIDFromLegacyPokemonDataStruct' if legacy else
             'GetNativeSpeciesIDFromPokemonDataStruct', hl=addr(prefix+'Species'),
             de=addr(prefix+'Form')-addr(prefix+'Species'))
        return r.B * 256 + r.C
    try:
        m[0xff50] = 1
        m[0xffff] = m[0xff0f] = m[0xff40] = 0
        m[0xc000:0xd000] = [0] * 0x1000
        for bank in (1, 2):
            m[0xff70] = bank; m[0xd000:0xe000] = [0] * 0x1000
        m[0xff70] = 1
        write('wTrainerGroupBank', 1)
        for native, form in identities:
            m[0xc300:0xc303] = [native & 255, native >> 8, form | 0x80]
            call('ReadTrainerPartySpecies')
            assert r.HL == 0xc303, 'trainer record advancement'
            call('GetSpeciesAndFormIndex', bc=read('wCurForm')[0] * 256 + read('wCurPartySpecies')[0])
            assert r.B * 256 + r.C + 1 == native, ('trainer identity', hex(native))
            assert read('wCurForm')[0] & 0xdf == form | 0x80
        # A zero form must still select a valid plain/dynamic presentation.
        for native in (25, 24, wide or 0x123):
            m[0xc300:0xc303] = [native & 255, native >> 8, 0]
            call('ReadTrainerPartySpecies')
            assert read('wCurForm')[0] & 31
        print(f'PASS {len(identities)} trainer identities plus dynamic-form defaults', flush=True)

        # Every optional field combination, variable nickname lengths and
        # escaped move bytes, including a zero low byte and serial sentinel bytes.
        phone_cases = 0
        for flags in range(64):
            records, expected_names = [], set()
            for slot, (native, form) in enumerate([(wide or 0x123, 1), (25, 1), (19, 1)]):
                record = bytearray([20, native & 255, native >> 8, form])
                if flags & 1: record.append(0)  # held item
                if flags & 4: record.append(0)  # DV spread
                if flags & 8: record.append(0)  # personality
                if flags & 16: record.extend([0x80] * (slot * 3) + [0x53])
                if flags & 2: record.append(0)  # EV spread
                if flags & 32: record.extend([33, 0xff, 0, 1, 0xff, 0xfe, 0xff, 0])
                records.append(record)
                call('GetPokemonNameFromNativeIDBC', bc=native)
                expected_names.add(read('wStringBuffer1', 11).split(b'\x53')[0])
                m[0xc300:0xc300+len(record)] = list(record)
                call('SkipTrainerPartyMon', a=flags, bc=0x1234, de=0x5678)
                assert r.HL == 0xc300 + len(record) and (r.B, r.C, r.D, r.E) == (0x12, 0x34, 0x56, 0x78)
            payload = bytes([flags]) + b''.join(records)
            # Deliberately cross a 256-byte address boundary.
            at = 0xc3f0
            m[at:at+len(payload)] = list(payload)
            seen = set()
            for _ in range(64):
                call('RandomPhoneMonFromTrainer', bc=len(payload) << 8, hl=at)
                name = read('wStringBuffer4', 11).split(b'\x53')[0]
                assert name in expected_names, ('phone record', flags, name, expected_names)
                seen.add(name)
                if seen == expected_names: break
            assert seen == expected_names, ('phone sampling', flags, seen, expected_names)
            phone_cases += 1
        print(f'PASS {phone_cases} phone record layouts, all three party members and native names', flush=True)

        # All supported growth groups/variants, both daycare records and both
        # persistent formats. EXP just below the next level must not round up.
        growth_cases = 0
        for native, form in identities:
            call('GetBaseDataFromNativeIDBC', bc=native)
            call('CalcExpAtLevel', de=21 << 8)
            exp = int.from_bytes(read('hProduct', 4), 'big') - 1
            for mode in (0, 0x16bc):
                write('wPokemonDataFormat', mode.to_bytes(2, 'little'))
                call('GetLegacySpeciesAndFormFromNativeIDBC', bc=native, a=form | 0x80)
                species_byte, runtime_form = r.C, r.B
                if mode:
                    call('GetPokemonIDFromIndex', hl=native)
                    species_byte = r.A
                for parent in (1, 2):
                    prefix = f'wBreedMon{parent}'
                    write(prefix+'Species', species_byte)
                    write(prefix+'Form', runtime_form)
                    write(prefix+'Level', 19)
                    write(prefix+'Exp', exp.to_bytes(3, 'big'))
                    before = read(prefix, addr(prefix+'Level')-addr(prefix)+1)
                    call(f'GetBreedMon{parent}LevelGrowth')
                    assert (r.B, r.D, r.E) == (19, 1, 20), ('daycare growth', hex(native), mode, parent, r.B, r.D, r.E)
                    assert read(prefix, len(before)) == before, 'growth query modified daycare'
                    assert native_struct('wTempMon', legacy=True) == native
                    assert read('wTempMonForm')[0] & 0x80, 'gender metadata lost'
                    growth_cases += 1
        print(f'PASS {growth_cases} daycare growth calculations and runtime temp identities; no ROM stubs')
    finally:
        p.stop(save=False)


if __name__ == '__main__': main()
