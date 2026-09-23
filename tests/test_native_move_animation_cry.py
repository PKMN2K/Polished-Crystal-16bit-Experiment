"""Native active-species selection for move-animation cries (audio playback stubbed)."""
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
            symbols[fields[1]] = tuple(int(x, 16) for x in fields[0].split(":"))

    def addr(name):
        return symbols[name][1]

    def offset(name):
        bank, address = symbols[name]
        return bank * 0x4000 + address - (0x4000 if bank else 0)

    data = rom.read_bytes()
    root = Path(__file__).resolve().parents[1]
    count_variants = sum(
        line.strip().startswith("native_variant_identity ")
        for line in (root / "data/pokemon/native_variant_name_roots.asm").read_text().splitlines()
    )
    start = offset("NativeVariantIdentityTable")
    variants = [
        (int.from_bytes(data[p:p + 2], "little"),
         int.from_bytes(data[p + 2:p + 4], "little"))
        for p in range(start, start + 5 * count_variants, 5)
    ]
    roots = variants[0][0] - 1
    cases = [(n, n) for n in range(roots + 1)] + variants
    deltas = [(0, 0xC0), (0, 0x40), (0, 0), (0, 0)]

    pyboy = PyBoy(str(rom), window="null", sound_emulated=False, cgb=True, log_level="ERROR")
    mem, regs = pyboy.memory, pyboy.register_file
    cries, waits = [], []

    def word(name):
        a = addr(name)
        return mem[a] + 256 * mem[a + 1]

    def capture(_):
        cries.append((regs.D * 256 + regs.E, word("wCryPitch"), word("wCryLength")))

    def run():
        bank, target = symbols["BattleAnimCmd_Cry"]
        mem[0x2000] = bank
        mem[addr("hROMBank")] = bank
        mem[0xC100:0xC106] = [0xF3, 0xCD, target & 255, target >> 8, 0x18, 0xFE]
        regs.SP, regs.PC = 0xC0FF, 0xC100
        pyboy.tick(4, False, False)
        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF)
        assert mem[addr("hROMBank")] == bank
        assert mem[0xFF70] & 7 == 1

    tested = 0
    try:
        mem[0xFF50] = 1
        mem[0xFFFF] = mem[0xFF0F] = mem[0xFF40] = 0
        mem[0xFF70] = 1
        for name in ("_PlayCry", "WaitSFX"):
            bank, address = symbols[name]
            mem[bank, address] = 0xC9
        bank, address = symbols["_PlayCry"]
        pyboy.hook_register(bank, address, capture, None)
        bank, address = symbols["WaitSFX"]
        pyboy.hook_register(bank, address, lambda _: waits.append(True), None)

        # Use the actual GetBattleAnimByte reader with a temporary ROM script
        # byte at an unused-by-this-test entry point after the cry data table.
        script_bank, script_addr = symbols["PlayHitSound"]
        for turn in (0, 1):
            for native, species in cases:
                for prefix, identity in (
                    ("wBattle", native if turn == 0 else 143),
                    ("wEnemy", native if turn == 1 else 143),
                ):
                    location = addr(prefix + "MonNativeSpecies")
                    mem[location:location + 2] = list(identity.to_bytes(2, "little"))
                    mem[addr(prefix + "MonSpecies")] = 59
                    mem[addr(prefix + "MonForm")] = 0x21
                mem[addr("hBattleTurn")] = turn
                for parameter, (pitch_delta, length_delta) in enumerate(deltas):
                    mem[0xFF70] = 1
                    mem[script_bank, script_addr] = 0xFC | parameter
                    mem[addr("wBattleAnimAddress"):addr("wBattleAnimAddress") + 2] = [
                        script_addr & 255, script_addr >> 8
                    ]
                    mem[addr("wCurSpecies")] = 91
                    mem[addr("wCurForm")] = 0x23
                    mem[addr("wCryTracks")] = 0x55
                    mem[addr("wStereoPanningMask")] = 0x6A
                    mem[addr("wCryPitch"):addr("wCryPitch") + 2] = [0x34, 0x12]
                    mem[addr("wCryLength"):addr("wCryLength") + 2] = [0x78, 0x56]
                    cries.clear()
                    waits.clear()
                    run()
                    assert word("wBattleAnimAddress") == script_addr + 1
                    assert mem[addr("wCryTracks")] == (0xF0 if turn == 0 else 0x0F)
                    assert not waits
                    if species in (0, 255, 256):
                        assert not cries
                        assert (word("wCryPitch"), word("wCryLength")) == (0x1234, 0x5678)
                        assert mem[addr("wStereoPanningMask")] == 0x6A
                    else:
                        p = offset("PokemonCryData") + (species - 1) * 5
                        pitch = int.from_bytes(data[p + 1:p + 3], "little")
                        length = int.from_bytes(data[p + 3:p + 5], "little")
                        expected = (data[p], (pitch + pitch_delta) & 65535,
                                    (length + length_delta) & 65535)
                        assert cries == [expected], (turn, native, parameter, cries, expected)
                        assert mem[addr("wStereoPanningMask")] == 1
                    assert mem[addr("hBattleTurn")] == turn
                    assert (mem[addr("wCurSpecies")], mem[addr("wCurForm")]) == (91, 0x23)
                    tested += 1
        print(f"PASS: {tested} native move-animation cry CPU cases")
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
