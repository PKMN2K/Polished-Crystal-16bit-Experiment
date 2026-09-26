"""CPU tests for active battle ability reset through native species identity shadows."""
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

    base_size = addr("wCurBaseDataEnd") - addr("wCurBaseData")
    ability_off = addr("wBaseAbility1") - addr("wCurBaseData")
    bank, base_addr = syms["BaseDataRecords"]
    base_off = bank * 0x4000 + base_addr - 0x4000

    pyboy = PyBoy(str(rom), window="null", sound_emulated=False,
                  cgb=True, log_level="ERROR")
    memory, regs = pyboy.memory, pyboy.register_file

    def call(label):
        bank, target = syms[label]
        memory[0x2000] = bank
        memory[addr("hROMBank")] = bank
        memory[0xC100:0xC106] = [
            0xF3, 0xCD, target & 0xFF, target >> 8, 0x18, 0xFE
        ]
        regs.SP, regs.PC = 0xC0FF, 0xC100
        pyboy.tick(6, False, False)
        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF)
        assert memory[addr("hROMBank")] == bank
        assert memory[0xFF70] & 7 == 1

    try:
        memory[0xFF50] = 1
        memory[0xFFFF] = memory[0xFF0F] = memory[0xFF40] = 0
        memory[0xFF70] = 1
        memory[addr("wInitialOptions")] = 0xFF
        count = 0

        sides = (
            ("ResetPlayerAbility", "wBattleMonNativeSpecies",
             "wBattleMonSpecies", "wBattleMonPersonality", "wPlayerAbility"),
            ("ResetEnemyAbility", "wEnemyMonNativeSpecies",
             "wEnemyMonSpecies", "wEnemyMonPersonality", "wEnemyAbility"),
        )

        for label, shadow, legacy, personality, out in sides:
            for native in (25, 256, alolan_raichu):
                # Deliberately conflict the legacy byte species with the native
                # identity. Ability slot 1 is selected by a zero personality byte.
                memory[addr(legacy)] = 150
                memory[addr(personality)] = 0
                memory[addr(personality) + 1] = 0
                memory[addr(shadow):addr(shadow) + 2] = list(native.to_bytes(2, "little"))
                memory[addr(out)] = 0xA5

                call(label)

                expected = data[
                    base_off + (native - 1) * base_size + ability_off
                ]
                assert memory[addr(out)] == expected
                assert int.from_bytes(
                    bytes(memory[addr(shadow):addr(shadow) + 2]), "little"
                ) == native
                count += 1

            # An empty native shadow must not fall back to the legacy byte
            # species; it resolves to no active ability.
            memory[addr(legacy)] = 150
            memory[addr(personality)] = 0
            memory[addr(personality) + 1] = 0
            memory[addr(shadow):addr(shadow) + 2] = [0, 0]
            memory[addr(out)] = 0xA5

            call(label)

            assert memory[addr(out)] == 0
            count += 1

        print(
            f"PASS: {count} active native ability-reset cases; "
            "both sides, ordinary/extended/variant IDs, conflicting legacy "
            "identity and empty native shadows"
        )
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
