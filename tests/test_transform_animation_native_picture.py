"""Exercise Transform animation's native picture identity and renderer dispatch.

The front/back renderers are stubbed: these CPU tests verify identity,
bank/global restoration, and call parameters, not decompression or visuals.
"""
import argparse
from pathlib import Path

from pyboy import PyBoy


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    rom = parser.parse_args().rom
    symbols = {}
    for line in rom.with_suffix(".sym").read_text().splitlines():
        parts = line.split()
        if len(parts) == 2 and ":" in parts[0]:
            symbols[parts[1]] = tuple(int(v, 16) for v in parts[0].split(":"))

    def address(name):
        return symbols[name][1]

    def offset(name):
        bank, addr = symbols[name]
        return bank * 0x4000 + addr - (0x4000 if bank else 0)

    data = rom.read_bytes()
    source = Path(__file__).resolve().parents[1]
    variant_count = sum(
        line.strip().startswith("native_variant_identity ")
        for line in (source / "data/pokemon/native_variant_name_roots.asm").read_text().splitlines()
    )
    variant_start = offset("NativeVariantIdentityTable")
    variants = []
    for pos in range(variant_start, variant_start + variant_count * 5, 5):
        native = int.from_bytes(data[pos:pos + 2], "little")
        root = int.from_bytes(data[pos + 2:pos + 4], "little")
        form = data[pos + 4]
        variants.append((native, 0xFF, root & 255, form | ((root >> 8) << 5)))

    # Root-form normalization, extended root, and every native mechanical form.
    cases = [
        (25, 0xE1, 25, 1),
        (257, 1, 1, 0x21),
        (201, 0xE2, 201, 2),
        (25, 3, 25, 3),
        (26, 2, 26, 1),
    ] + variants + [
        (0, 2, 92, 0x23),
        (256, 2, 92, 0x23),
    ]

    pyboy = PyBoy(str(rom), window="null", sound_emulated=False, cgb=True, log_level="ERROR")
    mem, regs = pyboy.memory, pyboy.register_file
    rendered = []
    initial = (91, 92, 0x23)

    def capture(which):
        rendered.append((
            which,
            tuple(mem[address(n)] for n in ("wCurSpecies", "wCurPartySpecies", "wCurForm")),
            regs.D * 256 + regs.E,
        ))

    def call_transform():
        bank, target = symbols["BattleAnimCmd_Transform"]
        mem[0x2000] = bank
        mem[address("hROMBank")] = bank
        mem[0xC100:0xC106] = [0xF3, 0xCD, target & 255, target >> 8, 0x18, 0xFE]
        regs.SP, regs.PC = 0xC0FF, 0xC100
        pyboy.tick(4, False, False)
        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF), (hex(regs.PC), hex(regs.SP))
        assert mem[address("hROMBank")] == bank
        assert mem[0xFF70] & 7 == 1

    tested = 0
    try:
        mem[0xFF50] = 1
        mem[0xFFFF] = mem[0xFF0F] = mem[0xFF40] = 0
        mem[0xFF70] = 1
        for name in ("GetFrontpic", "GetBackpic"):
            bank, target = symbols[name]
            mem[bank, target] = 0xC9  # RET: capture identity at renderer boundary
            pyboy.hook_register(bank, target, capture, name)

        for side in ("Player", "Enemy"):
            for native, raw, species, form in cases:
                for turn in (0, 1) if native in (25, 257, 0, 256) else (0 if side == "Player" else 1,):
                    mem[0xFF70] = 1
                    mem[address("hBattleTurn")] = turn
                    for prefix, value in (
                        ("wBattle", native if side == "Player" else 143),
                        ("wEnemy", native if side == "Enemy" else 143),
                    ):
                        at = address(prefix + "MonNativeSpecies")
                        mem[at:at + 2] = list(value.to_bytes(2, "little"))
                        mem[address(prefix + "MonSpecies")] = 59
                        mem[address(prefix + "MonForm")] = raw if value == native else 1

                    # These outdated entry-time species bytes must never
                    # decide which image Transform draws.
                    mem[address("wTempBattleMonSpecies")] = 71
                    mem[address("wTempEnemyMonSpecies")] = 72
                    for name, value in zip(("wCurSpecies", "wCurPartySpecies", "wCurForm"), initial):
                        mem[address(name)] = value
                    rendered.clear()
                    call_transform()
                    assert mem[address("hBattleTurn")] == turn
                    assert mem[address("wCurSpecies")] == initial[0]
                    assert mem[address("wCurPartySpecies")] == initial[1]
                    assert (mem[address("wTempBattleMonSpecies")],
                            mem[address("wTempEnemyMonSpecies")]) == (71, 72)
                    if native in (0, 256):
                        assert not rendered, (side, native, rendered)
                        assert mem[address("wCurForm")] == initial[2]
                    else:
                        expected = "GetBackpic" if side == "Player" else "GetFrontpic"
                        assert rendered == [(expected, (91, species, form), 0x8000)], (
                            side, native, turn, rendered, expected, species, form
                        )
                        # Like the original command, the transformed form
                        # remains current after party species is restored.
                        assert mem[address("wCurForm")] == form
                    tested += 1

        print(f"PASS: {tested} native Transform-animation picture CPU cases")
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
