"""Exercise native Hall of Fame save/load without stubbing the identity decoder."""
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

    def address(name):
        return symbols[name][1]

    data = rom.read_bytes()
    root = Path(__file__).resolve().parents[1]
    count = sum(line.strip().startswith("native_variant_identity ") for line in
                (root / "data/pokemon/native_variant_name_roots.asm").read_text().splitlines())
    bank, at = symbols["NativeVariantIdentityTable"]
    start = bank * 0x4000 + at - 0x4000
    variants = [(int.from_bytes(data[p:p+2], "little"),
                 int.from_bytes(data[p+2:p+4], "little"), data[p+4])
                for p in range(start, start + 5 * count, 5)]
    identities = [(25, 25, 1), (257, 257, 1)] + variants
    identities += [(129, 129, form) for form in range(1, 21)]
    mon_length = address("wHallOfFameTempMon1End") - address("wHallOfFameTempMon1")
    team_length = address("sHallOfFame02") - address("sHallOfFame01")
    native_length = 6 * 2
    teams = (address("sHallOfFameEnd") - address("sHallOfFame")) // team_length
    assert team_length == 2 + mon_length * 6

    pyboy = PyBoy(str(rom), window="null", sound_emulated=False, cgb=True, log_level="ERROR")
    mem, regs = pyboy.memory, pyboy.register_file

    def write(at, values):
        mem[at:at+len(values)] = list(values)

    def read(at, length):
        return bytes(mem[at:at+length])

    def open_sram():
        mem[0] = 0x0A
        mem[0x4000] = symbols["sHallOfFame"][0]

    def invoke(name, hl=0xC280, de=0xC380):
        bank, target = symbols[name]
        mem[0x2000] = bank
        mem[address("hROMBank")] = bank
        write(0xC100, [0xF3, 0xCD, target & 255, target >> 8, 0x18, 0xFE])
        regs.HL, regs.D, regs.E = hl, de >> 8, de & 255
        regs.SP, regs.PC = 0xC0FF, 0xC100
        pyboy.tick(8, False, False)
        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF), (name, hex(regs.PC), hex(regs.SP))
        assert mem[address("hROMBank")] == bank, name
        assert mem[0xFF70] & 7 == 1, name
        return bool(regs.F & 0x10)

    def record(species, form, seed):
        # Trainer ID, personality, level and nickname must survive byte-for-byte.
        result = bytearray((seed + i) & 255 for i in range(mon_length))
        result[0], result[4] = species, form
        return result

    checks = 0
    try:
        mem[0xFF50] = 1
        mem[0xFFFF] = mem[0xFF0F] = mem[0xFF40] = 0
        mem[0xFF70] = 1
        mem[0] = 0x0A
        mem[0x4000] = symbols["sSRAMAccessCount"][0]
        mem[address("sSRAMAccessCount")] = 0
        mem[address("wSRAMAccessCount")] = 1
        open_sram()
        write(address("sHallOfFameNativeMagic"), [0xF0, 0x16])

        # Read the native shadow as the authority, including stale legacy
        # species/form bytes. Exercise all six slots and keep empty slots intact.
        for native, species, form in identities:
            for metadata in (0, 0x40, 0x80, 0xC0):
                originals, expected, words = bytearray(), bytearray(), bytearray()
                for slot in range(6):
                    empty = slot == 5
                    legacy_form = (0x3F if native != species else form | 0x20) | metadata
                    before = record(0xFF if empty else 19, legacy_form, 0x50 + slot)
                    after = bytearray(before)
                    if not empty:
                        after[0] = species & 255
                        after[4] = form | ((species >> 8) << 5) | metadata
                    originals.extend(before)
                    expected.extend(after)
                    words.extend((0 if empty else native).to_bytes(2, "little"))
                open_sram()
                write(address("sHallOfFameNativeSpecies"), words)
                write(address("wHallOfFameTempMon1"), originals)
                invoke("ApplyHallOfFameNativeSpecies", address("sHallOfFameNativeSpecies"),
                       address("wHallOfFameTempMon1"))
                actual = read(address("wHallOfFameTempMon1"), mon_length * 6)
                assert actual == expected, ("native overlay", hex(native), hex(metadata), actual.hex(), expected.hex())
                assert read(address("sHallOfFameNativeSpecies"), native_length) == words
                checks += 1

        # The real SRAM loader must select the matching shadow for every stored
        # team, preserve metadata, and leave both saved representations unchanged.
        legacy_teams, expected_teams, native_teams = [], [], []
        for team in range(teams):
            legacy, expected, words = bytearray([team + 1]), bytearray([team + 1]), bytearray()
            for slot in range(6):
                native, species, form = identities[(team * 6 + slot) % len(identities)]
                metadata = (slot % 4) << 6
                before = record(19, metadata | (0x3F if native != species else form | 0x20), 0x60 + slot)
                after = record(species & 255, metadata | form | ((species >> 8) << 5), 0x60 + slot)
                legacy.extend(before)
                expected.extend(after)
                words.extend(native.to_bytes(2, "little"))
            legacy.append(0xFF)
            expected.append(0xFF)
            legacy_teams.append(bytes(legacy))
            expected_teams.append(bytes(expected))
            native_teams.append(bytes(words))
        open_sram()
        write(address("sHallOfFame"), b"".join(legacy_teams))
        write(address("sHallOfFameNativeSpecies"), b"".join(native_teams))
        for team in range(teams):
            mem[address("wJumptableIndex")] = team
            assert not invoke("LoadHOFTeam"), team
            assert read(address("wHallOfFameTemp"), team_length) == expected_teams[team], team
            open_sram()
            assert read(address("sHallOfFame"), team_length * teams) == b"".join(legacy_teams)
            assert read(address("sHallOfFameNativeSpecies"), native_length * teams) == b"".join(native_teams)
            checks += 1

        # Add a new team and prove the legacy records and native words shift
        # together. The new native shadow is built by the production save code.
        new_team = expected_teams[-1]
        write(address("wOverworldMapBlocks"), new_team)
        invoke("AddHallOfFameEntry")
        saved_legacy = [new_team] + legacy_teams[:-1]
        saved_native = [native_teams[-1]] + native_teams[:-1]
        open_sram()
        assert read(address("sHallOfFame"), team_length * teams) == b"".join(saved_legacy)
        assert read(address("sHallOfFameNativeSpecies"), native_length * teams) == b"".join(saved_native)
        mem[address("wJumptableIndex")] = 0
        assert not invoke("LoadHOFTeam")
        assert read(address("wHallOfFameTemp"), team_length) == new_team
        checks += 1

        # Generate the saved team from actual player records, in both supported
        # RAM formats. Eggs are omitted without misaligning the native shadow.
        party_length = address("wPartyMon2Species") - address("wPartyMon1Species")
        party_start = address("wPartyMon1Species")
        for marker in (0, 0x16BC):
            for egg_slots in ((), (0,), (5,), tuple(range(6))):
                write(address("wPokemonDataFormat"), marker.to_bytes(2, "little"))
                mem[address("wPartyCount")] = 6
                mem[address("wHallOfFameCount")] = 42
                expected = bytearray([42])
                words = bytearray()
                for slot in range(6):
                    native, species, form = identities[slot]
                    at = party_start + slot * party_length
                    write(at, bytes(party_length))
                    mem[at] = slot + 1 if marker else species & 255
                    # A transient variant's form byte can be stale. The native
                    # ID still determines its mechanical form in the saved team.
                    raw_form = 1 if marker and native != species else form
                    metadata = 0x80 if slot % 2 else 0
                    form_byte = raw_form | ((species >> 8) << 5) | metadata
                    if slot in egg_slots:
                        form_byte |= 0x40
                    mem[at + address("wPartyMon1Form") - party_start] = form_byte
                    personal = 0x21 + slot
                    mem[at + address("wPartyMon1Personality") - party_start] = personal
                    write(at + address("wPartyMon1ID") - party_start, [slot + 1, slot + 11])
                    mem[at + address("wPartyMon1Level") - party_start] = slot + 30
                    nickname = bytes([0x80 + slot] * (mon_length - 6))
                    write(address("wPartyMonNicknames") + slot * (len(nickname) + 1), nickname + b"\x53")
                    mem[0xFF70] = 2
                    write(address("wPokemonIndexTableEntries") + slot * 2,
                          native.to_bytes(2, "little"))
                    mem[0xFF70] = 1
                    if slot not in egg_slots:
                        expected.extend([species & 255, slot + 1, slot + 11,
                                         personal, form | ((species >> 8) << 5) | metadata, slot + 30])
                        expected.extend(nickname)
                        words.extend(native.to_bytes(2, "little"))
                expected.append(0xFF)
                expected.extend(bytes(team_length - len(expected)))
                words.extend(bytes(native_length - len(words)))
                party_before = read(party_start, party_length * 6)
                invoke("GetHallOfFameParty")
                assert read(party_start, party_length * 6) == party_before
                assert read(address("wOverworldMapBlocks"), team_length) == expected, (marker, egg_slots)
                invoke("AddHallOfFameEntry")
                open_sram()
                assert read(address("sHallOfFameNativeSpecies"), native_length) == words, (marker, egg_slots)
                mem[address("wJumptableIndex")] = 0
                assert not invoke("LoadHOFTeam")
                assert read(address("wHallOfFameTemp"), team_length) == expected, (marker, egg_slots)
                checks += 1

        print(f"PASS: {checks} native Hall of Fame cases; all mechanical variants, extended roots, "
              "cosmetic forms, metadata, empty slots, ten saved teams, history rotation and live party/egg save/load")
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
