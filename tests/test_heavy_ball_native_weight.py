"""CPU tests for Heavy Ball weight lookup through the enemy native battle identity."""
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

    def call_heavy_ball():
        bank, target = syms["HeavyBallMultiplier"]
        memory[0x2000] = bank
        memory[addr("hROMBank")] = bank
        memory[0xC100:0xC106] = [
            0xF3, 0xCD, target & 0xFF, target >> 8, 0x18, 0xFE
        ]
        regs.SP, regs.PC = 0xC0FF, 0xC100
        pyboy.tick(12, False, False)
        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF)
        assert memory[addr("hROMBank")] == bank
        assert memory[0xFF70] & 7 == 1

    try:
        memory[0xFF50] = 1
        memory[0xFFFF] = memory[0xFF0F] = memory[0xFF40] = 0
        memory[0xFF70] = 1
        count = 0

        # Native identity, deliberately conflicting legacy identity, expected
        # Heavy Ball-adjusted catch rate. Weights are in 0.1 kg units:
        # Pikachu 60 (<1024), Arcanine 1550 (<2048), Snorlax 4600 (>4096),
        # native ID 256 is the zero-weight reserved mechanical entry, and
        # Alolan Raichu is 210 (<1024).
        cases = (
            (25, 143, 80),
            (59, 25, 100),
            (143, 25, 140),
            (256, 143, 80),
            (alolan_raichu, 143, 80),
        )

        for native, legacy_species, expected in cases:
            memory[addr("wEnemyMonSpecies")] = legacy_species & 0xFF
            memory[addr("wEnemyMonForm")] = 0
            memory[addr("wEnemyMonCatchRate")] = 100
            memory[addr("wEnemyMonNativeSpecies"):addr("wEnemyMonNativeSpecies") + 2] = (
                list(native.to_bytes(2, "little"))
            )

            call_heavy_ball()

            assert memory[addr("wEnemyMonCatchRate")] == expected
            count += 1

        # Empty native shadow must not fall back to a conflicting legacy
        # species and must leave the catch rate unchanged.
        memory[addr("wEnemyMonSpecies")] = 143
        memory[addr("wEnemyMonForm")] = 0
        memory[addr("wEnemyMonCatchRate")] = 100
        memory[addr("wEnemyMonNativeSpecies"):addr("wEnemyMonNativeSpecies") + 2] = [0, 0]

        call_heavy_ball()

        assert memory[addr("wEnemyMonCatchRate")] == 100
        count += 1

        print(
            f"PASS: {count} Heavy Ball native-weight cases; "
            "ordinary/extended/variant IDs, threshold behavior, conflicting "
            "legacy identity and empty native shadow"
        )
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
