"""CPU tests for Low Kick weight lookup through the opposing native identity."""
import argparse
from pathlib import Path

from pyboy import PyBoy


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom", type=Path)
    rom = ap.parse_args().rom

    syms = {}
    for line in rom.with_suffix(".sym").read_text().splitlines():
        fields = line.split()
        if len(fields) == 2 and ":" in fields[0]:
            syms[fields[1]] = tuple(int(v, 16) for v in fields[0].split(":"))

    def addr(name):
        return syms[name][1]

    data = rom.read_bytes()
    bank, table_addr = syms["NativeVariantIdentityTable"]
    table_off = bank * 0x4000 + table_addr - 0x4000
    alolan_raichu = next(
        int.from_bytes(data[pos:pos + 2], "little")
        for pos in range(table_off, table_off + 5 * 100, 5)
        if int.from_bytes(data[pos + 2:pos + 4], "little") == 26
        and data[pos + 4] == 2
    )

    pyboy = PyBoy(str(rom), window="null", sound_emulated=False,
                  cgb=True, log_level="ERROR")
    memory, regs = pyboy.memory, pyboy.register_file

    def call_low_kick():
        bank, target = syms["BattleCommand_lowkick"]
        memory[0x2000] = bank
        memory[addr("hROMBank")] = bank
        memory[0xC100:0xC106] = [
            0xF3, 0xCD, target & 0xFF, target >> 8, 0x18, 0xFE
        ]
        regs.B, regs.C, regs.D, regs.E = 0x12, 0x34, 0x56, 0x78
        regs.SP, regs.PC = 0xC0FF, 0xC100
        pyboy.tick(12, False, False)
        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF), (turn, native, has_light, ignore, hex(regs.PC), hex(regs.SP))
        assert (regs.B, regs.C, regs.E) == (0x12, 0x34, 0x78)
        assert memory[addr("hROMBank")] == bank
        assert memory[0xFF70] & 7 == 1
        return regs.D

    try:
        memory[0xFF50] = 1
        memory[0xFFFF] = memory[0xFF0F] = memory[0xFF40] = 0
        memory[0xFF70] = 1
        count = 0

        # Expected powers preserve this fork's existing weight thresholds.
        # native ID, power without Light Metal, power with Light Metal
        cases = ((25, 80, 60), (59, 100, 80), (143, 120, 120),
                 (256, 20, 20), (alolan_raichu, 80, 80), (0, 20, 20))
        ability_names = [line.split()[1] for line in
                         (Path(__file__).resolve().parents[1] /
                          "constants/ability_constants.asm").read_text().splitlines()
                         if line.strip().startswith("const ")]
        light_metal = ability_names.index("LIGHT_METAL")
        for turn in (0, 1):
            memory[addr("hBattleTurn")] = turn
            opponent = "wEnemy" if turn == 0 else "wBattle"
            user = "wBattle" if turn == 0 else "wEnemy"
            ability = "wEnemyAbility" if turn == 0 else "wPlayerAbility"
            for native, normal, light in cases:
                for has_light, ignore in ((False, False), (True, False), (True, True)):
                    for side, identity in ((opponent, native), (user, 143)):
                        target = addr(side + "MonNativeSpecies")
                        memory[target:target + 2] = list(identity.to_bytes(2, "little"))
                        memory[addr(side + "MonSpecies")] = 59
                        memory[addr(side + "MonForm")] = 0
                    memory[addr("wPlayerAbility")] = 0
                    memory[addr("wEnemyAbility")] = 0
                    memory[addr(ability)] = light_metal if has_light else 0
                    memory[addr("wMoveState")] = (4 << (4 * turn)) if ignore else 0
                    expected = light if has_light and not ignore else normal
                    actual = call_low_kick()
                    assert actual == expected, (turn, native, has_light, ignore, actual, expected)
                    count += 1
        print(f"PASS: {count} Low Kick native-weight CPU cases")
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
