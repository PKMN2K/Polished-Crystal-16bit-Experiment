"""CPU regression for enemy send-out temporary-record native base-data lookup.

The legacy GetBaseData entry is stubbed to prove it is bypassed when an
active native enemy identity is present. This tests the send-out preparation
helper, not full on-screen send-out animation.
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
    variant_count = sum(
        line.strip().startswith("native_variant_identity ")
        for line in (root / "data/pokemon/native_variant_name_roots.asm").read_text().splitlines()
    )
    start = offset("NativeVariantIdentityTable")
    variants = [
        int.from_bytes(data[pos:pos + 2], "little")
        for pos in range(start, start + 5 * variant_count, 5)
    ]
    native_cases = [25, 257] + variants[:3] + [0]

    pyboy = PyBoy(str(rom), window="null", sound_emulated=False, cgb=True, log_level="ERROR")
    mem, regs = pyboy.memory, pyboy.register_file
    stride = addr("wPartyMon2Species") - addr("wPartyMon1Species")
    form_offset = addr("wOTPartyMon1Form") - addr("wOTPartyMon1Species")
    base_start, base_end = addr("wCurBaseData"), addr("wCurBaseDataEnd")
    base_size = base_end - base_start
    get_base_calls = []

    def call_native_copy():
        bank, target = symbols["CopyEnemyBattlePkmnToTempMon"]
        mem[0x2000] = bank
        mem[addr("hROMBank")] = bank
        mem[0xC100:0xC106] = [0xF3, 0xCD, target & 255, target >> 8, 0x18, 0xFE]
        regs.SP, regs.PC = 0xC0FF, 0xC100
        pyboy.tick(4, False, False)
        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF), (
            hex(regs.PC), hex(regs.SP)
        )
        assert mem[addr("hROMBank")] == bank
        assert mem[0xFF70] & 7 == 1

    tested = 0
    try:
        mem[0xFF50] = 1
        mem[0xFFFF] = mem[0xFF0F] = mem[0xFF40] = 0
        mem[0xFF70] = 1
        bank, target = symbols["GetBaseData"]
        mem[bank, target] = 0xC9
        pyboy.hook_register(bank, target, lambda _: get_base_calls.append(True), None)

        for marker in (0, 0x16BC):
            for turn in (0, 1):
                for slot in (0, 2, 5):
                    for native in native_cases:
                        mem[0xFF70] = 1
                        mem[addr("wPokemonDataFormat"):addr("wPokemonDataFormat") + 2] = (
                            list(marker.to_bytes(2, "little"))
                        )
                        mem[addr("hBattleTurn")] = turn
                        mem[addr("wCurPartyMon")] = slot
                        mem[addr("wMonType")] = 1  # OTPARTYMON
                        mem[addr("wEnemyMonSpecies")] = 151
                        mem[addr("wEnemyMonForm")] = 0x23
                        mem[addr("wBattleMonNativeSpecies"):addr("wBattleMonNativeSpecies") + 2] = [143, 0]
                        mem[addr("wEnemyMonNativeSpecies"):addr("wEnemyMonNativeSpecies") + 2] = (
                            list(native.to_bytes(2, "little"))
                        )
                        mem[addr("wCurSpecies")] = 91
                        mem[addr("wCurPartySpecies")] = 92
                        mem[addr("wCurForm")] = 0x23
                        source = addr("wOTPartyMon1Species") + slot * stride
                        original = [(i * 13 + slot * 11 + 7) & 255 for i in range(stride)]
                        original[0] = 59
                        original[form_offset] = 0xC1  # form 1 + gender/Egg metadata
                        mem[source:source + stride] = original
                        temp = addr("wTempMonSpecies")
                        mem[temp:temp + stride] = [0xA5] * stride
                        mem[base_start:base_end] = [0xA5] * base_size
                        get_base_calls.clear()

                        call_native_copy()

                        context = (hex(marker), turn, slot, native)
                        assert list(mem[temp:temp + stride]) == original, context
                        assert list(mem[source:source + stride]) == original, context
                        assert (
                            mem[addr("wCurSpecies")],
                            mem[addr("wCurPartySpecies")],
                            mem[addr("wCurForm")],
                        ) == (59, 59, 1), context
                        assert mem[addr("wEnemyMonSpecies")] == 151, context
                        assert mem[addr("wEnemyMonForm")] == 0x23, context
                        if native:
                            expect = list(data[
                                offset("BaseDataRecords") + (native - 1) * base_size:
                                offset("BaseDataRecords") + native * base_size
                            ])
                            assert list(mem[base_start:base_end]) == expect, context
                            assert not get_base_calls, context
                        else:
                            # Empty native shadow uses the prior legacy path;
                            # GetBaseData is stubbed, so base buffer is unchanged.
                            assert get_base_calls == [True], context
                            assert list(mem[base_start:base_end]) == [0xA5] * base_size, context
                        tested += 1

        print(f"PASS: {tested} native enemy send-out temporary-record CPU cases")
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
