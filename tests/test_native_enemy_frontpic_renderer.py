"""CPU regression for the battle-only native enemy frontpic preparation path.

Low-level decompression/copy calls are stubbed. This checks that the real
frontpic pointer/size preparation keeps native base data intact, and that
non-battle picture preparation retains its existing legacy lookup.
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

    def addr(name):
        return symbols[name][1]

    def offset(name):
        bank, address = symbols[name]
        return bank * 0x4000 + address - (0x4000 if bank else 0)

    data = rom.read_bytes()
    root = Path(__file__).resolve().parents[1]
    nvariants = sum(
        line.strip().startswith("native_variant_identity ")
        for line in (root / "data/pokemon/native_variant_name_roots.asm").read_text().splitlines()
    )
    table = offset("NativeVariantIdentityTable")
    variants = []
    for p in range(table, table + 5 * nvariants, 5):
        native = int.from_bytes(data[p:p + 2], "little")
        species = int.from_bytes(data[p + 2:p + 4], "little")
        form = data[p + 4]
        variants.append((native, 0xFF, species & 255, form | ((species >> 8) << 5)))

    cases = [(25, 0xE1, 25, 1), (257, 1, 1, 0x21),
             (201, 0xE2, 201, 2), (25, 3, 25, 3),
             (26, 2, 26, 1)] + variants + [
                 (0, 2, 92, 0x23), (256, 2, 92, 0x23)
             ]

    pyboy = PyBoy(str(rom), window="null", sound_emulated=False, cgb=True, log_level="ERROR")
    mem, regs = pyboy.memory, pyboy.register_file
    base_start, base_end = addr("wCurBaseData"), addr("wCurBaseDataEnd")
    base_size = base_end - base_start
    native_entry, animated_entry, legacy_calls = [], [], []

    def capture_native(_):
        native_entry.append((
            tuple(mem[addr(n)] for n in ("wCurSpecies", "wCurPartySpecies", "wCurForm")),
            list(mem[base_start:base_end]),
        ))

    def capture_animated(_):
        animated_entry.append((
            tuple(mem[addr(n)] for n in ("wCurSpecies", "wCurPartySpecies", "wCurForm")),
            list(mem[base_start:base_end]),
        ))

    def call(name):
        bank, target = symbols[name]
        mem[0x2000] = bank
        mem[addr("hROMBank")] = bank
        mem[0xC100:0xC106] = [0xF3, 0xCD, target & 255, target >> 8, 0x18, 0xFE]
        regs.SP, regs.PC = 0xC0FF, 0xC100
        regs.D, regs.E = 0x90, 0x00  # vTiles2, as at the battle call site
        pyboy.tick(4, False, False)
        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF), (
            name, hex(regs.PC), hex(regs.SP)
        )
        assert mem[addr("hROMBank")] == bank, name
        assert mem[0xFF70] & 7 == 1, name

    def stub(name, callback=None):
        bank, address = symbols[name]
        mem[bank, address] = 0xC9  # RET
        if callback is not None:
            pyboy.hook_register(bank, address, callback, None)

    count = 0
    try:
        mem[0xFF50] = 1
        mem[0xFFFF] = mem[0xFF0F] = mem[0xFF40] = 0
        mem[0xFF70] = 1
        stub("GetBaseData", lambda _: legacy_calls.append(True))
        stub("FarDecompressInB")
        stub("PadFrontpic")
        stub("Get2bpp")
        bank, address = symbols["_GetNativeFrontpic"]
        pyboy.hook_register(bank, address, capture_native, None)  # Observe real routine.
        stub("GetAnimatedFrontpic", capture_animated)

        for turn in (0, 1):
            for native, raw, species, form in cases:
                mem[0xFF70] = 1
                mem[addr("hBattleTurn")] = turn
                shadow = addr("wEnemyMonNativeSpecies")
                mem[shadow:shadow + 2] = list(native.to_bytes(2, "little"))
                other = addr("wBattleMonNativeSpecies")
                mem[other:other + 2] = [143, 0]
                mem[addr("wEnemyMonSpecies")] = 59
                mem[addr("wEnemyMonForm")] = raw
                mem[addr("wTempEnemyMonSpecies")] = 72
                for name, value in zip(
                    ("wCurSpecies", "wCurPartySpecies", "wCurForm"), (91, 92, 0x23)
                ):
                    mem[addr(name)] = value
                mem[base_start:base_end] = [0xA5] * base_size
                native_entry.clear()
                animated_entry.clear()
                legacy_calls.clear()

                call("PrepareNativeEnemyBattleAnimatedFrontpic")

                context = (turn, native, raw)
                assert not legacy_calls, context
                if native in (0, 256):
                    assert not native_entry and not animated_entry, context
                    assert tuple(mem[addr(n)] for n in (
                        "wCurSpecies", "wCurPartySpecies", "wCurForm"
                    )) == (91, 92, 0x23), context
                    assert list(mem[base_start:base_end]) == [0xA5] * base_size, context
                else:
                    expected_base = list(data[
                        offset("BaseDataRecords") + (native - 1) * base_size:
                        offset("BaseDataRecords") + native * base_size
                    ])
                    expected = ((species, species, form), expected_base)
                    assert native_entry == [expected], (context, native_entry, expected)
                    assert animated_entry == [expected], (context, animated_entry, expected)
                    assert list(mem[base_start:base_end]) == expected_base, context
                    assert mem[addr("wEnemyMonSpecies")] == 59, context
                    assert mem[addr("wEnemyMonForm")] == raw, context
                    assert mem[addr("wTempEnemyMonSpecies")] == 72, context
                count += 1

        # General-purpose picture calls must still perform the legacy lookup.
        mem[0xFF70] = 1
        mem[addr("wCurPartySpecies")] = 25
        mem[addr("wCurSpecies")] = 91
        mem[addr("wCurForm")] = 1
        mem[base_start:base_end] = [0xA5] * base_size
        native_entry.clear()
        animated_entry.clear()
        legacy_calls.clear()
        call("PrepareAnimatedFrontpic")
        assert legacy_calls == [True], legacy_calls
        assert not native_entry
        assert animated_entry == [((25, 25, 1), [0xA5] * base_size)]
        count += 1

        print(f"PASS: {count} native enemy frontpic and generic renderer CPU cases")
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
