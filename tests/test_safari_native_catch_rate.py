"""CPU tests for Safari catch-rate reset through the enemy native battle identity."""
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
    catch_off = addr("wBaseCatchRate") - addr("wCurBaseData")
    bank, base_addr = syms["BaseDataRecords"]
    base_off = bank * 0x4000 + base_addr - 0x4000

    pyboy = PyBoy(str(rom), window="null", sound_emulated=False,
                  cgb=True, log_level="ERROR")
    memory, regs = pyboy.memory, pyboy.register_file

    def call_reset():
        bank, target = syms["ResetSafariCatchRateFromEnemyNativeSpecies"]
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
        count = 0

        for native in (25, 256, alolan_raichu):
            # Deliberately conflicting legacy identity proves catch-rate data is
            # selected by the native shadow, while legacy globals retain the
            # old side effect expected by surrounding battle code.
            memory[addr("wEnemyMonSpecies")] = 150
            memory[addr("wEnemyMonForm")] = 0x41
            memory[addr("wCurSpecies")] = 1
            memory[addr("wCurForm")] = 2
            memory[addr("wEnemyMonCatchRate")] = 0xA5
            memory[addr("wEnemyMonNativeSpecies"):addr("wEnemyMonNativeSpecies") + 2] = (
                list(native.to_bytes(2, "little"))
            )

            call_reset()

            expected = data[
                base_off + (native - 1) * base_size + catch_off
            ]
            assert memory[addr("wEnemyMonCatchRate")] == expected
            assert memory[addr("wCurSpecies")] == 150
            assert memory[addr("wCurForm")] == 0x41
            count += 1

        # Empty native shadow leaves the current catch rate unchanged while
        # preserving the same legacy-global publication behavior.
        memory[addr("wEnemyMonSpecies")] = 25
        memory[addr("wEnemyMonForm")] = 0x82
        memory[addr("wCurSpecies")] = 1
        memory[addr("wCurForm")] = 2
        memory[addr("wEnemyMonCatchRate")] = 0x5A
        memory[addr("wEnemyMonNativeSpecies"):addr("wEnemyMonNativeSpecies") + 2] = [0, 0]

        call_reset()

        assert memory[addr("wEnemyMonCatchRate")] == 0x5A
        assert memory[addr("wCurSpecies")] == 25
        assert memory[addr("wCurForm")] == 0x82
        count += 1

        print(
            f"PASS: {count} Safari native catch-rate cases; "
            "ordinary/extended/variant IDs, empty shadow, exact ROM catch rate "
            "and preserved legacy-global side effects"
        )
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
