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

    # Parse the compiled item + native-root table instead of hardcoding item IDs.
    table_bank, table_addr = syms["ValidBattleItemTableNative"]
    pos = rom_offset(table_bank, table_addr)
    records = []
    while data[pos] != 0xFF:
        records.append((
            data[pos],
            int.from_bytes(data[pos + 1:pos + 3], "little"),
        ))
        pos += 3
    assert records

    # Pick a table root that has a native mechanical variant. This verifies the
    # old zero-form wildcard semantics survived the migration (e.g. a regional
    # Farfetch'd/Marowak still qualifies for the root species' item effect).
    roots = {root for _, root in records}
    variant_bank, variant_addr = syms["NativeVariantIdentityTable"]
    variant_off = rom_offset(variant_bank, variant_addr)
    variant_match = None
    for p in range(variant_off, variant_off + 5 * 100, 5):
        native = int.from_bytes(data[p:p + 2], "little")
        root = int.from_bytes(data[p + 2:p + 4], "little")
        if native and root in roots and native != root:
            variant_match = (native, root)
            break
    assert variant_match is not None
    variant, root = variant_match

    item = next(item for item, record_root in records if record_root == root)
    unrelated = next(record_root for _, record_root in records if record_root != root)

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
        pyboy.tick(8, False, False)
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

            # Root native identity matches even when legacy species/form disagrees.
            memory[addr(shadow):addr(shadow) + 2] = list(root.to_bytes(2, "little"))
            memory[addr(legacy_species)] = 150
            memory[addr(legacy_form)] = 0x20
            assert call_valid()
            count += 1

            # A mechanical native variant with the same root must also match,
            # preserving the old zero-form wildcard behavior.
            memory[addr(shadow):addr(shadow) + 2] = list(variant.to_bytes(2, "little"))
            assert call_valid()
            count += 1

            # A different root does not qualify, even if legacy bytes claim the
            # qualifying species.
            memory[addr(shadow):addr(shadow) + 2] = list(unrelated.to_bytes(2, "little"))
            memory[addr(legacy_species)] = root & 0xFF
            memory[addr(legacy_form)] = 0
            assert not call_valid()
            count += 1

            # Empty native identity must not fall back to the legacy identity.
            memory[addr(shadow):addr(shadow) + 2] = [0, 0]
            assert not call_valid()
            count += 1

            # Correct root with no held item is invalid.
            memory[addr(shadow):addr(shadow) + 2] = list(root.to_bytes(2, "little"))
            memory[addr(item_addr)] = 0
            assert not call_valid()
            count += 1
            memory[addr(item_addr)] = item

        print(
            f"PASS: {count} native species-restricted held-item cases; "
            "both active sides, mechanical-variant root matching, legacy "
            "disagreement, unrelated roots, empty shadows and wrong-item guards"
        )
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
