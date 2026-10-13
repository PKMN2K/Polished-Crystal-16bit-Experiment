"""Real animation substitution uses bank-aware active native species lists."""
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

    def addr(label):
        return syms[label][1]

    data = rom.read_bytes()

    def read_list(label):
        bank, address = syms[label]
        pos = bank * 0x4000 + address - 0x4000
        members = set()
        while int.from_bytes(data[pos:pos + 2], "little"):
            members.add(int.from_bytes(data[pos:pos + 2], "little"))
            pos += 2
        return members

    milk = read_list("CheckBattleAnimSubstitution.MilkDrinkUsers")
    fury = read_list("FuryAttackUsers")
    withdraw = read_list("WithdrawUsers")
    harden = read_list("HardenUsers")
    cases = sorted(milk | fury | withdraw | harden | {0, 25, 256, 257, 0x1207, 0xFFFF})
    # Move IDs and substituted animation IDs from constants/move_constants.asm.
    FRESH_SNACK, FURY_STRIKES, DEFENSE_CURL = 0x87, 0x9A, 0x6F
    MILK_DRINK, FURY_ATTACK, WITHDRAW, HARDEN = 0x101, 0x100, 0x102, 0x103
    moves = (FRESH_SNACK, FURY_STRIKES, DEFENSE_CURL, 33, 0x180)
    pyboy = PyBoy(str(rom), window="null", sound_emulated=False,
                  cgb=True, log_level="ERROR")
    mem, regs = pyboy.memory, pyboy.register_file

    def write_word(label, word):
        mem[addr(label):addr(label) + 2] = list(word.to_bytes(2, "little"))

    def invoke():
        bank, target = syms["CheckBattleAnimSubstitution"]
        mem[0x2000] = bank
        mem[addr("hROMBank")] = bank
        mem[0xC100:0xC106] = [0xF3, 0xCD, target & 255, target >> 8, 0x18, 0xFE]
        regs.SP, regs.PC = 0xC0FF, 0xC100
        pyboy.tick(2, False, False)
        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF)
        assert mem[addr("hROMBank")] == bank
        assert mem[0xFF70] & 7 == 1

    try:
        mem[0xFF50] = 1
        mem[0xFFFF] = mem[0xFF0F] = mem[0xFF40] = 0
        mem[0xFF70] = 1
        count = 0
        protected = ("wBattleMonNativeSpecies", "wEnemyMonNativeSpecies",
                     "wBattleMonSpecies", "wEnemyMonSpecies",
                     "wBattleMonForm", "wEnemyMonForm", "hBattleTurn")
        for side, active, other in (
            (0, "wBattleMonNativeSpecies", "wEnemyMonNativeSpecies"),
            (1, "wEnemyMonNativeSpecies", "wBattleMonNativeSpecies"),
        ):
            for native in cases:
                for move in moves:
                    context = (side, hex(native), hex(move))
                    write_word(active, native)
                    # The opposite side is a matching species: nonmembers
                    # prove the matcher selects the current move user.
                    inactive = 241 if move == FRESH_SNACK else 15 if move == FURY_STRIKES else 7
                    write_word(other, inactive)
                    for label in ("wBattleMonSpecies", "wEnemyMonSpecies"):
                        mem[addr(label)] = inactive
                    for label in ("wBattleMonForm", "wEnemyMonForm"):
                        mem[addr(label)] = 0xA1
                    mem[addr("hBattleTurn")] = side
                    mem[addr("wFXAnimIDLo")] = move & 255
                    mem[addr("wFXAnimIDHi")] = move >> 8
                    before = [(label, bytes(mem[addr(label):addr(label) + (2 if "Native" in label else 1)]))
                              for label in protected]
                    expected = move
                    if move == FRESH_SNACK and native in milk:
                        expected = MILK_DRINK
                    elif move == FURY_STRIKES and native in fury:
                        expected = FURY_ATTACK
                    elif move == DEFENSE_CURL:
                        if native in harden:
                            expected = HARDEN
                        elif native in withdraw:
                            expected = WITHDRAW
                    invoke()
                    actual = mem[addr("wFXAnimIDLo")] | (mem[addr("wFXAnimIDHi")] << 8)
                    assert actual == expected, (context, hex(actual), hex(expected))
                    for label, value in before:
                        assert bytes(mem[addr(label):addr(label) + len(value)]) == value, (context, label)
                    count += 1
        print(f"PASS: {count} real native animation-substitution cases; Fresh Snack, "
              "Fury Strikes and Defense Curl select both-side ROM species lists, "
              "ignore conflicting legacy/opponent identities, preserve battle state, "
              "and leave unrelated/16-bit animation IDs unchanged")
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
