"""Scripted encounters retain native identities, forms and allocator roots.

The real script command reads synthetic four-byte parameters from WRAM. No ROM
code is patched. A gameplay fixture separately exercises the compiled macro and
complete battle through joypad input.
"""
import argparse
from pathlib import Path
from pyboy import PyBoy


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    rom = parser.parse_args().rom
    symbols = {}
    for line in rom.with_suffix('.sym').read_text().splitlines():
        fields = line.split()
        if len(fields) == 2 and ':' in fields[0]:
            symbols[fields[1]] = tuple(int(x, 16) for x in fields[0].split(':'))
    data = rom.read_bytes()
    def addr(name): return symbols[name][1]
    def rom_bytes(name, size):
        bank, at = symbols[name]
        start = bank * 0x4000 + at % 0x4000
        return data[start:start + size]
    wide = (int.from_bytes(rom_bytes('NativeWideTestIdentity', 2), 'little')
            if 'NativeWideTestIdentity' in symbols else None)
    variants = rom_bytes('NativeVariantIdentityTable', 46 * 5)
    first_variant = int.from_bytes(variants[:2], 'little')
    cases = [(wide, 1)] if wide else []
    cases += [(native, 1) for native in range(1, first_variant)
              if native not in (0xff, 0x100)]
    cases += [(int.from_bytes(variants[n:n+2], 'little'), variants[n+4] | 0x80)
              for n in range(0, len(variants), 5)]
    cases += [(25, 3), (201, 26)]
    p = PyBoy(str(rom), window='null', sound_emulated=False, cgb=True, log_level='ERROR')
    p.set_emulation_speed(0)
    m, r = p.memory, p.register_file
    def write(name, values): m[addr(name):addr(name)+len(values)] = list(values)
    def call(name, a=0, hl=0xc280, de=0xc380):
        bank, target = symbols[name]
        bank = bank or 1
        m[0x2000] = bank
        m[addr('hROMBank')] = bank
        m[0xc100:0xc106] = [0xf3, 0xcd, target & 255, target >> 8, 0x18, 0xfe]
        r.A, r.HL, r.D, r.E = a, hl, de >> 8, de & 255
        r.SP, r.PC = 0xc0ff, 0xc100
        for _ in range(40):
            p.tick(1, False, False)
            if (r.PC, r.SP) == (0xc104, 0xc0ff): break
        assert (r.PC, r.SP) == (0xc104, 0xc0ff), (name, hex(r.PC), hex(r.SP))
        assert m[addr('hROMBank')] == bank and m[0xff70] & 7 == 1, name
    def decoded():
        call('GetNativeSpeciesIDFromLegacyPokemonDataStruct',
             hl=addr('wTempWildMonSpecies'),
             de=addr('wWildMonForm')-addr('wTempWildMonSpecies'))
        return r.B * 256 + r.C
    try:
        m[0xff50] = 1
        m[0xffff] = m[0xff0f] = m[0xff40] = 0
        m[0xc000:0xd000] = [0] * 0x1000
        for bank in (1, 2):
            m[0xff70] = bank
            m[0xd000:0xe000] = [0] * 0x1000
        m[0xff70] = 1
        for native, form in cases:
            write('hScriptPos', bytes((0x00, 0xc3)))
            write('hScriptBank', bytes((1,)))
            m[0xc300:0xc304] = [native & 255, native >> 8, form, 19]
            call('Script_loadwildmon')
            assert decoded() == native, ('scripted encounter identity', hex(native), decoded())
            assert m[addr('wWildMonForm')] & ~0x20 == form
            assert m[addr('wCurPartyLevel')] == 19
            assert bytes(m[addr('hScriptPos'):addr('hScriptPos')+2]) == b'\x04\xc3'
            assert m[addr('wBattleScriptFlags')] == 0x80
        if wide:
            write('hScriptPos', b'\x00\xc3')
            m[0xc300:0xc304] = [wide & 255, wide >> 8, 1, 19]
            call('Script_loadwildmon')
            for native in range(1, 255): call('GetPokemonIDFromIndex', hl=native)
            call('PokemonTableGarbageCollection')
            assert decoded() == wide, 'pending scripted encounter lost during GC'
        print(f'PASS {len(cases)} scripted native encounters, forms, stream advancement'
              f' and wide pending-encounter GC={bool(wide)}; no ROM stubs')
    finally:
        p.stop(save=False)


if __name__ == '__main__': main()
