"""CPU tests for exact opponent matching through active native battle identity."""
import argparse
from pathlib import Path

from pyboy import PyBoy


DITTO = 132


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

    pyboy = PyBoy(str(rom), window="null", sound_emulated=False,
                  cgb=True, log_level="ERROR")
    memory, regs = pyboy.memory, pyboy.register_file

    def call_match(native):
        bank, target = syms["IsOpponentActiveNativeSpeciesBC"]
        memory[0x2000] = bank
        memory[addr("hROMBank")] = bank
        memory[0xC100:0xC106] = [
            0xF3, 0xCD, target & 0xFF, target >> 8, 0x18, 0xFE
        ]
        regs.BC = native
        regs.HL = 0xC222
        regs.SP, regs.PC = 0xC0FF, 0xC100
        pyboy.tick(4, False, False)
        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF)
        assert regs.HL == 0xC222
        assert memory[addr("hROMBank")] == bank
        assert memory[0xFF70] & 7 == 1
        return bool(regs.F & 0x80)

    try:
        memory[0xFF50] = 1
        memory[0xFFFF] = memory[0xFF0F] = memory[0xFF40] = 0
        memory[0xFF70] = 1
        count = 0

        # hBattleTurn 0: player's opponent is the enemy shadow.
        memory[addr("hBattleTurn")] = 0
        memory[addr("wBattleMonNativeSpecies"):addr("wBattleMonNativeSpecies") + 2] = (
            list((25).to_bytes(2, "little"))
        )
        memory[addr("wEnemyMonNativeSpecies"):addr("wEnemyMonNativeSpecies") + 2] = (
            list((DITTO).to_bytes(2, "little"))
        )
        # Deliberately conflicting legacy bytes prove they are irrelevant.
        memory[addr("wBattleMonSpecies")] = DITTO
        memory[addr("wEnemyMonSpecies")] = 150
        assert call_match(DITTO)
        count += 1
        assert not call_match(25)
        count += 1

        # hBattleTurn 1: enemy's opponent is the player shadow.
        memory[addr("hBattleTurn")] = 1
        memory[addr("wBattleMonNativeSpecies"):addr("wBattleMonNativeSpecies") + 2] = (
            list((DITTO).to_bytes(2, "little"))
        )
        memory[addr("wEnemyMonNativeSpecies"):addr("wEnemyMonNativeSpecies") + 2] = (
            list((25).to_bytes(2, "little"))
        )
        memory[addr("wBattleMonSpecies")] = 150
        memory[addr("wEnemyMonSpecies")] = DITTO
        assert call_match(DITTO)
        count += 1
        assert not call_match(25)
        count += 1

        # Full-word comparison must reject a high-byte mismatch even when the
        # low byte matches Ditto.
        memory[addr("hBattleTurn")] = 0
        memory[addr("wEnemyMonNativeSpecies"):addr("wEnemyMonNativeSpecies") + 2] = (
            list(((1 << 8) | DITTO).to_bytes(2, "little"))
        )
        assert not call_match(DITTO)
        count += 1

        # Empty opponent identity is never Ditto.
        memory[addr("wEnemyMonNativeSpecies"):addr("wEnemyMonNativeSpecies") + 2] = [0, 0]
        memory[addr("wEnemyMonSpecies")] = DITTO
        assert not call_match(DITTO)
        count += 1

        # The inactive side must never be selected by mistake.
        memory[addr("hBattleTurn")] = 0
        memory[addr("wBattleMonNativeSpecies"):addr("wBattleMonNativeSpecies") + 2] = (
            list((DITTO).to_bytes(2, "little"))
        )
        memory[addr("wEnemyMonNativeSpecies"):addr("wEnemyMonNativeSpecies") + 2] = (
            list((59).to_bytes(2, "little"))
        )
        assert not call_match(DITTO)
        count += 1

        memory[addr("hBattleTurn")] = 1
        memory[addr("wBattleMonNativeSpecies"):addr("wBattleMonNativeSpecies") + 2] = (
            list((59).to_bytes(2, "little"))
        )
        memory[addr("wEnemyMonNativeSpecies"):addr("wEnemyMonNativeSpecies") + 2] = (
            list((DITTO).to_bytes(2, "little"))
        )
        assert not call_match(DITTO)
        count += 1

        print(
            f"PASS: {count} exact opponent native-identity cases; "
            "both battle turns, full-word matching, legacy disagreement, "
            "empty shadows and wrong-side guards"
        )
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
