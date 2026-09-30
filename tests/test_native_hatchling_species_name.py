"""Hatchling species-name lookup must preserve the extended native root."""
import argparse
from pathlib import Path

from pyboy import PyBoy


MON_NAME_LENGTH = 11
NAME_RECORD_LENGTH = MON_NAME_LENGTH - 1


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

    def rom_offset(name):
        bank, address = symbols[name]
        return bank * 0x4000 + address - (0x4000 if bank else 0)

    data = rom.read_bytes()
    records_start = rom_offset("PokemonNameRecords")
    records_end = rom_offset("PokemonNameRecords.IndirectEnd")
    num_records = (records_end - records_start) // NAME_RECORD_LENGTH
    assert num_records > 0
    assert (records_end - records_start) % NAME_RECORD_LENGTH == 0

    pyboy = PyBoy(
        str(rom),
        window="null",
        sound_emulated=False,
        cgb=True,
        log_level="ERROR",
    )
    mem, regs = pyboy.memory, pyboy.register_file

    def invoke():
        bank, target = symbols["GetPartyPokemonName"]
        assert bank == 0, bank

        mem[0x2000] = 1
        mem[addr("hROMBank")] = 1
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

        tested = 0
        extended_0101_name = None
        for native in range(1, num_records):
            species = native & 0xFF
            ext = (native >> 8) << 5

            for metadata in (0x00, 0x40, 0x80, 0xC0):
                mem[addr("wCurPartySpecies")] = species
                mem[addr("wCurForm")] = ext | metadata
                mem[addr("wNamedObjectIndex")] = 0xEE
                mem[addr("wNamedObjectIndex") + 1] = 0xEE
                mem[addr("wStringBuffer1"):addr("wStringBuffer1") + MON_NAME_LENGTH] = [0x55] * MON_NAME_LENGTH

                invoke()

                start = records_start + native * NAME_RECORD_LENGTH
                expected = data[start:start + NAME_RECORD_LENGTH]
                actual = bytes(
                    mem[addr("wStringBuffer1"):addr("wStringBuffer1") + NAME_RECORD_LENGTH]
                )

                assert actual == expected, (
                    hex(native),
                    metadata,
                    actual.hex(),
                    expected.hex(),
                )
                assert mem[addr("wNamedObjectIndex")] == species, (hex(native), metadata)
                assert mem[addr("wNamedObjectIndex") + 1] == (ext | metadata), (
                    hex(native),
                    metadata,
                )
                if native == 0x0101 and metadata == 0:
                    extended_0101_name = actual
                tested += 1

        # Explicit anti-alias proof: $0101 (Mismagius) must not use species $0001's name.
        assert extended_0101_name is not None
        one_start = records_start + NAME_RECORD_LENGTH
        assert extended_0101_name != data[one_start:one_start + NAME_RECORD_LENGTH]

        print(
            f"PASS: {tested} hatchling species-name cases across {num_records - 1} native roots; "
            "extended-root reconstruction, metadata tolerance, exact name records, "
            "and no low-byte aliasing"
        )
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
