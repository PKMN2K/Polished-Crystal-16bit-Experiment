"""CPU tests for native active-battle identity synchronization through Transform."""
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

    def call_copy():
        bank, target = syms["CopyTransformNativeIdentity"]
        memory[0x2000] = bank
        memory[addr("hROMBank")] = bank
        memory[0xC100:0xC106] = [
            0xF3, 0xCD, target & 0xFF, target >> 8, 0x18, 0xFE
        ]
        regs.SP, regs.PC = 0xC0FF, 0xC100
        pyboy.tick(4, False, False)
        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF)
        assert memory[addr("hROMBank")] == bank
        assert memory[0xFF70] & 7 == 1

    try:
        memory[0xFF50] = 1
        memory[0xFFFF] = memory[0xFF0F] = memory[0xFF40] = 0
        memory[0xFF70] = 1
        count = 0

        cases = (25, 256, alolan_raichu, 0)

        # Player transforms: copy enemy native identity into player shadow.
        for native in cases:
            player_before = 143
            memory[addr("hBattleTurn")] = 0
            memory[addr("wBattleMonNativeSpecies"):addr("wBattleMonNativeSpecies") + 2] = (
                list(player_before.to_bytes(2, "little"))
            )
            memory[addr("wEnemyMonNativeSpecies"):addr("wEnemyMonNativeSpecies") + 2] = (
                list(native.to_bytes(2, "little"))
            )

            call_copy()

            player_after = int.from_bytes(
                bytes(memory[
                    addr("wBattleMonNativeSpecies"):
                    addr("wBattleMonNativeSpecies") + 2
                ]), "little"
            )
            enemy_after = int.from_bytes(
                bytes(memory[
                    addr("wEnemyMonNativeSpecies"):
                    addr("wEnemyMonNativeSpecies") + 2
                ]), "little"
            )
            assert player_after == native
            assert enemy_after == native
            count += 1

        # Enemy transforms: copy player native identity into enemy shadow.
        for native in cases:
            enemy_before = 59
            memory[addr("hBattleTurn")] = 1
            memory[addr("wBattleMonNativeSpecies"):addr("wBattleMonNativeSpecies") + 2] = (
                list(native.to_bytes(2, "little"))
            )
            memory[addr("wEnemyMonNativeSpecies"):addr("wEnemyMonNativeSpecies") + 2] = (
                list(enemy_before.to_bytes(2, "little"))
            )

            call_copy()

            player_after = int.from_bytes(
                bytes(memory[
                    addr("wBattleMonNativeSpecies"):
                    addr("wBattleMonNativeSpecies") + 2
                ]), "little"
            )
            enemy_after = int.from_bytes(
                bytes(memory[
                    addr("wEnemyMonNativeSpecies"):
                    addr("wEnemyMonNativeSpecies") + 2
                ]), "little"
            )
            assert player_after == native
            assert enemy_after == native
            count += 1

        print(
            f"PASS: {count} Transform native-shadow synchronization cases; "
            "both directions, ordinary/extended/variant IDs and empty shadow"
        )
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
