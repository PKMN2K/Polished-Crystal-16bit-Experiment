"""Full native PC serialization round trips include live stat/HP/PP reconstruction."""
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
        start = addr('wTempMonSpecies')
        extra = addr('wTempMonExtra')
        end = extra + 3
        encoded_extra = addr('wEncodedTempMonExtra')
        nickname_len = addr('wEncodedTempMonOT') - addr('wEncodedTempMonNickname')
        ot_len = addr('wEncodedTempMonEnd') - addr('wEncodedTempMonOT')
        identities = [(25, 25, 1), (257, 257, 1)] + variants
        identities += [(129, 129, form) for form in range(1, 21)]
        for native, base, canonical in identities:
            for metadata in (0, 0x40, 0x80, 0xC0):
                for stale in (False, True):
                    context = (native, canonical, metadata, stale)
                    mem[start:end] = [0] * (end-start)
                    put('wTempMonSpecies', base & 255)
                    put('wTempMonForm', canonical | ((base >> 8) << 5) | metadata)
                    put('wTempMonLevel', 25)
                    put('wTempMonItem', 0x42)
                    put('wTempMonHappiness', 100)
                    put('wTempMonPersonality', 0x21)
                    dv = addr('wTempMonDVs')
                    mem[dv:dv+3] = [0xAB, 0xCD, 0xEF]
                    moves, pp = addr('wTempMonMoves'), addr('wTempMonPP')
                    mem[moves:moves+4] = [33] * 4
                    mem[pp:pp+4] = [0, 0x40, 0x80, 0xC0]
                    nick, ot = addr('wTempMonNickname'), addr('wTempMonOT')
                    mem[nick:nick+nickname_len+1] = [0x80+i for i in range(nickname_len)] + [0x53]
                    mem[ot:ot+ot_len+1] = [0x8A+i for i in range(ot_len)] + [0x53]
                    assert not invoke('SetTempPartyMonData')[1], context
                    expected = bytes(mem[start:end])
                    stats = addr('wTempMonMaxHP')
                    assert all(int.from_bytes(mem[stats+i:stats+i+2], 'big') > 0 for i in range(0, 12, 2)), context
                    assert all(mem[pp+i] & 0x3F for i in range(4)), context
                    invoke('EncodeTempMon')
                    assert mem[addr('wEncodedTempMonSpecies')] == 0, context
                    assert bytes(mem[encoded_extra+1:encoded_extra+3]) == native.to_bytes(2, 'little'), context
                    if stale and native in {v[0] for v in variants}:
                        # Valid native ID with a stale normal presentation form.
                        put('wEncodedTempMonForm', metadata | 1)
                        invoke('ChecksumTempMon')
                    assert invoke('ChecksumTempMon')[0], context
                    assert not invoke('DecodeTempMon')[1], context
                    actual = bytes(mem[start:end])
                    for i, (want, got) in enumerate(zip(expected, actual)):
                        if start+i in (extra+1, extra+2, addr('wTempMonUnused')):
                            continue  # native word / unserialized scratch byte
                        assert got == want, (context, hex(start+i), want, got)
                    assert bytes(mem[extra+1:extra+3]) == native.to_bytes(2, 'little'), context
                    count += 1
        print(f'PASS: {count} complete native PC serialization round trips; live EncodeTempMon, checksum, DecodeTempMon, base data, stat/HP/PP rebuild, all mechanical variants, cosmetic forms, metadata, names/items/DVs and stale variant forms')
    finally:
        p.stop(save=False)


if __name__ == '__main__':
    main()
