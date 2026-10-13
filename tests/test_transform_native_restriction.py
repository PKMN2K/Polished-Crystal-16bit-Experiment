"""CPU tests for Transform's native Mewtwo/Armor Suit restriction.

Run the real Transform entry through its early checks. Stub the failure branch
and the continuation immediately after the restriction, not the identity lookup.
This does not execute the remainder of Transform or its animations.
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
    bank, address = syms['NativeVariantIdentityTable']
    start = bank * 0x4000 + address - 0x4000
    root = Path(__file__).resolve().parents[1]
    count_variants = sum(line.strip().startswith('native_variant_identity ')
                         for line in (root / 'data/pokemon/native_variant_name_roots.asm').read_text().splitlines())
    cases = [(0, 0), (25, 25), (150, 150), (256, 256), (257, 257)]
    cases += [(int.from_bytes(data[p:p + 2], 'little'),
               int.from_bytes(data[p + 2:p + 4], 'little'))
              for p in range(start, start + 5 * count_variants, 5)]
    armored = next(native for native, species in cases if native != 150 and species == 150)
    # ARMOR_SUIT is the existing item ID $be, unchanged by species migration.
    armor_suit = 0xBE
    pyboy = PyBoy(str(rom), window='null', sound_emulated=False, cgb=True, log_level='ERROR')
    memory, regs = pyboy.memory, pyboy.register_file
    count = 0
    try:
        memory[0xFF50] = 1
        memory[0xFFFF] = memory[0xFF0F] = memory[0xFF40] = 0
        memory[0xFF70] = 1
        for name, target in [('BattleCommand_transform.not_armored_mewtwo', 0xC110),
                             ('BattleEffect_ButItFailed', 0xC120)]:
            bank, address = syms[name]
            memory[bank, address:address + 3] = [0xC3, target & 255, target >> 8]
        memory[0xC110:0xC113] = [0x3E, 0, 0xC9]
        memory[0xC120:0xC123] = [0x3E, 1, 0xC9]
        bank, target = syms['BattleCommand_transform']
        memory[0xC100:0xC106] = [0xF3, 0xCD, target & 255, target >> 8, 0x18, 0xFE]
        globals_ = ('wCurSpecies', 'wCurPartySpecies', 'wCurForm')
        for turn in (0, 1):
            opponent = 'wEnemy' if turn == 0 else 'wBattle'
            user = 'wBattle' if turn == 0 else 'wEnemy'
            opponent_status = 'wEnemySubStatus2' if turn == 0 else 'wPlayerSubStatus2'
            for native, species in cases:
                for item in (0, armor_suit):
                    for legacy in (25, 150):
                        memory[addr('hBattleTurn')] = turn
                        for prefix, identity, held in ((opponent, native, item), (user, armored, armor_suit)):
                            address = addr(prefix + 'MonNativeSpecies')
                            memory[address:address + 2] = list(identity.to_bytes(2, 'little'))
                            memory[addr(prefix + 'MonSpecies')] = legacy
                            memory[addr(prefix + 'MonForm')] = 0x21
                            memory[addr(prefix + 'MonItem')] = held
                        memory[addr('wPlayerSubStatus2')] = 0
                        memory[addr('wEnemySubStatus2')] = 0
                        for name, value in zip(globals_, (91, 92, 0x23)):
                            memory[addr(name)] = value
                        memory[0x2000] = bank
                        memory[addr('hROMBank')] = bank
                        regs.SP, regs.PC = 0xC0FF, 0xC100
                        pyboy.tick(4, False, False)
                        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF)
                        assert regs.A == int(species == 150 and item == armor_suit), (turn, native, item, legacy)
                        assert memory[addr('hROMBank')] == bank
                        assert memory[0xFF70] & 7 == 1
                        assert memory[addr('hBattleTurn')] == turn
                        assert [memory[addr(n)] for n in globals_] == [91, 92, 0x23]
                        count += 1
            # A transformed target must still fail before this new check.
            memory[addr(opponent_status)] = 1 << 4
            memory[addr(opponent + 'MonItem')] = 0
            memory[0x2000] = bank
            memory[addr('hROMBank')] = bank
            regs.SP, regs.PC = 0xC0FF, 0xC100
            pyboy.tick(4, False, False)
            assert (regs.PC, regs.SP, regs.A) == (0xC104, 0xC0FF, 1)
            count += 1
        print(f'PASS: {count} Transform native-restriction CPU cases')
    finally:
        pyboy.stop(save=False)


if __name__ == '__main__':
    main()
