"""CPU tests for the Silph Scope ghost reveal's native picture and Dex identity.

Renderer and Dex entry points are stubbed; only dispatch, identities,
register arguments, and restoration are tested, not displayed graphics.
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
        fields = line.split()
        if len(fields) == 2 and ":" in fields[0]:
            symbols[fields[1]] = tuple(int(v, 16) for v in fields[0].split(":"))

    def addr(name):
        return symbols[name][1]

    def offset(name):
        bank, address = symbols[name]
        return bank * 0x4000 + address - (0x4000 if bank else 0)

    data = rom.read_bytes()
    source = Path(__file__).resolve().parents[1]
    count_variants = sum(
        line.strip().startswith("native_variant_identity ")
        for line in (source / "data/pokemon/native_variant_name_roots.asm").read_text().splitlines()
    )
    variants = []
    start = offset("NativeVariantIdentityTable")
    for p in range(start, start + 5 * count_variants, 5):
        native = int.from_bytes(data[p:p + 2], "little")
        root = int.from_bytes(data[p + 2:p + 4], "little")
        variants.append((native, 0xFF, root & 255, data[p + 4] | ((root >> 8) << 5)))

    # Full native variant table plus extended root, cosmetic normalization,
    # and the two nonrenderable identities.
    cases = [
        (25, 0xE1, 25, 1),
        (257, 1, 1, 0x21),
        (201, 0xE2, 201, 2),
        (25, 3, 25, 3),
        (26, 2, 26, 1),
    ] + variants + [(0, 2, 92, 0x23), (256, 2, 92, 0x23)]

    pyboy = PyBoy(str(rom), window="null", sound_emulated=False, cgb=True, log_level="ERROR")
    mem, regs = pyboy.memory, pyboy.register_file
    pictures, seen = [], []
    initial = (91, 92, 0x23)

    def capture_picture(_):
        pictures.append((
            tuple(mem[addr(name)] for name in ("wCurSpecies", "wCurPartySpecies", "wCurForm")),
            (regs.D << 8) | regs.E,
        ))

    def capture_seen(_):
        seen.append((
            (regs.B << 8) | regs.C,
            tuple(mem[addr(name)] for name in ("wCurSpecies", "wCurPartySpecies", "wCurForm")),
        ))

    def invoke(name):
        bank, target = symbols[name]
        mem[0x2000] = bank
        mem[addr("hROMBank")] = bank
        mem[0xC100:0xC106] = [0xF3, 0xCD, target & 255, target >> 8, 0x18, 0xFE]
        regs.SP, regs.PC = 0xC0FF, 0xC100
        pyboy.tick(4, False, False)
        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF), (
            name, hex(regs.PC), hex(regs.SP)
        )
        assert mem[addr("hROMBank")] == bank
        assert mem[0xFF70] & 7 == 1

    tested = 0
    try:
        mem[0xFF50] = 1
        mem[0xFFFF] = mem[0xFF0F] = mem[0xFF40] = 0
        mem[0xFF70] = 1
        for name, callback in (("GetFrontpic", capture_picture), ("SetSeenMon", capture_seen)):
            bank, address = symbols[name]
            mem[bank, address] = 0xC9
            pyboy.hook_register(bank, address, callback, None)

        for turn in (0, 1):
            for native, raw, species, form in cases:
                mem[0xFF70] = 1
                mem[addr("hBattleTurn")] = turn
                shadow = addr("wEnemyMonNativeSpecies")
                mem[shadow:shadow + 2] = list(native.to_bytes(2, "little"))
                mem[addr("wEnemyMonSpecies")] = 59
                mem[addr("wEnemyMonForm")] = raw
                mem[addr("wTempEnemyMonSpecies")] = 72
                for name, value in zip(("wCurSpecies", "wCurPartySpecies", "wCurForm"), initial):
                    mem[addr(name)] = value
                pictures.clear()
                seen.clear()

                invoke("RevealGhostEnemyFrontpic")
                assert mem[addr("hBattleTurn")] == turn
                if native in (0, 256):
                    assert not pictures
                    assert tuple(mem[addr(n)] for n in (
                        "wCurSpecies", "wCurPartySpecies", "wCurForm"
                    )) == initial
                else:
                    assert pictures == [((91, species, form), 0x8000)], (
                        turn, native, raw, pictures, species, form
                    )

                # Simulate animation clobbering renderer presentation globals:
                # the Dex path must derive its identity from the enemy shadow.
                mem[addr("wCurPartySpecies")] = 92
                mem[addr("wCurForm")] = 0x23
                invoke("RecordRevealedGhostEnemySeen")
                assert mem[addr("hBattleTurn")] == turn
                assert mem[addr("wTempEnemyMonSpecies")] == 72
                assert mem[addr("wEnemyMonSpecies")] == 59
                assert mem[addr("wEnemyMonForm")] == raw
                if native in (0, 256):
                    assert not seen
                    assert (mem[addr("wCurPartySpecies")], mem[addr("wCurForm")]) == (92, 0x23)
                else:
                    assert seen == [((form << 8) | species, (91, species, form))], (
                        turn, native, raw, seen, species, form
                    )
                tested += 1

        print(f"PASS: {tested} native ghost-reveal picture and Dex CPU cases")
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
