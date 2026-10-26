"""Native identities determine mechanical forms at legacy runtime boundaries."""
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
    # The catalog-boundary checks below assume variants occupy consecutive
    # native IDs. Verify the actual ROM table rather than trusting its last
    # entry if a future catalog edit introduces a gap or duplicate.
    first_variant = variants[0][0]
    assert first_variant > 0x0100, first_variant  # native variants follow the root catalog
    assert all(native == first_variant + i for i, (native, _, _) in enumerate(variants)), (
        "native variant identity table contains a gap or duplicate"
    )
    p = PyBoy(str(rom), window='null', sound_emulated=False, cgb=True, log_level='ERROR')
    mem, regs = p.memory, p.register_file
    def put(s, value): mem[addr(s)] = value
    def word(s, value): mem[addr(s):addr(s)+2] = list(value.to_bytes(2, 'little'))
    def seed(value):
        mem[0xFF70] = 2
        at = addr('wPokemonIndexTableEntries') + 12
        mem[at:at+2] = list(value.to_bytes(2, 'little'))
        mem[0xFF70] = 1
    def invoke(label, native, raw):
        b, a = syms[label]
        mem[0x2000] = b
        put('hROMBank', b)
        mem[0xC100:0xC106] = [0xF3, 0xCD, a & 255, a >> 8, 0x18, 0xFE]
        regs.B, regs.C = native >> 8, native & 255
        regs.A = raw
        regs.D, regs.E, regs.HL = 0x56, 0x78, 0xC280
        if label == 'GetLegacySpeciesAndFormFromTransientID':
            regs.A, regs.B = 7, raw
        elif label == 'GetLegacySpeciesAndFormFromTransientStruct':
            regs.D, regs.E = 0, 1
            mem[0xC280:0xC282] = [7, raw]
        regs.SP, regs.PC = 0xC0FF, 0xC100
        p.tick(4, False, False)
        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF), (label, hex(regs.PC))
        assert mem[addr('hROMBank')] == b
        assert mem[0xFF70] & 7 == 1
        return regs.A, regs.B, regs.C
    count = 0
    try:
        mem[0xFF50] = 1
        mem[0xFFFF] = mem[0xFF0F] = mem[0xFF40] = 0
        mem[0xFF70] = 1
        cases = [(native, base, form, raw)
                 for native, base, form in variants for raw in (0, 1, 0x21, 0x3F)]
        cases += [(129, 129, form, form | extra)
                  for form in range(1, 21) for extra in (0, 0x20)]
        cases += [(257, 257, 1, raw) for raw in (1, 0x21)]
        # Zero, the reserved $0100 root, and out-of-catalog native IDs
        # must never alias a valid species or preserve stale metadata.
        # The final catalog entry is the last mechanical variant. Derive
        # the first invalid ID from the table rather than hardcoding $0152,
        # so newly added species do not break this safety regression.
        last_native = variants[-1][0]  # authoritative ID in the ROM table
        assert last_native < 0x01ff, "update boundary test for expanded catalog"
        # Probe across the entire unused tail of the nine-bit ID space,
        # not just its endpoints. A partial range check must not allow a
        # nonexistent variant to index past NativeVariantIdentityTable.
        unsupported_tail = range(last_native + 1, 0x0200)
        # Exercise high-byte rejection across the 16-bit space; checking
        # only $0200 and $FFFF would miss a guard that accepts middle banks.
        invalid_high_words = (
            (hi << 8) | lo
            for hi in (0x02, 0x03, 0x7f, 0x80, 0xfe, 0xff)
            for lo in (0x00, 0x01, 0x7f, 0xff)
        )
        invalid_ids = (0x0000, 0x0100, *unsupported_tail,
                       *invalid_high_words)
        for native in invalid_ids:
            for raw in (0x00, 0x21, 0xc0, 0xff):
                result = invoke('GetLegacySpeciesAndFormFromNativeIDBC', native, raw)
                assert result == (0, 0, 0), (native, raw, result)
                assert (regs.D, regs.E, regs.HL) == (0x56, 0x78, 0xC280)
                count += 1

        labels = ('GetLegacySpeciesAndFormFromNativeIDBC',
                  'GetLegacySpeciesAndFormFromTransientID',
                  'GetLegacySpeciesAndFormFromTransientStruct')
        for native, base, canonical, raw in cases:
            for metadata in (0, 0x40, 0x80, 0xC0):
                seed(native)
                for label in labels:
                    input_form = raw | metadata
                    # Structure decoder intentionally returns species/form bits
                    # only; callers merge Egg/gender from the unchanged record.
                    expected_meta = 0 if label.endswith('Struct') else metadata
                    expected_form = canonical | ((base >> 8) << 5) | expected_meta
                    before_table = None
                    mem[0xFF70] = 2
                    at = addr('wPokemonIndexTableEntries') + 12
                    before_table = bytes(mem[at:at+2])
                    mem[0xFF70] = 1
                    result = invoke(label, native, input_form)
                    assert result == (base & 255, expected_form, base & 255), (label, native, input_form, result, expected_form)
                    if label != 'GetLegacySpeciesAndFormFromTransientID':
                        assert regs.HL == 0xC280, (label, regs.HL)
                    if label == 'GetLegacySpeciesAndFormFromNativeIDBC':
                        assert (regs.D, regs.E) == (0x56, 0x78)
                    if label.endswith('Struct'):
                        assert bytes(mem[0xC280:0xC282]) == bytes([7, input_form])
                    mem[0xFF70] = 2
                    assert bytes(mem[at:at+2]) == before_table
                    mem[0xFF70] = 1
                    # Re-encoding the returned legacy pair must recover the
                    # authoritative ID, including every mechanical variant.
                    b, target = syms['GetSpeciesAndFormIndex']
                    mem[0xC100:0xC106] = [0xF3, 0xCD, target & 255, target >> 8, 0x18, 0xFE]
                    regs.SP, regs.PC = 0xC0FF, 0xC100
                    p.tick(4, False, False)
                    assert (regs.PC, regs.SP) == (0xC104, 0xC0FF)
                    assert (regs.B << 8 | regs.C) + 1 == native, (label, native, raw, metadata)
                    count += 1
        print(f'PASS: {count} native form-boundary cases; every mechanical variant ignores stale form bits, cosmetic Magikarp forms survive, native root controls EXTSPECIES, metadata/records/tables preserved and IDs round-trip')
    finally:
        p.stop(save=False)


if __name__ == '__main__':
    main()
