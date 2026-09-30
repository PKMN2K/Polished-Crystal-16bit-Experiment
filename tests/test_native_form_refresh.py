"""Intentional party form edits update native IDs without restoring the old form."""
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
        transitions = [(base, native, base, form) for native, base, form in variants]
        transitions += [(native, base, base, 1) for native, base, form in variants]
        transitions += [(129, 129, 129, 20), (257, 257, 257, 1)]
        stride = addr('wPartyMon2Species') - addr('wPartyMon1Species')
        for old, new, base, edited in transitions:
            for marker in (0, 0x16BC, 0x00BC, 0x1600):
                for slot in range(6):
                    for metadata in (0, 0x40, 0x80, 0xC0):
                        context = (old, new, marker, slot, metadata)
                        mem[0xFF70] = 2
                        mem[0xD000:0xE000] = [0] * 4096
                        mem[0xFF70] = 1
                        seed(old)
                        word = marker.to_bytes(2, 'little')
                        at = addr('wPokemonDataFormat')
                        mem[at:at+2] = list(word)
                        put('wCurPartyMon', slot)
                        put('wPartyCount', 6)
                        start = addr('wPartyMon1Species')
                        mem[start:start+6*stride] = [0] * (6*stride)
                        record = start + slot*stride
                        mem[record:record+stride] = [0xA5] * stride
                        mem[record] = 7 if marker == 0x16BC else base & 255
                        form_at = record + addr('wPartyMon1Form') - start
                        mem[form_at] = edited | ((base >> 8) << 5) | metadata
                        before = bytes(mem[start:start+6*stride])
                        invoke()
                        assert (regs.B, regs.C, regs.D, regs.E, regs.HL) == (0x12, 0x34, 0x56, 0x78, 0xC280), context
                        after = bytes(mem[start:start+6*stride])
                        assert after[:record-start] == before[:record-start]
                        assert after[record-start+1:] == before[record-start+1:], context
                        if marker == 0x16BC:
                            transient = mem[record]
                            assert transient, context
                            mem[0xFF70] = 2
                            entry = addr('wPokemonIndexTableEntries') + 2*(transient-1)
                            actual = int.from_bytes(mem[entry:entry+2], 'little')
                            mem[0xFF70] = 1
                            assert actual == new, (context, actual)
                        else:
                            assert after == before, context
                        assert bytes(mem[at:at+2]) == word, context
                        count += 1
        armored = next(native for native, base, form in variants if base == 150 and form == 2)
        for marker in (0, 0x16BC):
            for old_armored in (False, True):
                for want_armored in (False, True):
                    for slot in range(6):
                        for metadata in (0, 0x40, 0x80, 0xC0):
                            context = ('live armor', marker, old_armored, want_armored, slot, metadata)
                            mem[0xFF70] = 2
                            mem[0xD000:0xE000] = [0] * 4096
                            mem[0xFF70] = 1
                            seed(armored if old_armored else 150)
                            at = addr('wPokemonDataFormat')
                            mem[at:at+2] = list(marker.to_bytes(2, 'little'))
                            put('wCurPartyMon', slot)
                            put('wPartyCount', 6)
                            start = addr('wPartyMon1Species')
                            mem[start:start+6*stride] = [0] * (6*stride)
                            record = start + slot*stride
                            mem[record:record+stride] = [0xA5] * stride
                            mem[record] = 7 if marker else 150
                            form_at = record + addr('wPartyMon1Form') - start
                            item_at = record + addr('wPartyMon1Item') - start
                            mem[form_at] = (2 if old_armored else 1) | metadata
                            mem[item_at] = 0xBE if want_armored else 0
                            before = bytes(mem[start:start+6*stride])
                            invoke('UpdateMewtwoForm', item_at)
                            assert mem[form_at] == (2 if want_armored else 1) | metadata, context
                            after = bytes(mem[start:start+6*stride])
                            for i, (was, got) in enumerate(zip(before, after)):
                                if start+i not in (record, form_at):
                                    assert was == got, (context, i)
                            if marker:
                                transient = mem[record]
                                mem[0xFF70] = 2
                                entry = addr('wPokemonIndexTableEntries') + 2*(transient-1)
                                actual = int.from_bytes(mem[entry:entry+2], 'little')
                                mem[0xFF70] = 1
                                assert actual == (armored if want_armored else 150), (context, actual)
                            else:
                                assert mem[record] == 150, context
                            count += 1
        print(f'PASS: {count} intentional native party-form refresh cases; every mechanical variant enters/exits correctly, six slots, four format markers, cosmetic forms, live Mewtwo armor updates, metadata/nonidentity bytes and helper registers preserved')
    finally:
        p.stop(save=False)


if __name__ == '__main__':
    main()
