"""CPU regression for explicit native enemy front-picture animation sizing.

The real animation setup and native base-data lookup execute. Sprite tick
and GetPicSize are stubbed to validate dispatch, identity, bank restoration,
base-data side effects and dimension storage, not rendered animation pixels.
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
    nvariants = sum(
        line.strip().startswith("native_variant_identity ")
        for line in (source / "data/pokemon/native_variant_name_roots.asm").read_text().splitlines()
    )
    start = offset("NativeVariantIdentityTable")
    variants = [
        (
            int.from_bytes(data[p:p + 2], "little"),
            0xFF,
            int.from_bytes(data[p + 2:p + 4], "little") & 0xFF,
            data[p + 4] | ((data[p + 3] & 1) << 5),
        )
        for p in range(start, start + 5 * nvariants, 5)
    ]
    cases = [(25, 0xE1, 25, 1), (257, 1, 1, 0x21),
             (201, 0xE2, 201, 2), (25, 3, 25, 3),
             (26, 2, 26, 1)] + variants + [
                 (0, 2, 92, 0x23), (256, 2, 92, 0x23)
             ]

    pyboy = PyBoy(str(rom), window="null", sound_emulated=False, cgb=True, log_level="ERROR")
    mem, regs = pyboy.memory, pyboy.register_file
    base_start, base_end = addr("wCurBaseData"), addr("wCurBaseDataEnd")
    base_size = base_end - base_start
    anim_bank = symbols["wPokeAnimStruct"][0] & 7
    legacy_calls, dims, ticks = [], [], []

    def read_anim(name):
        old_bank = mem[0xFF70]
        mem[0xFF70] = anim_bank
        try:
            return mem[addr(name)]
        finally:
            mem[0xFF70] = old_bank

    def capture_size(_):
        assert mem[0xFF70] & 7 == 1, "GetPicSize must read bank 1"
        dims.append((
            tuple(mem[addr(n)] for n in ("wCurSpecies", "wCurPartySpecies", "wCurForm")),
            list(mem[base_start:base_end]),
        ))
        regs.A = 6  # Return an unmistakable frontpic height.

    def call(name, anim=9):
        bank, target = symbols[name]
        mem[0x2000] = bank
        mem[addr("hROMBank")] = bank
        mem[0xC100:0xC106] = [0xF3, 0xCD, target & 255, target >> 8, 0x18, 0xFE]
        regs.HL = 0xC800
        regs.D, regs.E = 0, anim
        regs.SP, regs.PC = 0xC0FF, 0xC100
        pyboy.tick(4, False, False)
        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF), (
            name, hex(regs.PC), hex(regs.SP)
        )
        assert mem[addr("hROMBank")] == bank, name
        assert mem[0xFF70] & 7 == 1, name

    def prepare(native, raw, turn):
        mem[0xFF70] = 1
        mem[addr("hBattleTurn")] = turn
        shadow = addr("wEnemyMonNativeSpecies")
        mem[shadow:shadow + 2] = list(native.to_bytes(2, "little"))
        other = addr("wBattleMonNativeSpecies")
        mem[other:other + 2] = [143, 0]
        mem[addr("wEnemyMonSpecies")] = 59
        mem[addr("wEnemyMonForm")] = raw
        for name, value in zip(
            ("wCurSpecies", "wCurPartySpecies", "wCurForm"), (91, 92, 0x23)
        ):
            mem[addr(name)] = value
        mem[base_start:base_end] = [0xA5] * base_size
        mem[0xFF70] = anim_bank
        mem[addr("wPokeAnimFrontpicHeight")] = 0xA5
        mem[0xFF70] = 1
        legacy_calls.clear()
        dims.clear()
        ticks.clear()

    count = 0
    try:
        mem[0xFF50] = 1
        mem[0xFFFF] = mem[0xFF0F] = mem[0xFF40] = 0
        mem[0xFF70] = 1

        for name, callback in (
            ("GetBaseData", lambda _: legacy_calls.append(True)),
            ("GetPicSize", capture_size),
            ("TickPokeAnim", lambda _: ticks.append(True)),
        ):
            bank, address = symbols[name]
            mem[bank, address] = 0xC9
            pyboy.hook_register(bank, address, callback, None)
        bank, address = symbols["TickPokeAnim"]
        mem[bank, address:address + 2] = [0x37, 0xC9]  # SCF; RET: one animation tick.

        for turn in (0, 1):
            for native, raw, species, form in cases:
                prepare(native, raw, turn)
                call("AnimateNativeEnemyBattleFrontpic")
                context = (turn, native, raw)
                assert not legacy_calls, context
                assert (
                    mem[addr("wCurPartySpecies")], mem[addr("wCurForm")]
                ) == (92, 0x23), context
                assert mem[addr("hBattleTurn")] == turn, context
                assert mem[addr("wEnemyMonSpecies")] == 59, context
                assert mem[addr("wEnemyMonForm")] == raw, context
                if native in (0, 256):
                    assert not dims and not ticks, context
                    assert read_anim("wPokeAnimFrontpicHeight") == 0xA5, context
                    assert list(mem[base_start:base_end]) == [0xA5] * base_size, context
                else:
                    expected_base = list(data[
                        offset("BaseDataRecords") + (native - 1) * base_size:
                        offset("BaseDataRecords") + native * base_size
                    ])
                    assert dims == [((species, species, form), expected_base)], (
                        context, dims
                    )
                    assert ticks == [True], context
                    assert read_anim("wPokeAnimFrontpicHeight") == 6, context
                    assert list(mem[base_start:base_end]) == expected_base, context
                    assert read_anim("wPokeAnimSpecies") == species, context
                    assert read_anim("wPokeAnimVariant") == form, context
                count += 1

        # The old entry is not battle-scoped, even with the enemy turn and
        # native shadow populated: it must retain the legacy base-data call.
        for turn in (0, 1):
            prepare(257, 1, turn)
            mem[addr("wCurPartySpecies")] = 25
            mem[addr("wCurForm")] = 1
            call("AnimateFrontpic", anim=2)  # Non-battle menu animation.
            assert legacy_calls == [True], (turn, legacy_calls)
            assert dims == [((25, 25, 1), [0xA5] * base_size)], (turn, dims)
            assert ticks == [True], turn
            assert read_anim("wPokeAnimFrontpicHeight") == 6, turn
            assert list(mem[base_start:base_end]) == [0xA5] * base_size, turn
            count += 1

        print(f"PASS: {count} native enemy and generic frontpic animation-dimension CPU cases")
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
