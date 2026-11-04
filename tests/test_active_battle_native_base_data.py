"""CPU tests for base-data lookup through active native battle identity shadows."""
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
    bank, base_addr = syms["BaseDataRecords"]
    base_off = bank * 0x4000 + base_addr - 0x4000

    pyboy = PyBoy(str(rom), window="null", sound_emulated=False,
                  cgb=True, log_level="ERROR")
    memory, regs = pyboy.memory, pyboy.register_file

    def call_helper():
        bank, target = syms["GetBaseDataFromActiveBattleNativeSpecies"]
        memory[0x2000] = bank
        memory[addr("hROMBank")] = bank
        memory[0xC100:0xC106] = [
            0xF3, 0xCD, target & 0xFF, target >> 8, 0x18, 0xFE
        ]
        regs.B, regs.C, regs.D, regs.E, regs.HL = 0x12, 0x34, 0x56, 0x78, 0xC222
        regs.SP, regs.PC = 0xC0FF, 0xC100
        pyboy.tick(4, False, False)
        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF)
        assert memory[addr("hROMBank")] == bank
        assert memory[0xFF70] & 7 == 1

    count = 0
    try:
        memory[0xFF50] = 1
        memory[0xFFFF] = memory[0xFF0F] = memory[0xFF40] = 0
        memory[0xFF70] = 1

        globals_ = ("wCurSpecies", "wCurPartySpecies", "wCurForm")
        cases = (25, 256, alolan_raichu)

        for turn, shadow in (
            (0, "wBattleMonNativeSpecies"),
            (1, "wEnemyMonNativeSpecies"),
        ):
            other = "wEnemyMonNativeSpecies" if turn == 0 else "wBattleMonNativeSpecies"
            for native in cases:
                memory[addr("hBattleTurn")] = turn
                memory[addr(shadow):addr(shadow) + 2] = list(native.to_bytes(2, "little"))
                memory[addr(other):addr(other) + 2] = list((1).to_bytes(2, "little"))

                # Deliberately conflicting legacy globals prove this lookup is
                # driven only by the native battle shadow.
                for name, value in zip(globals_, (91, 92, 0x23)):
                    memory[addr(name)] = value
                memory[addr("wCurBaseData"):addr("wCurBaseDataEnd")] = [0xA5] * base_size

                call_helper()

                expected = list(
                    data[base_off + (native - 1) * base_size:
                         base_off + native * base_size]
                )
                assert list(memory[addr("wCurBaseData"):addr("wCurBaseDataEnd")]) == expected
                assert not regs.F & 0x10
                assert (regs.B, regs.C, regs.D, regs.E, regs.HL) == (
                    0x12, 0x34, 0x56, 0x78, 0xC222
                )
                assert [memory[addr(name)] for name in globals_] == [91, 92, 0x23]
                assert int.from_bytes(
                    bytes(memory[addr(shadow):addr(shadow) + 2]), "little"
                ) == native
                count += 1

            memory[addr("hBattleTurn")] = turn
            memory[addr(shadow):addr(shadow) + 2] = [0, 0]
            memory[addr("wCurBaseData"):addr("wCurBaseDataEnd")] = [0xA5] * base_size
            call_helper()
            assert regs.F & 0x10
            assert list(memory[addr("wCurBaseData"):addr("wCurBaseDataEnd")]) == [0xA5] * base_size
            count += 1

        print(
            f"PASS: {count} active native battle base-data cases; "
            "both sides, ordinary/extended/variant IDs, exact ROM data, "
            "empty shadows and register/global preservation"
        )
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
