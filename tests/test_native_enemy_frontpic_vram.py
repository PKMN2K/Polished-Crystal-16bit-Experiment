"""Unstubbed native enemy frontpic decompression and VRAM-transfer CPU regression.

Execute the real LZ decoder, padding, base-frame and animation tile transfers
with the LCD disabled (direct 2bpp copy). Compare the native battle-only route
against the generic route for the *same* resolved presentation identity.
This is an offscreen VRAM-byte test, not a screenshot or gameplay test.
"""
import argparse
import hashlib
from pathlib import Path

from pyboy import PyBoy


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom", type=Path)
    rom = ap.parse_args().rom
    symbols = {}
    for line in rom.with_suffix(".sym").read_text().splitlines():
        fields = line.split()
        if len(fields) == 2 and ":" in fields[0]:
            symbols[fields[1]] = tuple(int(v, 16) for v in fields[0].split(":"))

    def address(label):
        return symbols[label][1]

    def offset(label):
        bank, addr = symbols[label]
        return bank * 0x4000 + addr - (0x4000 if bank else 0)

    data = rom.read_bytes()
    root = Path(__file__).resolve().parents[1]
    count_variants = sum(
        line.strip().startswith("native_variant_identity ")
        for line in (root / "data/pokemon/native_variant_name_roots.asm").read_text().splitlines()
    )
    table = offset("NativeVariantIdentityTable")
    variants = []
    for p in range(table, table + 5 * count_variants, 5):
        native = int.from_bytes(data[p:p + 2], "little")
        species = int.from_bytes(data[p + 2:p + 4], "little")
        variants.append((native, 0xFF, species & 255, data[p + 4] | ((species >> 8) << 5)))
    assert len(variants) >= 2, "Need at least two regional variants"
    cases = [
        (25, 0xE1, 25, 1),       # plain root, stale high form bits
        (257, 1, 1, 0x21),       # root over $00ff
        (201, 0xE2, 201, 2),    # existing cosmetic overlay
        (25, 3, 25, 3),         # another cosmetic overlay
        (26, 2, 26, 1),         # invalid cosmetic form normalizes
    ] + variants[:2]

    pyboy = PyBoy(str(rom), window="null", sound_emulated=False, cgb=True, log_level="ERROR")
    mem, regs = pyboy.memory, pyboy.register_file
    base_start, base_end = address("wCurBaseData"), address("wCurBaseDataEnd")
    base_len = base_end - base_start
    v0_start = address("vTiles2")
    v0_end = v0_start + 7 * 7 * 16
    v1_start = address("vTiles3")
    v1_end = address("vTiles5")  # vTiles3 and vTiles4, including extra animation frames
    lookups, decompressions, transfers = [], [], []

    def setup(turn, native, raw, presentation=None):
        mem[0xFF70] = 1
        mem[0xFF4F] = 0
        mem[address("hBattleTurn")] = turn
        enemy = address("wEnemyMonNativeSpecies")
        mem[enemy:enemy + 2] = list(native.to_bytes(2, "little"))
        player = address("wBattleMonNativeSpecies")
        mem[player:player + 2] = [143, 0]
        mem[address("wEnemyMonSpecies")] = 59
        mem[address("wEnemyMonForm")] = raw
        mem[address("wTempEnemyMonSpecies")] = 72
        for label, value in zip(
            ("wCurSpecies", "wCurPartySpecies", "wCurForm"),
            (91, 92, 0x23) if presentation is None
            else (presentation[0], presentation[0], presentation[1]),
        ):
            mem[address(label)] = value
        mem[address("wBoxAlignment")] = 0
        mem[base_start:base_end] = [0xA5] * base_len
        mem[address("wMonPicSize")] = 0
        mem[address("wMonAnimationSize")] = 0
        # Address each VRAM bank explicitly. PyBoy's banked memory view
        # avoids ambiguity with the hardware VBK value at capture time.
        mem[0, v0_start:v0_end] = [0x5A] * (v0_end - v0_start)
        mem[1, v1_start:v1_end] = [0x5A] * (v1_end - v1_start)
        lookups.clear()
        decompressions.clear()
        transfers.clear()

    def invoke(entry):
        bank, target = symbols[entry]
        mem[0x2000] = bank
        mem[address("hROMBank")] = bank
        mem[0xC100:0xC106] = [0xF3, 0xCD, target & 255, target >> 8, 0x18, 0xFE]
        regs.SP, regs.PC = 0xC0FF, 0xC100
        regs.D, regs.E = 0x90, 0x00  # vTiles2
        pyboy.tick(4, False, False)
        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF), (
            entry, hex(regs.PC), hex(regs.SP)
        )
        assert mem[address("hROMBank")] == bank, entry
        assert mem[0xFF70] & 7 == 1, entry
        assert mem[0xFF4F] & 1 == 0, entry

    def snapshot():
        front = bytes(mem[0, v0_start:v0_end])
        animated = bytes(mem[1, v1_start:v1_end])
        return (front, animated, mem[address("wMonPicSize")],
                mem[address("wMonAnimationSize")])

    try:
        mem[0xFF50] = 1
        mem[0xFFFF] = mem[0xFF0F] = mem[0xFF40] = 0
        mem[0xFF70] = 1
        mem[0xFF4F] = 0
        # These hooks observe the REAL routines; no ROM opcodes are replaced.
        for name, target in (
            ("GetBaseData", lookups),
            ("FarDecompressInB", decompressions),
            ("Get2bpp", transfers),
        ):
            bank, addr = symbols[name]
            if name == "Get2bpp":
                pyboy.hook_register(
                    bank, addr,
                    lambda _: transfers.append((
                        regs.HL, (regs.D << 8) | regs.E, regs.C,
                        mem[0xFF4F] & 1, mem[0xFF70] & 7,
                    )),
                    None,
                )
            else:
                pyboy.hook_register(bank, addr, lambda _, dest=target: dest.append(True), None)

        executed = 0
        digests = []
        for turn in (0, 1):
            for native, raw, species, form in cases:
                context = (turn, native, raw)
                expected_base = bytes(data[
                    offset("BaseDataRecords") + (native - 1) * base_len:
                    offset("BaseDataRecords") + native * base_len
                ])
                setup(turn, native, raw)
                invoke("PrepareNativeEnemyBattleAnimatedFrontpic")
                actual = snapshot()
                assert not lookups, ("battle used legacy base lookup", context)
                assert decompressions and len(transfers) >= 2, (
                    "decoder or VRAM transfer not executed", context,
                    len(decompressions), len(transfers)
                )
                assert bytes(mem[base_start:base_end]) == expected_base, context
                assert (mem[address("wCurSpecies")], mem[address("wCurPartySpecies")],
                        mem[address("wCurForm")]) == (species, species, form), context
                assert mem[address("wEnemyMonSpecies")] == 59, context
                assert mem[address("wEnemyMonForm")] == raw, context
                assert mem[address("wTempEnemyMonSpecies")] == 72, context
                assert actual[0] != bytes([0x5A] * len(actual[0])), (
                    "no frontpic bytes copied", context
                )
                assert actual[1][:len(actual[0])] != bytes([0x5A] * len(actual[0])), (
                    "no animated base tiles copied", context,
                    "transfers (dest,src,count,vbk,wbk)", transfers,
                    "base frame sha", hashlib.sha256(actual[0]).hexdigest()[:16],
                    "vbk1 first bytes", list(actual[1][:32]),
                )

                # The generic renderer must produce identical REAL tile bytes
                # for the equivalent visual species/form without using the
                # (intentionally conflicting) native enemy battle shadow.
                setup(turn, 143, 0xFF, (species, form))
                invoke("PrepareAnimatedFrontpic")
                generic = snapshot()
                assert len(lookups) == 1, ("generic lost legacy lookup", context)
                assert decompressions and len(transfers) >= 2, context
                assert actual == generic, (
                    "native/generic VRAM bytes or dimensions differ",
                    context,
                    hashlib.sha256(actual[0] + actual[1]).hexdigest(),
                    hashlib.sha256(generic[0] + generic[1]).hexdigest(),
                    actual[2:], generic[2:],
                )
                digests.append(hashlib.sha256(actual[0] + actual[1]).hexdigest()[:12])
                executed += 1

        # An empty or reserved shadow must not call the decoder or touch VRAM.
        for native in (0, 256):
            setup(1, native, 2)
            before = snapshot()
            invoke("PrepareNativeEnemyBattleAnimatedFrontpic")
            assert snapshot() == before, ("invalid identity drew", native)
            assert not lookups and not decompressions and not transfers, native
            assert bytes(mem[base_start:base_end]) == bytes([0xA5] * base_len), native
            assert (mem[address("wCurSpecies")], mem[address("wCurPartySpecies")],
                    mem[address("wCurForm")]) == (91, 92, 0x23), native
            executed += 1

        print(
            f"PASS: {executed} real native/generic frontpic decoder and "
            f"VRAM-transfer CPU cases; frame digests {', '.join(digests[:4])}"
        )
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
