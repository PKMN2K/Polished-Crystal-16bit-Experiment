"""Test native faint-cry selection and parameters; audio playback is stubbed."""
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
    def addr(name):
        return syms[name][1]
    def offset(name):
        bank, address = syms[name]
        return bank * 0x4000 + address - (0x4000 if bank else 0)
    data = rom.read_bytes()
    root = Path(__file__).resolve().parents[1]
    variant_count = sum(line.strip().startswith('native_variant_identity ')
                        for line in (root / 'data/pokemon/native_variant_name_roots.asm').read_text().splitlines())
    start = offset('NativeVariantIdentityTable')
    variants = [(int.from_bytes(data[p:p+2], 'little'), int.from_bytes(data[p+2:p+4], 'little'))
                for p in range(start, start + variant_count * 5, 5)]
    num_roots = variants[0][0] - 1
    cases = [(n, n) for n in range(num_roots + 1)] + variants
    pyboy = PyBoy(str(rom), window='null', sound_emulated=False, cgb=True, log_level='ERROR')
    mem, regs = pyboy.memory, pyboy.register_file
    calls = []
    def capture(_):
        calls.append((regs.D * 256 + regs.E, word('wCryPitch'), word('wCryLength')))
    def word(name):
        return mem[addr(name)] + 256 * mem[addr(name) + 1]
    def run(name, bc=0):
        bank, target = syms[name]
        mem[0x2000] = bank
        mem[addr('hROMBank')] = bank
        mem[0xC100:0xC106] = [0xF3, 0xCD, target & 255, target >> 8, 0x18, 0xFE]
        regs.B, regs.C = bc >> 8, bc & 255
        regs.SP, regs.PC = 0xC0FF, 0xC100
        pyboy.tick(4, False, False)
        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF), (name, hex(regs.PC))
        assert mem[addr('hROMBank')] == bank
        assert mem[0xFF70] & 7 == 1
    count = 0
    try:
        mem[0xFF50] = 1
        mem[0xFFFF] = mem[0xFF0F] = mem[0xFF40] = 0
        mem[0xFF70] = 1
        for name in ('_PlayCry', 'WaitSFX'):
            bank, address = syms[name]
            mem[bank, address] = 0xC9
        bank, address = syms['_PlayCry']
        pyboy.hook_register(bank, address, capture, None)
        for turn in (0, 1):
            for native, species in cases:
                for prefix, identity in (('wBattle', native if turn == 0 else 143),
                                         ('wEnemy', native if turn else 143)):
                    address = addr(prefix + 'MonNativeSpecies')
                    mem[address:address + 2] = list(identity.to_bytes(2, 'little'))
                    mem[addr(prefix + 'MonSpecies')] = 59
                    mem[addr(prefix + 'MonForm')] = 0x21
                mem[addr('hBattleTurn')] = turn
                for name, value in (('wCurSpecies', 91), ('wCurForm', 0x23),
                                    ('wStereoPanningMask', 1), ('wCryTracks', 0xF0 if turn == 0 else 0x0F)):
                    mem[addr(name)] = value
                mem[addr('wCryPitch'):addr('wCryPitch') + 2] = [0x34, 0x12]
                mem[addr('wCryLength'):addr('wCryLength') + 2] = [0x78, 0x56]
                calls.clear()
                run('PlayFaintCryFromActiveNativeSpecies')
                if species in (0, 255, 256):
                    assert not calls and word('wCryPitch') == 0x1234 and word('wCryLength') == 0x5678
                else:
                    p = offset('PokemonCryData') + (species - 1) * 5
                    pitch = int.from_bytes(data[p+1:p+3], 'little')
                    length = int.from_bytes(data[p+3:p+5], 'little')
                    expected = (data[p], pitch, (length + length // 2) & 65535)
                    assert calls == [expected], (turn, native, species, calls, expected)
                assert mem[addr('hBattleTurn')] == turn
                assert mem[addr('wCurSpecies')] == 91 and mem[addr('wCurForm')] == 0x23
                assert mem[addr('wStereoPanningMask')] == 1
                assert mem[addr('wCryTracks')] == (0xF0 if turn == 0 else 0x0F)
                count += 1
        # The existing script/legacy entry still uses the shared slow-cry tail.
        for species, form in ((25, 1), (201, 2), (26, 2), (1, 0x21)):
            calls.clear()
            run('PlaySlowCryBC', form * 256 + species)
            native_root = species + (256 if form & 0x20 else 0)
            p = offset('PokemonCryData') + (native_root - 1) * 5
            length = int.from_bytes(data[p+3:p+5], 'little')
            assert calls == [(data[p], int.from_bytes(data[p+1:p+3], 'little'), (length + length // 2) & 65535)]
            count += 1
        print(f'PASS: {count} native faint-cry and legacy slow-cry CPU cases')
    finally:
        pyboy.stop(save=False)


if __name__ == '__main__':
    main()
