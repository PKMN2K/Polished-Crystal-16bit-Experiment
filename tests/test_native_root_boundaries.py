"""Bank-safe native root resolution in battle comparisons and PC box decoding."""
import argparse
import re
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
    # A plain call/jump between local ROMX labels must stay in the same bank.
    # Check linked banks so moving either section cannot silently break it.
    source = (root / 'engine/16/native_species.asm').read_text().splitlines()
    labels = {m.group(1) for line in source if (m := re.match(r'^(\w+)::?', line))}
    caller = None
    audited = 0
    for line in source:
        if m := re.match(r'^(\w+)::?', line):
            caller = m.group(1)
        if m := re.match(r'\s+(?:call|jp|jr)\s+(?:[nzc]+, )?(\w+)\s*$', line):
            target = m.group(1)
            if target in labels and caller in syms:
                assert syms[target][0] == 0 or syms[caller][0] == syms[target][0], (caller, target, syms[caller], syms[target])
                audited += 1
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
        identities = [(25, 25, 1), (257, 257, 1)] + variants
        for native, base, form in identities:
            for marker in (0, 0x16BC):
                for side in (0, 1):
                    for match in (False, True):
                        word('wPokemonDataFormat', marker)
                        seed(native if side == 0 else (base if match else 129))
                        put('hBattleTurn', side)
                        put('wCurBattleMon', 0)
                        put('wCurOTMon', 0)
                        put('wPlayerFutureSightCount', 0)
                        put('wEnemyFutureSightCount', 0)
                        user = 'wOTPartyMon1' if side else 'wPartyMon1'
                        other = 'wPartyMon1' if side else 'wOTPartyMon1'
                        put(user+'Species', 7 if marker and side == 0 else base & 255)
                        put(user+'Form', form | ((base >> 8) << 5) | 0x80)
                        opposite = base if match else 129
                        put(other+'Species', 7 if marker and side else opposite & 255)
                        put(other+'Form', 1 | ((opposite >> 8) << 5))
                        before = [(s, mem[addr(s)]) for s in (user+'Species', user+'Form', other+'Species', other+'Form')]
                        assert invoke('BattlePartyRootsMatch')[0] == match, (native, marker, side, match)
                        assert (regs.B, regs.C, regs.D, regs.E, regs.HL) == (0x12, 0x34, 0x56, 0x78, 0xC280)
                        assert [(s, mem[addr(s)]) for s, _ in before] == before
                        count += 1
        for native, base, form in identities:
            for metadata in (0, 0x40, 0x80, 0xC0):
                put('wEncodedTempMonSpecies', 0)
                at = addr('wEncodedTempMonExtra')
                mem[at+1:at+3] = list(native.to_bytes(2, 'little'))
                encoded = form | ((base >> 8) << 5) | metadata
                put('wEncodedTempMonForm', encoded)
                assert not invoke('DecodeNativeBoxIdentity')[1], (native, encoded)
                assert mem[addr('wEncodedTempMonSpecies')] == base & 255
                assert mem[addr('wEncodedTempMonForm')] == encoded, (native, encoded, mem[addr('wEncodedTempMonForm')])
                assert bytes(mem[at+1:at+3]) == native.to_bytes(2, 'little')
                count += 1
        for native in (0, 256, 0xFFFF):
            put('wEncodedTempMonSpecies', 0)
            at = addr('wEncodedTempMonExtra')
            mem[at+1:at+3] = list(native.to_bytes(2, 'little'))
            put('wEncodedTempMonForm', 0x81)
            assert invoke('DecodeNativeBoxIdentity')[1], native
            assert mem[addr('wEncodedTempMonSpecies')] == 0
            assert mem[addr('wEncodedTempMonForm')] == 0x81
            count += 1
        print(f'PASS: {count} native battle-root/box cases and {audited} linked-bank call checks; variants, full-word roots, both battle sides, transient/legacy formats, metadata and invalid box identities')
    finally:
        p.stop(save=False)


if __name__ == '__main__':
    main()
