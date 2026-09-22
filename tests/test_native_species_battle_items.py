"""CPU tests for species-restricted held items using active native identity."""
import argparse
from pathlib import Path

from pyboy import PyBoy


def rom_offset(bank, address):
    if bank == 0:
        return address
    return bank * 0x4000 + address - 0x4000


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
    table_bank, table_addr = syms["ValidBattleItemTableNative"]
    table_off = rom_offset(table_bank, table_addr)
    item = data[table_off]
    native = int.from_bytes(data[table_off + 1:table_off + 3], "little")
    assert item != 0xFF
    assert native != 0

    pyboy = PyBoy(str(rom), window="null", sound_emulated=False,
                  cgb=True, log_level="ERROR")
    memory, regs = pyboy.memory, pyboy.register_file

    def call_valid():
        bank, target = syms["UserValidBattleItem"]
        memory[0x2000] = bank
        memory[addr("hROMBank")] = bank
        memory[0xC100:0xC106] = [
            0xF3, 0xCD, target & 0xFF, target >> 8, 0x18, 0xFE
        ]
        regs.BC = 0x1234
        regs.DE = 0x5678
        regs.HL = 0xC222
        regs.SP, regs.PC = 0xC0FF, 0xC100
        pyboy.tick(6, False, False)
        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF)
        assert regs.BC == 0x1234
        assert regs.DE == 0x5678
        assert regs.HL == 0xC222
        assert memory[addr("hROMBank")] == bank
        assert memory[0xFF70] & 7 == 1
        return bool(regs.F & 0x80)

    try:
        memory[0xFF50] = 1
        memory[0xFFFF] = memory[0xFF0F] = memory[0xFF40] = 0
        memory[0xFF70] = 1
        count = 0

        sides = (
            (0, "wBattleMonItem", "wBattleMonNativeSpecies",
             "wBattleMonSpecies", "wBattleMonForm"),
            (1, "wEnemyMonItem", "wEnemyMonNativeSpecies",
             "wEnemyMonSpecies", "wEnemyMonForm"),
        )

        for turn, item_addr, shadow, legacy_species, legacy_form in sides:
            memory[addr("hBattleTurn")] = turn
            memory[addr(item_addr)] = item

            # Native identity matches while the legacy species/form deliberately
            # disagrees. The species-restricted item must still be valid.
            memory[addr(shadow):addr(shadow) + 2] = list(native.to_bytes(2, "little"))
            memory[addr(legacy_species)] = 150
            memory[addr(legacy_form)] = 0x20
            assert call_valid()
            count += 1

            # Same low byte but a different high byte must not match.
            wrong_high = ((native + 0x100) & 0xFFFF) or 0x100
            memory[addr(shadow):addr(shadow) + 2] = list(wrong_high.to_bytes(2, "little"))
            assert not call_valid()
            count += 1

            # Empty native identity must not fall back to matching legacy data.
            memory[addr(shadow):addr(shadow) + 2] = [0, 0]
            memory[addr(legacy_species)] = native & 0xFF
            memory[addr(legacy_form)] = (native >> 8) << 5 & 0x20
            assert not call_valid()
            count += 1

            # Correct native species with a different item is not valid.
            memory[addr(shadow):addr(shadow) + 2] = list(native.to_bytes(2, "little"))
            memory[addr(item_addr)] = (item + 1) & 0xFF
            if memory[addr(item_addr)] == 0xFF:
                memory[addr(item_addr)] = (item + 2) & 0xFF
            assert not call_valid()
            count += 1
            memory[addr(item_addr)] = item

        print(
            f"PASS: {count} native species-restricted held-item cases; "
            "both active sides, legacy disagreement, full-word mismatch, "
            "empty shadows and wrong-item guards"
        )
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
