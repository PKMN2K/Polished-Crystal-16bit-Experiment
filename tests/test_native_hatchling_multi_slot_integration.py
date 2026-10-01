"""Integrated multi-slot HatchEggs regression for native transient party identities."""
import argparse
from pathlib import Path

from pyboy import PyBoy


LEVEL = 5
DV = 15
HATCHED_HAPPINESS = 120
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

    def offset(name):
        bank, address = symbols[name]
        return bank * 0x4000 + address - (0x4000 if bank else 0)

    data = rom.read_bytes()
    base_size = addr("wCurBaseDataEnd") - addr("wCurBaseData")
    base_start = offset("BaseDataRecords")
    name_start = offset("PokemonNameRecords")

    pyboy = PyBoy(
        str(rom),
        window="null",
        sound_emulated=False,
        cgb=True,
        log_level="ERROR",
    )
    mem, regs = pyboy.memory, pyboy.register_file

    party = addr("wPartyMon1Species")
    stride = addr("wPartyMon2Species") - party
    form_offset = addr("wPartyMon1Form") - party
    happiness_offset = addr("wPartyMon1Happiness") - party
    id_offset = addr("wPartyMon1ID") - party
    level_offset = addr("wPartyMon1Level") - party
    status_offset = addr("wPartyMon1Status") - party
    hp_offset = addr("wPartyMon1HP") - party
    maxhp_offset = addr("wPartyMon1MaxHP") - party
    ev_offset = addr("wPartyMon1EVs") - party
    dv_offset = addr("wPartyMon1DVs") - party
    nature_offset = addr("wPartyMon1Nature") - party
    nicknames = addr("wPartyMon1Nickname")

    def expected_stats(native):
        start = base_start + (native - 1) * base_size
        base = list(data[start:start + 6])
        out = []
        for i, stat in enumerate(base):
            value = ((2 * (stat + DV) + 1) * LEVEL) // 100
            value += LEVEL + 10 if i == 0 else 5
            out.append(value)
        return out

    def read_words(start, count):
        return [
            (mem[start + i * 2] << 8) | mem[start + i * 2 + 1]
            for i in range(count)
        ]

    def call_home(name, b=0, c=0):
        bank, target = symbols[name]
        assert bank == 0, (name, bank)
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
        regs.B = b
        regs.C = c
        regs.SP = 0xC0FF
        regs.PC = 0xC100
        pyboy.tick(4, False, False)
        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF), (
            name,
            hex(regs.PC),
            hex(regs.SP),
        )
        return bool(regs.F & 0x80)

    def invoke_hatch():
        bank, target = symbols["HatchEggs"]
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

    def seed_mapping(transient_id, native):
        mem[0xFF70] = 2
        entry = addr("wPokemonIndexTableEntries") + (transient_id - 1) * 2
        mem[entry:entry + 2] = list(native.to_bytes(2, "little"))
        mem[0xFF70] = 1

    def seed_record(slot, transient_id, egg, happiness):
        record = party + slot * stride
        mem[record:record + stride] = [0] * stride
        mem[record] = transient_id
        mem[record + form_offset] = 0x81 | (0x40 if egg else 0)
        mem[record + happiness_offset] = happiness
        mem[record + level_offset] = LEVEL
        mem[record + ev_offset:record + ev_offset + 6] = [0] * 6
        mem[record + dv_offset:record + dv_offset + 3] = [0xFF] * 3
        mem[record + nature_offset] = 0
        mem[record + status_offset:record + status_offset + 2] = [0xA5, 0x5A]
        mem[record + hp_offset:record + hp_offset + 2] = [0, 20]
        mem[record + maxhp_offset:record + maxhp_offset + 12] = [0] * 12
        mem[record + maxhp_offset:record + maxhp_offset + 2] = [0, 20]
        mem[
            nicknames + slot * MON_NAME_LENGTH:
            nicknames + (slot + 1) * MON_NAME_LENGTH
        ] = [0x55] * MON_NAME_LENGTH
        return record

    try:
        mem[0xFF50] = 1
        mem[0xFFFF] = 0
        mem[0xFF0F] = 0
        mem[0xFF40] = 0
        mem[0xFF70] = 1

        # Keep the actual hatch mutation real and bypass only text/UI work.
        print_bank, print_addr = symbols["PrintText"]
        mem[print_bank, print_addr] = 0xC9

        mem[
            addr("wPokemonDataFormat"):addr("wPokemonDataFormat") + 2
        ] = [0xBC, 0x16]
        mem[addr("wPokedexFlags"):addr("wEndPokedexFlags")] = [0] * (
            addr("wEndPokedexFlags") - addr("wPokedexFlags")
        )
        mem[addr("wTempMon"):addr("wTempMon") + stride] = [0] * stride

        # Ready Egg, normal mon, ready extended Egg, not-ready Egg.
        layout = [
            # slot, transient, native, root, decoded form, egg, happiness
            (0, 7, 0x0019, 25, 0x01, True, 0),
            (1, 8, 0x0006, 6, 0x01, False, 50),
            (2, 9, 0x0101, 1, 0x21, True, 0),
            (3, 10, 0x0085, 133, 0x01, True, 5),
        ]

        records = {}
        for slot, transient, native, root, decoded_form, egg, happiness in layout:
            seed_mapping(transient, native)
            records[slot] = seed_record(slot, transient, egg, happiness)

        untouched = {
            slot: (
                bytes(mem[records[slot]:records[slot] + stride]),
                bytes(
                    mem[
                        nicknames + slot * MON_NAME_LENGTH:
                        nicknames + (slot + 1) * MON_NAME_LENGTH
                    ]
                ),
            )
            for slot in (1, 3)
        }

        mem[addr("wPartyCount")] = 4
        mem[addr("wCurPartyMon")] = 3
        mem[addr("wPlayerID"):addr("wPlayerID") + 2] = [0x12, 0x34]
        mem[addr("wInitialOptions")] = 0
        mem[addr("wInitialOptions2")] = 0
        mem[addr("wOptions3")] = 0xFF
        mem[addr("wDexCacheValid")] = 1
        mem[addr("wCurSpecies")] = 91
        mem[addr("wCurPartySpecies")] = 92
        mem[addr("wCurForm")] = 3

        invoke_hatch()

        for slot, transient, native, root, decoded_form, egg, happiness in (
            layout[0],
            layout[2],
        ):
            record = records[slot]
            assert mem[record] == transient, (slot, "transient id changed")
            assert mem[record + happiness_offset] == HATCHED_HAPPINESS, slot
            assert not (mem[record + form_offset] & 0x40), slot
            assert mem[record + form_offset] & 0x80, slot
            assert bytes(
                mem[record + id_offset:record + id_offset + 2]
            ) == bytes([0x12, 0x34]), slot
            assert bytes(
                mem[record + status_offset:record + status_offset + 2]
            ) == bytes([0, 0]), slot

            stats = expected_stats(native)
            actual_stats = read_words(record + maxhp_offset, 6)
            assert actual_stats == stats, (slot, native, actual_stats, stats)
            hp = (mem[record + hp_offset] << 8) | mem[record + hp_offset + 1]
            assert hp == stats[0], (slot, hp, stats[0])

            name_expected = data[
                name_start + native * NAME_RECORD_LENGTH:
                name_start + (native + 1) * NAME_RECORD_LENGTH
            ]
            nickname = bytes(
                mem[
                    nicknames + slot * MON_NAME_LENGTH:
                    nicknames + slot * MON_NAME_LENGTH + NAME_RECORD_LENGTH
                ]
            )
            assert nickname == name_expected, (
                slot,
                native,
                nickname.hex(),
                name_expected.hex(),
            )

            assert not call_home(
                "CheckCaughtMon", decoded_form, root & 0xFF
            ), ("caught", slot, native)
            assert not call_home(
                "CheckSeenMon", decoded_form, root & 0xFF
            ), ("seen", slot, native)

        # The intervening normal Pokémon and the not-ready Egg stay untouched.
        for slot in (1, 3):
            before_record, before_name = untouched[slot]
            assert bytes(
                mem[records[slot]:records[slot] + stride]
            ) == before_record, slot
            assert bytes(
                mem[
                    nicknames + slot * MON_NAME_LENGTH:
                    nicknames + (slot + 1) * MON_NAME_LENGTH
                ]
            ) == before_name, slot

        # $0101 remains distinct from $0001. Skipped members do not acquire Dex flags.
        assert call_home("CheckCaughtMon", 0x01, 0x01), "extended caught alias"
        assert call_home("CheckSeenMon", 0x01, 0x01), "extended seen alias"
        assert call_home("CheckCaughtMon", 0x01, 0x06), "normal mon registered"
        assert call_home("CheckCaughtMon", 0x01, 0x85), "not-ready Egg registered"

        # Slot 2 was the last completed hatch; slot 3 was visited but skipped.
        assert mem[addr("wTempMonSpecies")] == 1
        assert mem[addr("wTempMonForm")] & 0x3F == 0x21
        assert mem[addr("wCurPartyMon")] == 3
        assert mem[addr("wDexCacheValid")] == 0

        ext_base = data[
            base_start + (0x0101 - 1) * base_size:
            base_start + 0x0101 * base_size
        ]
        assert bytes(
            mem[addr("wCurBaseData"):addr("wCurBaseDataEnd")]
        ) == ext_base

        print(
            "PASS: one real HatchEggs pass over four slots hatched ordinary+$0101 "
            "without cross-slot identity bleed; normal mon and not-ready Egg stayed untouched"
        )
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
