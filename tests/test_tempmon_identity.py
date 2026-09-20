"""CPU regression test for the player/opponent temporary-Pokemon boundary.

Usage: python tests/test_tempmon_identity.py polishedcrystal-3.2.3.gbc
Requires PyBoy 2.7.0 and a matching RGBDS .sym file. No game save is used.
"""
import argparse
from pathlib import Path

from pyboy import PyBoy


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    args = parser.parse_args()
    symbols = {}
    for line in args.rom.with_suffix(".sym").read_text().splitlines():
        fields = line.split()
        if len(fields) == 2 and ":" in fields[0]:
            symbols[fields[1]] = tuple(int(x, 16) for x in fields[0].split(":"))

    def addr(name):
        return symbols[name][1]

    rom = args.rom.read_bytes()
    bank, address = symbols["NativeVariantIdentityTable"]
    offset = bank * 0x4000 + address - 0x4000
    alolan_raichu = None
    for pos in range(offset, offset + 5 * 100, 5):
        native = int.from_bytes(rom[pos:pos + 2], "little")
        root = int.from_bytes(rom[pos + 2:pos + 4], "little")
        if root == 26 and rom[pos + 4] == 2:
            alolan_raichu = native
            break
    assert alolan_raichu is not None
    cases = [(25, 25, 1), (256, 0, 0x21), (alolan_raichu, 26, 2)]
    emulator = PyBoy(str(args.rom), window="null", sound_emulated=False,
                     cgb=True, log_level="ERROR")
    memory, regs = emulator.memory, emulator.register_file
    try:
        memory[0xFF50] = 1
        memory[0xFFFF] = memory[0xFF0F] = memory[0xFF40] = 0
        stride = addr("wPartyMon2Species") - addr("wPartyMon1Species")
        form_offset = addr("wPartyMon1Form") - addr("wPartyMon1Species")
        destination = addr("wTempMonSpecies")
        bank, target = symbols["CopyPkmnToTempMon"]
        # DI; CALL target; JR to itself. Execute the real base-data lookup too.
        memory[0xC100:0xC106] = [0xF3, 0xCD, target & 255, target >> 8, 0x18, 0xFE]
        count = 0
        for marker in (0, 0x16BC, 0x00BC, 0x1600):
            for enemy in (False, True):
                for native, root, form in cases:
                    for slot in range(6):
                        for metadata in (0, 0x40, 0x80, 0xC0):
                            transient = marker == 0x16BC and not enemy
                            memory[0xFF70] = 1
                            memory[addr("wPokemonDataFormat"):addr("wPokemonDataFormat") + 2] = list(marker.to_bytes(2, "little"))
                            party = addr("wOTPartyMon1Species" if enemy else "wPartyMon1Species")
                            source = party + slot * stride
                            original = [(i * 7 + 3) & 255 for i in range(stride)]
                            original[0] = 7 if transient else root
                            original[form_offset] = form | metadata
                            memory[source:source + stride] = original
                            memory[destination:destination + stride] = [0xA5] * stride
                            memory[addr("wCurPartyMon")] = slot
                            memory[addr("wMonType")] = int(enemy)  # PARTYMON/OTPARTYMON
                            memory[0xFF70] = 2
                            entries = addr("wPokemonIndexTableEntries")
                            # Legacy root bytes deliberately resolve to the wrong
                            # identity if an opponent is accidentally decoded.
                            memory[entries:entries + 200] = [1, 0] * 100
                            entry = entries + 2 * (7 - 1)
                            memory[entry:entry + 2] = list(native.to_bytes(2, "little"))
                            memory[0xFF70] = 1
                            memory[0x2000] = bank
                            memory[addr("hROMBank")] = bank
                            regs.SP, regs.PC = 0xC0FF, 0xC100
                            emulator.tick(1, False, False)
                            context = (hex(marker), enemy, native, slot, hex(metadata))
                            assert regs.PC == 0xC104, (context, hex(regs.PC))
                            expected = original.copy()
                            expected[0] = root
                            assert memory[destination:destination + stride] == expected, context
                            assert memory[source:source + stride] == original, context
                            assert memory[addr("wCurSpecies")] == root, context
                            assert memory[addr("wCurPartySpecies")] == root, context
                            assert memory[addr("wCurForm")] == form, context
                            assert regs.SP == 0xC0FF, context
                            assert memory[addr("hROMBank")] == bank, context
                            assert memory[0xFF70] & 7 == 1, context
                            count += 1
        print(f"PASS: {count} full temporary-record copies; both party types, valid/absent/partial format markers, six slots, extended and variant identities, gender/Egg flags, source and stack/bank preservation")
    finally:
        emulator.stop(save=False)


if __name__ == "__main__":
    main()
