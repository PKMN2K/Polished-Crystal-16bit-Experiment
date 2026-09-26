"""CPU tests for active native species-list matching used by battle animations."""
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

    list_addr = 0xC300
    native_list = (25, 256, alolan_raichu)

    def write_list():
        pos = list_addr
        for native in native_list:
            memory[pos:pos + 2] = list(native.to_bytes(2, "little"))
            pos += 2
        memory[pos:pos + 2] = [0, 0]

    def call_match():
        bank, target = syms["IsActiveBattleNativeSpeciesInList"]
        memory[0x2000] = bank
        memory[addr("hROMBank")] = bank
        memory[0xC100:0xC106] = [
            0xF3, 0xCD, target & 0xFF, target >> 8, 0x18, 0xFE
        ]
        regs.HL = list_addr
        regs.DE = 0x5678
        regs.SP, regs.PC = 0xC0FF, 0xC100
        pyboy.tick(4, False, False)
        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF)
        assert regs.DE == 0x5678
        assert memory[addr("hROMBank")] == bank
        assert memory[0xFF70] & 7 == 1
        return bool(regs.F & 0x10)

    try:
        memory[0xFF50] = 1
        memory[0xFFFF] = memory[0xFF0F] = memory[0xFF40] = 0
        memory[0xFF70] = 1
        write_list()
        count = 0

        for turn, active_shadow, other_shadow, active_legacy, other_legacy in (
            (0, "wBattleMonNativeSpecies", "wEnemyMonNativeSpecies",
             "wBattleMonSpecies", "wEnemyMonSpecies"),
            (1, "wEnemyMonNativeSpecies", "wBattleMonNativeSpecies",
             "wEnemyMonSpecies", "wBattleMonSpecies"),
        ):
            # Matching ordinary, species #256 and regional/mechanical IDs.
            for native in native_list:
                memory[addr("hBattleTurn")] = turn
                memory[addr(active_shadow):addr(active_shadow) + 2] = (
                    list(native.to_bytes(2, "little"))
                )
                memory[addr(other_shadow):addr(other_shadow) + 2] = (
                    list((59).to_bytes(2, "little"))
                )
                # Legacy bytes deliberately disagree with the native identity.
                memory[addr(active_legacy)] = 150
                memory[addr(other_legacy)] = 241

                assert call_match()
                count += 1

            # Wrong-side selection would falsely match here: only the inactive
            # battler is in the list.
            memory[addr("hBattleTurn")] = turn
            memory[addr(active_shadow):addr(active_shadow) + 2] = list((59).to_bytes(2, "little"))
            memory[addr(other_shadow):addr(other_shadow) + 2] = list((25).to_bytes(2, "little"))
            memory[addr(active_legacy)] = 241
            memory[addr(other_legacy)] = 241
            assert not call_match()
            count += 1

            # Empty active native identity must not match the list even when
            # both legacy identity and the other active shadow would match.
            memory[addr(active_shadow):addr(active_shadow) + 2] = [0, 0]
            memory[addr(other_shadow):addr(other_shadow) + 2] = list((25).to_bytes(2, "little"))
            memory[addr(active_legacy)] = 241
            memory[addr(other_legacy)] = 241
            assert not call_match()
            count += 1

        print(
            f"PASS: {count} active native species-list cases; "
            "both sides, ordinary/extended/variant IDs, wrong-side guards, "
            "conflicting legacy identity and empty native shadows"
        )
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
