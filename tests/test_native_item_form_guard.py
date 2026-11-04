"""Mewtwo-only held-item form handling preserves unrelated native identities."""
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
    def invoke(label='RefreshPartyIdentityAfterFormChange', hl=0xC280):
        b, target = syms[label]
        mem[0x2000] = b
        put('hROMBank', b)
        mem[0xC100:0xC106] = [0xF3, 0xCD, target & 255, target >> 8, 0x18, 0xFE]
        regs.B, regs.C, regs.D, regs.E, regs.HL = 0x12, 0x34, 0x56, 0x78, hl
        regs.SP, regs.PC = 0xC0FF, 0xC100
        p.tick(4, False, False)
        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF), (hex(regs.PC), hex(regs.SP))
        assert mem[addr('hROMBank')] == b
        assert mem[0xFF70] & 7 == 1
    count = 0
    try:
        mem[0xFF50] = 1
        mem[0xFFFF] = mem[0xFF0F] = mem[0xFF40] = 0
        mem[0xFF70] = 1
        identities = [(native, base, form) for native, base, form in variants if base != 150]
        identities += [(25, 25, 1), (257, 257, 1), (129, 129, 20)]
        stride = addr('wPartyMon2Species') - addr('wPartyMon1Species')
        for native, base, canonical in identities:
            for slot in range(6):
                for raw in (1, canonical):
                    for metadata in (0, 0x40, 0x80, 0xC0):
                        for item in (0, 0x42, 0xBE):
                            context = (native, slot, raw, metadata, item)
                            mem[0xFF70] = 2
                            mem[0xD000:0xE000] = [0] * 4096
                            mem[0xFF70] = 1
                            seed(native)
                            at = addr('wPokemonDataFormat')
                            mem[at:at+2] = [0xBC, 0x16]
                            put('wCurPartyMon', slot)
                            put('wPartyCount', 6)
                            start = addr('wPartyMon1Species')
                            mem[start:start+6*stride] = [0] * (6*stride)
                            record = start + slot*stride
                            mem[record:record+stride] = [0xA5] * stride
                            mem[record] = 7
                            form_at = record + addr('wPartyMon1Form') - start
                            item_at = record + addr('wPartyMon1Item') - start
                            mem[form_at] = raw | ((base >> 8) << 5) | metadata
                            mem[item_at] = item
                            before = bytes(mem[start:start+6*stride])
                            invoke('UpdateMewtwoForm', item_at)
                            assert bytes(mem[start:start+6*stride]) == before, context
                            mem[0xFF70] = 2
                            entry = addr('wPokemonIndexTableEntries') + 12
                            assert int.from_bytes(mem[entry:entry+2], 'little') == native, context
                            mem[0xFF70] = 1
                            count += 1
        print(f'PASS: {count} held-item native identity preservation cases; every non-Mewtwo mechanical variant, stale/canonical form bytes, all six slots, cosmetic forms, metadata and empty/ordinary/Armor Suit items')
    finally:
        p.stop(save=False)


if __name__ == '__main__':
    main()
