"""Generic Egg frontpic never inherits hatchling form or extension bits."""
import argparse
from pathlib import Path
from pyboy import PyBoy


PLAIN_FORM = 1
EGG = 0xFF


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom", type=Path)
    rom = ap.parse_args().rom

    syms = {}
    for line in rom.with_suffix(".sym").read_text().splitlines():
        fields = line.split()
        if len(fields) == 2 and ":" in fields[0]:
            syms[fields[1]] = tuple(int(v, 16) for v in fields[0].split(":"))

    def addr(symbol):
        return syms[symbol][1]

    data = rom.read_bytes()
    bank, at = syms["BaseDataRecords"]
    base_start = bank * 0x4000 + at - 0x4000
    base_size = addr("wCurBaseDataEnd") - addr("wCurBaseData")
    expected_base = data[
        base_start + (EGG - 1) * base_size:
        base_start + EGG * base_size
    ]

    pyboy = PyBoy(
        str(rom),
        window="null",
        sound_emulated=False,
        cgb=True,
        log_level="ERROR",
    )
    mem, regs = pyboy.memory, pyboy.register_file

    def put(symbol, value):
        mem[addr(symbol)] = value

    def word(symbol, value):
        mem[addr(symbol):addr(symbol) + 2] = list(value.to_bytes(2, "little"))

    captures = []

    try:
        mem[0xFF50] = 1
        mem[0xFFFF] = 0
        mem[0xFF0F] = 0
        mem[0xFF40] = 0
        mem[0xFF70] = 1

        # Stop at the generic renderer entry. GetEggFrontpic's own base-data
        # lookup and bank/stack behavior still execute for real.
        front_bank, front_at = syms["GetFrontpic"]
        mem[front_bank, front_at] = 0xC9

        def capture(_):
            captures.append(
                (
                    mem[addr("wCurSpecies")],
                    mem[addr("wCurPartySpecies")],
                    mem[addr("wCurForm")],
                    regs.D << 8 | regs.E,
                )
            )

        pyboy.hook_register(front_bank, front_at, capture, None)

        start = addr("wPartyMon1Species")
        stride = addr("wPartyMon2Species") - start
        form_offset = addr("wPartyMon1Form") - start
        count = 0

        # Include a clean form, an extension-bit form that used to alias Egg
        # to $01ff, and upper metadata bits. Format markers are varied because
        # the generic Egg renderer must be independent of persistent encoding.
        for marker in (0, 0x16BC, 0x00BC, 0x1600):
            for raw_form in (PLAIN_FORM, 0x21, 0xC1, 0xE1):
                for slot in range(6):
                    context = (marker, raw_form, slot)
                    word("wPokemonDataFormat", marker)
                    mem[start:start + 6 * stride] = [0xA5] * (6 * stride)
                    record = start + slot * stride
                    mem[record] = 7
                    mem[record + form_offset] = raw_form

                    put("wCurPartyMon", slot)
                    put("wPartyCount", 6)
                    put("wCurSpecies", 91)
                    put("wCurPartySpecies", 92)
                    put("wCurForm", 3)
                    before = bytes(mem[start:start + 6 * stride])
                    previous = len(captures)

                    bank, target = syms["GetEggFrontpic"]
                    mem[0x2000] = bank
                    put("hROMBank", bank)
                    mem[0xC100:0xC106] = [
                        0xF3,
                        0xCD,
                        target & 0xFF,
                        target >> 8,
                        0x18,
                        0xFE,
                    ]
                    regs.D = 0x80
                    regs.E = 0x00
                    regs.SP = 0xC0FF
                    regs.PC = 0xC100
                    pyboy.tick(4, False, False)

                    assert (regs.PC, regs.SP) == (0xC104, 0xC0FF), (
                        context,
                        hex(regs.PC),
                        hex(regs.SP),
                    )
                    assert len(captures) == previous + 1, context
                    assert captures[-1] == (EGG, EGG, PLAIN_FORM, 0x8000), (
                        context,
                        captures[-1],
                    )
                    assert bytes(
                        mem[addr("wCurBaseData"):addr("wCurBaseDataEnd")]
                    ) == expected_base, context
                    assert bytes(mem[start:start + 6 * stride]) == before, context
                    count += 1

        print(
            f"PASS: {count} generic Egg frontpic identity cases; "
            "legacy/native/partial markers, all six party slots, extension and "
            "metadata form bits ignored, exact Egg base data, unchanged party records"
        )
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
