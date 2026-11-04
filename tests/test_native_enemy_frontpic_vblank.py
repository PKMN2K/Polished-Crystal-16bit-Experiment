"""LCD-on native enemy frontpic Request2bpp/VBlank regression.

Run the real enemy-native frontpic preparation with the LCD enabled. A tiny
test-only ROM0 redirect makes each Get2bpp call wait until LY >= $88 before
entering the real Request2bpp routine, forcing its scheduled VBlank copy path.
The LZ decoder, padding, Request2bpp, VBlank Serve2bppRequest and VRAM writes
remain real. Compare native battle output with the generic presentation path.
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
    nvariants = sum(
        line.strip().startswith("native_variant_identity ")
        for line in (root / "data/pokemon/native_variant_name_roots.asm").read_text().splitlines()
    )
    table = offset("NativeVariantIdentityTable")
    variants = []
    for p in range(table, table + 5 * nvariants, 5):
        native = int.from_bytes(data[p:p + 2], "little")
        species = int.from_bytes(data[p + 2:p + 4], "little")
        variants.append((native, 0xFF, species & 0xFF,
                         data[p + 4] | ((species >> 8) << 5)))
    assert len(variants) >= 2, "Need at least two regional variants"

    cases = [
        (25, 0xE1, 25, 1),
        (257, 1, 1, 0x21),
        (201, 0xE2, 201, 2),
        (25, 3, 25, 3),
        (26, 2, 26, 1),
    ] + variants[:2]

    pyboy = PyBoy(str(rom), window="null", sound_emulated=False,
                  cgb=True, log_level="ERROR")
    mem, regs = pyboy.memory, pyboy.register_file
    base_start, base_end = address("wCurBaseData"), address("wCurBaseDataEnd")
    base_len = base_end - base_start
    v0_start = address("vTiles2")
    v0_end = v0_start + 7 * 7 * 16
    v1_start = address("vTiles4")
    v1_end = address("vBGMap2")
    v1_base_offset = address("vTiles5") - v1_start

    lookups = []
    decompressions = []
    requests = []
    serves = []

    def set_hram(label, value):
        mem[address(label)] = value

    def setup(turn, native, raw, presentation=None):
        # LCD off while the fixture clears VRAM; invoke() enables it.
        mem[0xFF40] = 0
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
        identity = ((91, 92, 0x23) if presentation is None
                    else (presentation[0], presentation[0], presentation[1]))
        for label, value in zip(("wCurSpecies", "wCurPartySpecies", "wCurForm"),
                                identity):
            mem[address(label)] = value
        mem[address("wBoxAlignment")] = 0
        mem[base_start:base_end] = [0xA5] * base_len
        mem[address("wMonPicSize")] = 0
        mem[address("wMonAnimationSize")] = 0

        mem[0xFF4F] = 0
        mem[v0_start:v0_end] = [0x5A] * (v0_end - v0_start)
        mem[0xFF4F] = 1
        mem[v1_start:v1_end] = [0x5A] * (v1_end - v1_start)
        mem[0xFF4F] = 0

        # Minimal stable VBlank environment. hCrashCode skips the normal
        # "executing from RAM" diagnostic because this test uses a RAM
        # trampoline intentionally.
        set_hram("hVBlank", 6)
        set_hram("hCrashCode", 1)
        set_hram("hBGMapMode", 0)
        set_hram("hMapAnims", 0)
        set_hram("hOAMUpdate", 0)
        set_hram("hCGBPalUpdate", 0)
        set_hram("hDMATransfer", 0)
        set_hram("hRequested1bpp", 0)
        set_hram("hRequested2bpp", 0)
        set_hram("hVBlankOccurred", 1)
        mem[0xFFFF] = 0x01  # VBlank interrupt
        mem[0xFF0F] = 0

        lookups.clear()
        decompressions.clear()
        requests.clear()
        serves.clear()

    def invoke(entry):
        bank, target = symbols[entry]
        mem[0x2000] = bank
        mem[address("hROMBank")] = bank

        # EI; NOP; CALL target; DI; JR -2. Interrupts are needed for the
        # real DelayFrame/VBlank service; they are disabled again on return.
        mem[0xC100:0xC108] = [
            0xFB, 0x00, 0xCD, target & 0xFF, target >> 8,
            0xF3, 0x18, 0xFE,
        ]
        regs.SP, regs.PC = 0xC0FF, 0xC100
        regs.D, regs.E = 0x90, 0x00
        mem[0xFF40] = 0x91  # LCD on, BG on

        # Each late Request2bpp can consume multiple frames. Continue until
        # the target returns to the DI/infinite-loop tail.
        for _ in range(96):
            pyboy.tick(1, False, False)
            if (regs.PC, regs.SP) == (0xC106, 0xC0FF):
                break
        assert (regs.PC, regs.SP) == (0xC106, 0xC0FF), (
            entry, hex(regs.PC), hex(regs.SP), mem[0xFF44],
            mem[address("hRequested2bpp")],
        )
        assert mem[address("hROMBank")] == bank, entry
        assert mem[0xFF70] & 7 == 1, entry
        assert mem[0xFF4F] & 1 == 0, entry

    def snapshot():
        # LCD off makes both VRAM banks safely readable after the scheduled
        # transfer has completed.
        mem[0xFF40] = 0
        old_vbk = mem[0xFF4F] & 1
        mem[0xFF4F] = 0
        front = bytes(mem[v0_start:v0_end])
        mem[0xFF4F] = 1
        animated = bytes(mem[v1_start:v1_end])
        mem[0xFF4F] = old_vbk
        return (front, animated, mem[address("wMonPicSize")],
                mem[address("wMonAnimationSize")])

    try:
        mem[0xFF50] = 1
        mem[0xFF40] = 0
        mem[0xFF70] = 1
        mem[0xFF4F] = 0

        # Force Get2bpp's LCD-on dispatch to enter Request2bpp late in the
        # visible frame. The wrapper waits on real LY, then jumps to the real
        # Request2bpp. No decoder/copy routine is stubbed.
        get2_bank, get2 = symbols["Get2bpp"]
        assert get2_bank == 0
        req_bank, req = symbols["Request2bpp"]
        assert req_bank == 0
        mem[get2_bank, get2] = 0xC3
        mem[get2_bank, get2 + 1] = 0x00
        mem[get2_bank, get2 + 2] = 0xC2
        # C200: LDH A,[rLY]; CP $88; JR C,C200; JP Request2bpp
        mem[0xC200:0xC209] = [
            0xF0, 0x44, 0xFE, 0x88, 0x38, 0xFA,
            0xC3, req & 0xFF, req >> 8,
        ]

        for name, callback in (
            ("GetBaseData", lambda _: lookups.append(True)),
            ("FarDecompressInB", lambda _: decompressions.append(True)),
            ("Request2bpp", lambda _: requests.append((
                mem[0xFF44], regs.C, regs.HL, mem[0xFF4F] & 1,
            ))),
            ("Serve2bppRequest", lambda _: serves.append((
                mem[0xFF44], mem[address("hRequested2bpp")],
                mem[0xFF4F] & 1,
            ))),
        ):
            hook_bank, hook_addr = symbols[name]
            pyboy.hook_register(hook_bank, hook_addr, callback, None)

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
                assert decompressions, ("decoder did not execute", context)
                assert len(requests) >= 2, ("Request2bpp missing", context, requests)
                assert all(event[0] >= 0x88 for event in requests), (
                    "late-scanline redirect failed", context, requests
                )
                assert any(pending for _, pending, _ in serves), (
                    "VBlank never served a pending 2bpp request", context, serves
                )
                assert bytes(mem[base_start:base_end]) == expected_base, context
                assert (mem[address("wCurSpecies")],
                        mem[address("wCurPartySpecies")],
                        mem[address("wCurForm")]) == (species, species, form), context
                assert actual[0] != bytes([0x5A] * len(actual[0])), context
                base_anim = actual[1][
                    v1_base_offset:v1_base_offset + len(actual[0])
                ]
                assert base_anim != bytes([0x5A] * len(base_anim)), context

                native_request_count = len(requests)
                native_served = sum(1 for _, pending, _ in serves if pending)

                setup(turn, 143, 0xFF, (species, form))
                invoke("PrepareAnimatedFrontpic")
                generic = snapshot()
                assert len(lookups) == 1, ("generic lost legacy lookup", context)
                assert len(requests) >= 2, context
                assert any(pending for _, pending, _ in serves), context
                assert actual == generic, (
                    "LCD-on native/generic VRAM or dimensions differ",
                    context,
                    hashlib.sha256(actual[0] + actual[1]).hexdigest(),
                    hashlib.sha256(generic[0] + generic[1]).hexdigest(),
                    actual[2:], generic[2:],
                    native_request_count, native_served,
                )
                digests.append(
                    hashlib.sha256(actual[0] + actual[1]).hexdigest()[:12]
                )
                executed += 1

        print(
            f"PASS: {executed} LCD-on native/generic Request2bpp/VBlank "
            f"frontpic cases; frame digests {', '.join(digests[:4])}"
        )
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
