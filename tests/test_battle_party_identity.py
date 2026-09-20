"""Execute the player-party battle decoder in a built ROM using PyBoy.

Usage: python tests/test_battle_party_identity.py polishedcrystal-3.2.3.gbc
Requires PyBoy (tested with 2.7.0) and the matching RGBDS .sym file.
This is an isolated CPU regression test, not a gameplay/save compatibility test.
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

    # Read the native ID from the ROM identity table rather than assuming the
    # mechanical variants retain their current ordering.
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
    # Include an extended root and a mechanical variant, plus an ordinary root.
    cases = [(25, 25, 1), (256, 0, 0x21), (alolan_raichu, 26, 2)]
    emulator = PyBoy(str(args.rom), window="null", sound_emulated=False,
                     cgb=True, log_level="ERROR")
    memory, regs = emulator.memory, emulator.register_file
    try:
        memory[0xFF50] = 1  # Disable boot ROM; invoke only the routine under test.
        memory[0xFFFF] = memory[0xFF0F] = memory[0xFF40] = 0
        party_start = addr("wPartyMon1Species")
        stride = addr("wPartyMon2Species") - party_start
        form_offset = addr("wPartyMon1Form") - party_start
        battle_start = addr("wBattleMonSpecies")
        battle_end = addr("wBattleMonType1")
        bank, target = symbols["SendInUserPkmn.decode_player_identity"]
        # DI; CALL target; JR to itself. No game initialization or save writes.
        memory[0xC100:0xC106] = [0xF3, 0xCD, target & 255, target >> 8, 0x18, 0xFE]
        # Stop the send-in path at its first base-data lookup, after identity
        # publication. This patches only the emulator's ROM view.
        base_bank, base_addr = symbols["GetBaseData"]
        memory[base_bank, base_addr:base_addr + 3] = [0xC3, 0x04, 0xC1]
        count = 0
        integration_count = 0
        for transient in (False, True):
            for native, root, form in cases:
                for slot in range(6):
                    for metadata in (0, 0x40, 0x80, 0xC0):
                        memory[0xFF70] = 1
                        marker = 0x16BC if transient else 0
                        memory[addr("wPokemonDataFormat"):addr("wPokemonDataFormat") + 2] = list(marker.to_bytes(2, "little"))
                        source = party_start + slot * stride
                        original = [(i * 7 + 3) & 255 for i in range(stride)]
                        original[0] = 7 if transient else root
                        original[form_offset] = form | metadata
                        memory[source:source + stride] = original
                        memory[addr("wCurPartyMon")] = slot
                        memory[0xFF70] = 2
                        entry = addr("wPokemonIndexTableEntries") + 2 * (7 - 1)
                        memory[entry:entry + 2] = list(native.to_bytes(2, "little"))
                        memory[0xFF70] = 1
                        before = [0xA5] * (battle_end - battle_start)
                        before[0] = original[0]
                        before[addr("wBattleMonForm") - battle_start] = form | metadata
                        memory[battle_start:battle_end] = before
                        memory[0x2000] = bank
                        memory[addr("hROMBank")] = bank
                        regs.B, regs.C, regs.D, regs.E, regs.HL = 0x12, 0x34, 0x56, 0x78, 0xC222
                        memory[0xC101:0xC104] = [0xCD, target & 255, target >> 8]
                        regs.SP, regs.PC = 0xC0FF, 0xC100
                        emulator.tick(1, False, False)
                        assert regs.PC == 0xC104, (transient, native, slot, hex(regs.PC))
                        expected = before.copy()
                        expected[0] = root
                        assert memory[battle_start:battle_end] == expected, (transient, native, slot, metadata)
                        assert memory[source:source + stride] == original
                        assert (regs.B, regs.C, regs.D, regs.E, regs.HL, regs.SP) == (0x12, 0x34, 0x56, 0x78, 0xC222, 0xC0FF)
                        assert memory[addr("hROMBank")] == bank
                        assert memory[0xFF70] & 7 == 1
                        count += 1

                        for enemy in (False, True):
                            prefix = "wEnemyMon" if enemy else "wBattleMon"
                            temp = "wTempEnemyMon" if enemy else "wTempBattleMon"
                            src_prefix = "wOTPartyMon1" if enemy else "wPartyMon1"
                            party = addr(src_prefix + "Species")
                            selected = party + slot * stride
                            memory[selected:selected + stride] = original
                            memory[addr("hBattleTurn")] = int(enemy)
                            dest_start, dest_end = addr(prefix + "Species"), addr(prefix + "Type1")
                            expected = [0xA5] * (dest_end - dest_start)
                            # Match the source record fields, independent of how
                            # the send-in assembly implements its copies.
                            for first, last in (("Species", "ID"), ("DVs", "PokerusStatus"), ("Level", None)):
                                start = addr(src_prefix + first) - party
                                end = addr(src_prefix + last) - party if last else stride
                                dst = addr(prefix + first) - dest_start
                                expected[dst:dst + end - start] = original[start:end]
                            expected[0] = original[0] if enemy else root
                            memory[dest_start:dest_end] = [0xA5] * len(expected)
                            shadow_name = "wEnemyMonNativeSpecies" if enemy else "wBattleMonNativeSpecies"
                            shadow_addr = addr(shadow_name)
                            memory[shadow_addr:shadow_addr + 2] = [0xA5, 0x5A]
                            entry_bank, entry_addr = symbols["SendInUserPkmn.got_partymon"]
                            memory[0x2000] = entry_bank
                            memory[addr("hROMBank")] = entry_bank
                            memory[0xC101:0xC104] = [0xCD, entry_addr & 255, entry_addr >> 8]
                            regs.HL = party
                            regs.SP, regs.PC = 0xC0FF, 0xC100
                            emulator.tick(1, False, False)
                            assert regs.PC == 0xC104
                            assert memory[dest_start:dest_end] == expected, ("send-in", transient, native, slot, metadata, enemy)
                            assert memory[selected:selected + stride] == original
                            for name in ("wCurSpecies", "wCurPartySpecies", temp + "Species"):
                                assert memory[addr(name)] == expected[0], name
                            for name in ("wCurForm", temp + "Form"):
                                assert memory[addr(name)] == form | metadata, name
                            # Player send-ins always have a known native identity. For
                            # opponents, the legacy-format cases do too; transient-marker
                            # opponent fixtures intentionally keep their old byte value.
                            if not enemy or not transient:
                                got_native = int.from_bytes(
                                    bytes(memory[shadow_addr:shadow_addr + 2]), "little")
                                assert got_native == native, (
                                    "active-native", transient, native, slot, metadata, enemy, got_native)
                            integration_count += 1
        print(f"PASS: {count} decoder CPU cases and {integration_count} send-in cases; legacy/transient identities, both battle sides, six slots, extended species, variant forms, metadata and register/bank preservation")
    finally:
        emulator.stop(save=False)


if __name__ == "__main__":
    main()
