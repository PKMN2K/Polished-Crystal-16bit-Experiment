"""Hatchling stat refresh must decode native party identity before base-data/stat calculation."""
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

    variant_count = sum(
        line.strip().startswith("native_variant_identity ")
        for line in (source / "data/pokemon/native_variant_name_roots.asm").read_text().splitlines()
    )
    variant_start = offset("NativeVariantIdentityTable")
    variants = []
    for p in range(variant_start, variant_start + 5 * variant_count, 5):
        native = int.from_bytes(data[p:p + 2], "little")
        root = int.from_bytes(data[p + 2:p + 4], "little")
        form = data[p + 4]
        variants.append((native, root, form))

    sample_variants = []
    if variants:
        for i in sorted({0, len(variants) // 2, len(variants) - 1}):
            sample_variants.append(variants[i])

    cases = [
        (25, 25, 1),
        (257, 257, 1),
    ] + sample_variants

    base_size = addr("wCurBaseDataEnd") - addr("wCurBaseData")
    base_start = offset("BaseDataRecords")

    pyboy = PyBoy(
        str(rom),
        window="null",
        sound_emulated=False,
        cgb=True,
        log_level="ERROR",
    )
    mem, regs = pyboy.memory, pyboy.register_file

    party_start = addr("wPartyMon1Species")
    party_stride = addr("wPartyMon2Species") - party_start
    form_offset = addr("wPartyMon1Form") - party_start
    level_offset = addr("wPartyMon1Level") - party_start
    hp_offset = addr("wPartyMon1HP") - party_start
    maxhp_offset = addr("wPartyMon1MaxHP") - party_start

    captures = []

    def capture_calc(_):
        captures.append((
            mem[addr("wCurSpecies")],
            mem[addr("wCurPartySpecies")],
            mem[addr("wCurForm")],
            bytes(mem[addr("wCurBaseData"):addr("wCurBaseDataEnd")]),
            (regs.D << 8) | regs.E,
        ))

    def invoke_update():
        bank, target = symbols["UpdatePkmnStats"]
        mem[0x2000] = bank
        mem[addr("hROMBank")] = bank
        mem[0xC100:0xC106] = [
            0xF3,
            0xCD,
            target & 0xFF,
            target >> 8,
            0x18,
            0xFE,
        ]
        regs.SP = 0xC0FF
        regs.PC = 0xC100
        pyboy.tick(4, False, False)
        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF), (
            hex(regs.PC),
            hex(regs.SP),
        )

    try:
        mem[0xFF50] = 1
        mem[0xFFFF] = 0
        mem[0xFF0F] = 0
        mem[0xFF40] = 0
        mem[0xFF70] = 1

        calc_bank, calc_addr = symbols["CalcPkmnStats"]
        mem[calc_bank, calc_addr] = 0xC9
        pyboy.hook_register(calc_bank, calc_addr, capture_calc, None)

        tested = 0
        for native, root, mechanical_form in cases:
            for slot in range(6):
                for metadata in (0x00, 0x40, 0x80, 0xC0):
                    # Native-format party storage: the authoritative full ID lives
                    # in the transient table; legacy species/form bytes are allowed
                    # to disagree and must not drive the hatch stat refresh.
                    mem[addr("wPokemonDataFormat"):addr("wPokemonDataFormat") + 2] = [0xBC, 0x16]
                    mem[0xFF70] = 2
                    index_entry = addr("wPokemonIndexTableEntries") + 12
                    mem[index_entry:index_entry + 2] = list(native.to_bytes(2, "little"))
                    mem[0xFF70] = 1

                    mem[party_start:party_start + 6 * party_stride] = [0] * (6 * party_stride)
                    record = party_start + slot * party_stride
                    mem[record] = 7
                    mem[record + form_offset] = 1 | metadata
                    mem[record + level_offset] = 5
                    mem[record + hp_offset:record + hp_offset + 2] = [0, 20]
                    mem[record + maxhp_offset:record + maxhp_offset + 2] = [0, 20]

                    mem[addr("wCurPartyMon")] = slot
                    mem[addr("wPartyCount")] = 6
                    mem[addr("wCurSpecies")] = 91
                    mem[addr("wCurPartySpecies")] = 92
                    mem[addr("wCurForm")] = 3

                    captures.clear()
                    invoke_update()

                    expected_form = mechanical_form | ((root >> 8) << 5)
                    expected_base = data[
                        base_start + (native - 1) * base_size:
                        base_start + native * base_size
                    ]
                    expected_de = record + maxhp_offset

                    assert captures == [(
                        root & 0xFF,
                        root & 0xFF,
                        expected_form,
                        expected_base,
                        expected_de,
                    )], (
                        native,
                        root,
                        mechanical_form,
                        slot,
                        metadata,
                        captures,
                    )

                    # The stubbed calculator leaves max HP unchanged, so the real
                    # post-calculation HP adjustment should also leave current HP
                    # unchanged. This proves the routine returned cleanly through
                    # its normal hatch-time path.
                    assert bytes(mem[record + hp_offset:record + hp_offset + 2]) == bytes([0, 20])
                    assert bytes(mem[record + maxhp_offset:record + maxhp_offset + 2]) == bytes([0, 20])
                    tested += 1

        print(
            f"PASS: {tested} native hatchling stat-refresh cases; six party slots, "
            "ordinary/extended roots, representative mechanical variants, metadata, "
            "exact native base data, stat destination, and clean HP post-processing"
        )
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
