"""Daycare compatibility compares full native roots and recognizes real Ditto."""
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
    root = Path(__file__).resolve().parents[1]
    def addr(s): return syms[s][1]
    data = rom.read_bytes()
    bank, at = syms['NativeVariantIdentityTable']
    pos = bank * 0x4000 + at - 0x4000
    n = sum(line.strip().startswith('native_variant_identity ') for line in (root / 'data/pokemon/native_variant_name_roots.asm').read_text().splitlines())
    variants = [(int.from_bytes(data[p:p+2], 'little'), int.from_bytes(data[p+2:p+4], 'little'), data[p+4]) for p in range(pos, pos+5*n, 5)]
    pyboy = PyBoy(str(rom), window='null', sound_emulated=False, cgb=True, log_level='ERROR')
    mem, regs = pyboy.memory, pyboy.register_file
    def put(s, value): mem[addr(s)] = value
    def word(s, value): mem[addr(s):addr(s)+2] = list(value.to_bytes(2, 'little'))
    def invoke(label):
        bank, target = syms[label]
        mem[0x2000] = bank
        put('hROMBank', bank)
        mem[0xC100:0xC106] = [0xF3, 0xCD, target & 255, target >> 8, 0x18, 0xFE]
        regs.B, regs.C, regs.D, regs.E, regs.HL = 0x12, 0x34, 0x56, 0x78, 0xC280
        regs.SP, regs.PC = 0xC0FF, 0xC100
        pyboy.tick(4, False, False)
        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF), (label, hex(regs.PC), hex(regs.SP))
        assert mem[addr('hROMBank')] == bank
        assert mem[0xFF70] & 7 == 1
        return bool(regs.F & 0x80)
    def preserved():
        assert (regs.B, regs.C, regs.D, regs.E, regs.HL) == (0x12, 0x34, 0x56, 0x78, 0xC280)
    def seed(pair, marker, metadata):
        word('wPokemonDataFormat', marker)
        mem[0xFF70] = 2
        at = addr('wPokemonIndexTableEntries') + 12
        mem[at:at+4] = list(pair[0][0].to_bytes(2, 'little') + pair[1][0].to_bytes(2, 'little'))
        mem[0xFF70] = 1
        for i, (_, base, form) in enumerate(pair, 1):
            put(f'wBreedMon{i}Species', 6+i if marker == 0x16BC else base & 255)
            put(f'wBreedMon{i}Form', form | ((base >> 8) << 5) | metadata)
    def snapshot():
        return tuple(mem[addr(f'wBreedMon{i}{field}')] for i in (1, 2) for field in ('Species', 'Form'))
    count = 0
    try:
        mem[0xFF50] = 1
        mem[0xFFFF] = mem[0xFF0F] = mem[0xFF40] = 0
        mem[0xFF70] = 1
        low, high = (1, 1, 1), (257, 257, 1)
        pairs = [(low, low), (low, high), (high, low), (high, high)]
        for variant in variants:
            base = (variant[1], variant[1], 1)
            other = (25, 25, 1) if variant[1] != 25 else (1, 1, 1)
            pairs.extend(((variant, base), (base, variant), (variant, other), (other, variant)))
        for pair in pairs:
            same_root = pair[0][1] == pair[1][1]
            for marker in (0, 0x16BC, 0x00BC, 0x1600):
                for metadata in (0, 0x40, 0x80, 0xC0):
                    context = (pair, marker, metadata)
                    seed(pair, marker, metadata)
                    before = snapshot()
                    assert invoke('BreedmonRootsMatch') == same_root, context
                    preserved()
                    assert snapshot() == before, context
                    count += 1
                    # Execute the real compatibility-rating suffix, including
                    # both daycare loaders and the owner's two-byte ID check.
                    for owner2 in (0x1234, 0x1235, 0x1334):
                        word('wBreedMon1ID', 0x1234)
                        word('wBreedMon2ID', owner2)
                        invoke('CheckBreedmonCompatibility.breed_ok')
                        expected = (3 if same_root else 2) - (owner2 == 0x1234)
                        assert regs.A == mem[addr('wBreedingCompatibility')] == expected, (context, owner2, regs.A)
                        assert snapshot() == before, context
                        count += 1
        # Synthetic extended Ditto alias exercises only the identity predicate;
        # it is never sent to catalog/base-data lookups.
        for species in (132, 25):
            for form in (1, 2, 0x21, 0x22):
                for metadata in (0, 0x40, 0x80, 0xC0):
                    put('wCurPartySpecies', species)
                    put('wCurForm', form | metadata)
                    assert invoke('CheckBreedmonCompatibility.IsDitto') == (species == 132 and not form & 0x20), (species, form, metadata)
                    preserved()
                    count += 1
        print(f'PASS: {count} native daycare breeding cases; full-word root collisions, all mechanical variants, legacy/native/partial markers, metadata, same/different two-byte owner IDs, Ditto aliases and preserved records/registers')
    finally:
        pyboy.stop(save=False)


if __name__ == '__main__':
    main()
