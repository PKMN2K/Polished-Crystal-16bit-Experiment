"""Hatchling frontpic preparation decodes the selected native party identity."""
import argparse
from pathlib import Path
from pyboy import PyBoy


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('rom', type=Path)
    rom = ap.parse_args().rom
    syms = {}
    for line in rom.with_suffix('.sym').read_text().splitlines():
        fields = line.split()
        if len(fields) == 2 and ':' in fields[0]:
            syms[fields[1]] = tuple(int(v, 16) for v in fields[0].split(':'))
    def addr(s): return syms[s][1]
    root = Path(__file__).resolve().parents[1]
    data = rom.read_bytes()
    bank, at = syms['NativeVariantIdentityTable']
    pos = bank * 0x4000 + at - 0x4000
    n = sum(line.strip().startswith('native_variant_identity ') for line in (root / 'data/pokemon/native_variant_name_roots.asm').read_text().splitlines())
    variants = [(int.from_bytes(data[p:p+2], 'little'), int.from_bytes(data[p+2:p+4], 'little'), data[p+4]) for p in range(pos, pos+5*n, 5)]
    bank, at = syms['BaseDataRecords']
    base_start = bank * 0x4000 + at - 0x4000
    size = addr('wCurBaseDataEnd') - addr('wCurBaseData')
    pyboy = PyBoy(str(rom), window='null', sound_emulated=False, cgb=True, log_level='ERROR')
    mem, regs = pyboy.memory, pyboy.register_file
    def put(s, value): mem[addr(s)] = value
    def word(s, value): mem[addr(s):addr(s)+2] = list(value.to_bytes(2, 'little'))
    def invoke():
        bank, target = syms['GetHatchlingFrontpic']
        mem[0x2000] = bank
        put('hROMBank', bank)
        mem[0xC100:0xC106] = [0xF3, 0xCD, target & 255, target >> 8, 0x18, 0xFE]
        regs.B, regs.C, regs.D, regs.E, regs.HL = 0x12, 0x34, 0x80, 0x00, 0xC280
        regs.SP, regs.PC = 0xC0FF, 0xC100
        pyboy.tick(4, False, False)
        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF), (hex(regs.PC), hex(regs.SP))
        assert mem[addr('hROMBank')] == bank
        assert mem[0xFF70] & 7 == 1
    count = 0
    graphics = []
    try:
        mem[0xFF50] = 1
        mem[0xFFFF] = mem[0xFF0F] = mem[0xFF40] = 0
        mem[0xFF70] = 1
        # Stop only the VRAM/animation work. The actual party loader, native
        # decoder, bank transitions and base-data lookup run without stubs.
        bank, at = syms['PrepareAnimatedFrontpic']
        mem[bank, at] = 0xC9
        def capture(_):
            graphics.append((mem[addr('wCurSpecies')], mem[addr('wCurPartySpecies')], mem[addr('wCurForm')], regs.D << 8 | regs.E))
        pyboy.hook_register(bank, at, capture, None)
        start = addr('wPartyMon1Species')
        stride = addr('wPartyMon2Species') - start
        form_offset = addr('wPartyMon1Form') - start
        for native, base, form in [(25, 25, 1), (257, 257, 1)] + variants:
            for marker in (0, 0x16BC, 0x00BC, 0x1600):
                for raw in (form, 1, 0x21):
                    # Legacy storage owns its form bits; native storage owns
                    # mechanical form and root-extension bits in the full ID.
                    if marker != 0x16BC and raw != form:
                        continue
                    for metadata in (0, 0x40, 0x80, 0xC0):
                        for slot in range(6):
                            context = (native, marker, raw, metadata, slot)
                            word('wPokemonDataFormat', marker)
                            mem[0xFF70] = 2
                            entry = addr('wPokemonIndexTableEntries') + 12
                            mem[entry:entry+2] = list(native.to_bytes(2, 'little'))
                            mem[0xFF70] = 1
                            mem[start:start+6*stride] = [0xA5] * (6*stride)
                            record = start + slot*stride
                            mem[record] = 7 if marker == 0x16BC else base & 255
                            encoded = raw | metadata
                            if marker != 0x16BC:
                                encoded |= (base >> 8) << 5
                            mem[record+form_offset] = encoded
                            put('wCurPartyMon', slot)
                            put('wPartyCount', 6)
                            put('wCurSpecies', 91)
                            put('wCurPartySpecies', 92)
                            put('wCurForm', 3)
                            before = bytes(mem[start:start+6*stride])
                            previous = len(graphics)
                            invoke()
                            expected_form = (form if native != base else raw & 0x1F) | ((base >> 8) << 5)
                            assert len(graphics) == previous+1, context
                            assert graphics[-1] == (base & 255, base & 255, expected_form, 0x8000), (context, graphics[-1])
                            expected = data[base_start+(native-1)*size:base_start+native*size]
                            assert bytes(mem[addr('wCurBaseData'):addr('wCurBaseDataEnd')]) == expected, context
                            assert bytes(mem[start:start+6*stride]) == before, context
                            count += 1
        print(f'PASS: {count} native hatchling frontpic cases; all mechanical variants, full-word roots, six party slots, legacy/native/partial markers, stale globals/form bits, real base-data lookup, graphics identity/destination and unchanged party records')
    finally:
        pyboy.stop(save=False)


if __name__ == '__main__':
    main()
