"""CPU tests for native identity bridges at battle picture-refresh boundaries.

Renderer entry points are stubbed in integration cases: this tests identity,
base data, dispatch and restoration, not decompression or displayed graphics.
"""
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
    data = rom.read_bytes()
    def offset(name):
        bank, address = syms[name]
        return bank * 0x4000 + address - (0x4000 if bank else 0)
    root = Path(__file__).resolve().parents[1]
    count_variants = sum(line.strip().startswith('native_variant_identity ')
                         for line in (root / 'data/pokemon/native_variant_name_roots.asm').read_text().splitlines())
    variants = []
    start = offset('NativeVariantIdentityTable')
    for pos in range(start, start + count_variants * 5, 5):
        native = int.from_bytes(data[pos:pos + 2], 'little')
        species = int.from_bytes(data[pos + 2:pos + 4], 'little')
        form = data[pos + 4]
        variants.append((native, 0xFF, species & 255, form | ((species >> 8) << 5)))
    # Native root #257 must keep its extended bit, while stale extended bits
    # on low IDs must be discarded. Root Raichu must not become Alolan.
    cases = [(25, 0xE1, 25, 1), (257, 1, 1, 0x21),
             (201, 0xE2, 201, 2), (25, 3, 25, 3), (26, 2, 26, 1)] + variants
    pyboy = PyBoy(str(rom), window='null', sound_emulated=False, cgb=True, log_level='ERROR')
    memory, regs = pyboy.memory, pyboy.register_file
    globals_ = ('wCurSpecies', 'wCurPartySpecies', 'wCurForm')
    initial = (91, 92, 0x23)
    base_start, base_end = addr('wCurBaseData'), addr('wCurBaseDataEnd')
    base_size = base_end - base_start
    count = 0
    def setup(side, turn, native, raw):
        memory[addr('hBattleTurn')] = turn
        for prefix, identity in (('wBattle', native if side == 'Player' else 143),
                                 ('wEnemy', native if side == 'Enemy' else 143)):
            address = addr(prefix + 'MonNativeSpecies')
            memory[address:address + 2] = list(identity.to_bytes(2, 'little'))
            memory[addr(prefix + 'MonSpecies')] = 59
            memory[addr(prefix + 'MonForm')] = raw if identity == native else 1
        for name, value in zip(globals_, initial):
            memory[addr(name)] = value
        memory[base_start:base_end] = [0xA5] * base_size
    def call(name):
        bank, target = syms[name]
        memory[0x2000] = bank
        memory[addr('hROMBank')] = bank
        memory[0xC100:0xC106] = [0xF3, 0xCD, target & 255, target >> 8, 0x18, 0xFE]
        regs.B, regs.C, regs.D, regs.E, regs.HL = 0x12, 0x34, 0x56, 0x78, 0xC222
        regs.SP, regs.PC = 0xC0FF, 0xC100
        pyboy.tick(4, False, False)
        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF), (name, hex(regs.PC), hex(regs.SP))
        assert memory[addr('hROMBank')] == bank
        assert memory[0xFF70] & 7 == 1
    try:
        memory[0xFF50] = 1
        memory[0xFFFF] = memory[0xFF0F] = memory[0xFF40] = 0
        memory[0xFF70] = 1
        for side in ('Player', 'Enemy'):
            for turn in (0, 1):
                for native, raw, species, form in cases + [(0, 2, 92, 0x23), (256, 2, 92, 0x23)]:
                    setup(side, turn, native, raw)
                    call('Prepare' + side + 'BattlePictureIdentity')
                    assert [memory[addr(n)] for n in globals_] == [91, species, form], (side, native, raw)
                    assert bool(regs.F & 0x10) == (native in (0, 256))
                    assert (regs.B, regs.C, regs.D, regs.E, regs.HL) == (0x12, 0x34, 0x56, 0x78, 0xC222)
                    assert memory[addr('hBattleTurn')] == turn
                    count += 1

        captures = []
        def capture(name):
            captures.append((name, [memory[addr(n)] for n in globals_], list(memory[base_start:base_end])))
        for name in ('GetBackpic', 'PrepareNativeEnemyBattleAnimatedFrontpic', 'DecompressRequest2bpp'):
            bank, address = syms[name]
            memory[bank, address] = 0xC9  # return after capturing renderer inputs
            pyboy.hook_register(bank, address, capture, name)
        for side in ('Player', 'Enemy'):
            for turn in (0, 1):
                for native, raw, species, form in cases[:5] + variants[:3] + [(0, 2, 92, 0x23), (256, 2, 92, 0x23)]:
                    setup(side, turn, native, raw)
                    memory[addr('wBattleType')] = 0
                    captures.clear()
                    call('Drop' + side + 'Sub')
                    assert memory[addr('wCurPartySpecies')] == initial[1]
                    assert memory[addr('wCurForm')] == initial[2]
                    assert memory[addr('hBattleTurn')] == turn
                    if native in (0, 256):
                        assert not captures
                        assert memory[addr('wCurSpecies')] == initial[0]
                    else:
                        expected_name = 'GetBackpic' if side == 'Player' else 'PrepareNativeEnemyBattleAnimatedFrontpic'
                        expected_species = 91 if side == 'Player' else species
                        assert len(captures) == 1 and captures[0][:2] == (expected_name, [expected_species, species, form])
                        if side == 'Enemy':
                            start = offset('BaseDataRecords') + (native - 1) * base_size
                            assert captures[0][2] == list(data[start:start + base_size])
                    count += 1
        # Ghost battles must retain their special image dispatch.
        constants = (root / 'constants/battle_constants.asm').read_text()
        battle_types = constants.split('const BATTLETYPE_NORMAL', 1)[1].split('DEF NUM_BATTLE_TYPES', 1)[0]
        ghost = 1 + [line.split()[1] for line in battle_types.splitlines()
                     if line.strip().startswith('const ')].index('BATTLETYPE_GHOST')
        for turn in (0, 1):
            setup('Enemy', turn, 25, 1)
            memory[addr('wBattleType')] = ghost
            captures.clear()
            call('DropEnemySub')
            assert len(captures) == 1 and captures[0][:2] == ('DecompressRequest2bpp', [25, 25, 1])
            assert memory[addr('wCurPartySpecies')] == initial[1]
            assert memory[addr('wCurForm')] == initial[2]
            assert memory[addr('hBattleTurn')] == turn
            count += 1
        print(f'PASS: {count} native battle-picture CPU cases; helper identities and stubbed renderer boundaries')
    finally:
        pyboy.stop(save=False)


if __name__ == '__main__':
    main()
