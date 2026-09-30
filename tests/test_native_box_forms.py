"""PC box identity decoding uses native mechanical forms after checksum validation."""
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
    root = Path(__file__).resolve().parents[1]
    def addr(s): return syms[s][1]
    data = rom.read_bytes()
    bank, at = syms['NativeVariantIdentityTable']
    pos = bank * 0x4000 + at - 0x4000
    n = sum(l.strip().startswith('native_variant_identity ') for l in (root / 'data/pokemon/native_variant_name_roots.asm').read_text().splitlines())
    variants = [(int.from_bytes(data[p:p+2], 'little'), int.from_bytes(data[p+2:p+4], 'little'), data[p+4]) for p in range(pos, pos+5*n, 5)]
    p = PyBoy(str(rom), window='null', sound_emulated=False, cgb=True, log_level='ERROR')
    mem, regs = p.memory, p.register_file
    def put(s, value): mem[addr(s)] = value
    def word(s, value): mem[addr(s):addr(s)+2] = list(value.to_bytes(2, 'little'))
    def seed(value):
        mem[0xFF70] = 2
        at = addr('wPokemonIndexTableEntries') + 12
        mem[at:at+2] = list(value.to_bytes(2, 'little'))
        mem[0xFF70] = 1
    def invoke(label):
        b, a = syms[label]
        mem[0x2000] = b
        put('hROMBank', b)
        mem[0xC100:0xC106] = [0xF3, 0xCD, a & 255, a >> 8, 0x18, 0xFE]
        regs.B, regs.C, regs.D, regs.E, regs.HL = 0x12, 0x34, 0x56, 0x78, 0xC280
        regs.SP, regs.PC = 0xC0FF, 0xC100
        p.tick(4, False, False)
        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF), (label, hex(regs.PC))
        assert mem[addr('hROMBank')] == b
        assert mem[0xFF70] & 7 == 1
        return bool(regs.F & 0x80), bool(regs.F & 0x10)
    count = 0
    try:
        mem[0xFF50] = 1
        mem[0xFFFF] = mem[0xFF0F] = mem[0xFF40] = 0
        mem[0xFF70] = 1
        # DecodeTempMon's downstream stat rebuild is outside this identity /
        # checksum boundary; return there without changing the return flags.
        b, target = syms['SetTempPartyMonData']
        mem[b, target] = 0xC9
        start, end = addr('wEncodedTempMon'), addr('wEncodedTempMonEnd')
        form_addr = addr('wEncodedTempMonForm')
        extra = addr('wEncodedTempMonExtra')
        cases = [(native, base, canonical, raw)
                 for native, base, canonical in variants for raw in (0, 1, 0x21, 0x3F)]
        cases += [(129, 129, form, form) for form in range(1, 21)]
        cases += [(257, 257, 1, 1)]
        def setup(native, raw):
            mem[start:end] = [0] * (end-start)
            mem[extra+1:extra+3] = list(native.to_bytes(2, 'little'))
            put('wEncodedTempMonForm', raw)
            put('wEncodedTempMonLevel', 10)
        for native, base, canonical, raw in cases:
            for metadata in (0, 0x40, 0x80, 0xC0):
                expected = canonical | ((base >> 8) << 5) | metadata
                for live in (False, True):
                    setup(native, raw | metadata)
                    if live:
                        invoke('ChecksumTempMon')
                        assert invoke('ChecksumTempMon')[0]
                    label = 'DecodeTempMon' if live else 'DecodeNativeBoxIdentity'
                    assert not invoke(label)[1], (label, native, raw, metadata)
                    species = 'wTempMonSpecies' if live else 'wEncodedTempMonSpecies'
                    form = 'wTempMonForm' if live else 'wEncodedTempMonForm'
                    assert mem[addr(species)] == base & 255, (label, native)
                    assert mem[addr(form)] == expected, (label, native, raw, metadata, mem[addr(form)], expected)
                    if live:
                        at = addr('wTempMonExtra')
                        assert bytes(mem[at+1:at+3]) == native.to_bytes(2, 'little')
                    else:
                        assert bytes(mem[extra+1:extra+3]) == native.to_bytes(2, 'little')
                    count += 1
        for native in (0, 256, 0xFFFF):
            setup(native, 0x81)
            invoke('ChecksumTempMon')
            assert invoke('DecodeTempMon')[1], native
            count += 1
        for native, _, _ in variants:
            setup(native, 1)
            invoke('ChecksumTempMon')
            # Identity edits without a new checksum must take the bad-record
            # path before native form decoding can accept the identity.
            mem[extra+1] ^= 1
            assert invoke('DecodeTempMon')[1], native
            count += 1
        for species in (25, 129):
            setup(0xFFFF, 0x81)
            put('wEncodedTempMonSpecies', species)
            before = bytes(mem[start:end])
            assert not invoke('DecodeNativeBoxIdentity')[1]
            assert bytes(mem[start:end]) == before
            count += 1
        print(f'PASS: {count} native PC-box form/checksum cases; canonical regional forms, cosmetic forms, Egg/gender metadata, native word preservation, live DecodeTempMon identity boundary, invalid/corrupt rejection and legacy compatibility')
    finally:
        p.stop(save=False)


if __name__ == '__main__':
    main()
