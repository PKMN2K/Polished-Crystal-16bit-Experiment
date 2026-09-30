"""Tree sleep uses the generated opponent record's native identity and ability."""
import argparse
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

    def addr(label):
        return symbols[label][1]

    def offset(label):
        bank, address = symbols[label]
        return bank * 0x4000 + address - (0x4000 if bank else 0)

    data = rom.read_bytes()
    table = offset("NativeVariantIdentityTable")
    root = Path(__file__).resolve().parents[1]
    nvariants = sum(line.strip().startswith("native_variant_identity ")
                    for line in (root / "data/pokemon/native_variant_name_roots.asm").read_text().splitlines())
    end = table + 5 * nvariants
    variant = next(
        (int.from_bytes(data[p:p + 2], "little"), 26, 2)
        for p in range(table, end, 5)
        if int.from_bytes(data[p + 2:p + 4], "little") == 26
        and data[p + 4] == 2
    )
    cases = [(n, n & 255, 1 | ((n >> 8) << 5))
             for n in (10, 48, 163, 164, 214, 56, 239, 257)] + [variant]
    base_size = addr("wCurBaseDataEnd") - addr("wCurBaseData")
    ability_offset = addr("wBaseAbility1") - addr("wCurBaseData")
    base = offset("BaseDataRecords")
    lists = []
    list_table = offset("AsleepTreeMons")
    for time in range(4):
        pos = list_table + time + data[list_table + time]
        identities = set()
        while int.from_bytes(data[pos:pos + 2], "little"):
            identities.add(int.from_bytes(data[pos:pos + 2], "little"))
            pos += 2
        lists.append(identities)

    pyboy = PyBoy(str(rom), window="null", sound_emulated=False,
                  cgb=True, log_level="ERROR")
    mem, regs = pyboy.memory, pyboy.register_file
    calls = {name: [] for name in ("GetAbility", "IsLegacySpeciesInNativeList",
                                  "IsNativeSpeciesInListBC")}
    for name, entries in calls.items():
        bank, address = symbols[name]
        pyboy.hook_register(bank, address, lambda _, e=entries: e.append(
            (regs.B, regs.C, regs.HL, mem[regs.HL], mem[regs.HL + 1])
        ), None)

    def invoke(label):
        bank, target = symbols[label]
        mem[0x2000] = bank
        mem[addr("hROMBank")] = bank
        mem[0xC100:0xC106] = [0xF3, 0xCD, target & 255, target >> 8, 0x18, 0xFE]
        regs.SP, regs.PC = 0xC0FF, 0xC100
        pyboy.tick(2, False, False)
        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF), label
        assert mem[addr("hROMBank")] == bank, label
        assert mem[0xFF70] & 7 == 1, label
        return bool(regs.F & 0x10)

    try:
        mem[0xFF50] = 1
        mem[0xFFFF] = mem[0xFF0F] = mem[0xFF40] = 0
        mem[0xFF70] = 1
        stride = addr("wOTPartyMon2Species") - addr("wOTPartyMon1Species")
        record = addr("wOTPartyMon1Species")
        protected = ("wTempEnemyMonSpecies", "wTempEnemyMonForm",
                     "wEnemyMonSpecies", "wEnemyMonPersonality",
                     "wCurSpecies", "wCurPartySpecies", "wCurForm")
        count = 0
        for native, species, form in cases:
            for slot, selector in enumerate((0x20, 0x40, 0x60)):
                ability = data[base + (native - 1) * base_size + ability_offset + slot]
                for enabled in (False, True):
                    for time in range(4):
                        for battle_type in (0, 4):
                            context = (native, selector, enabled, time, battle_type)
                            mem[record:record + stride] = [0xA5] * stride
                            mem[addr("wOTPartyMon1Species")] = species
                            mem[addr("wOTPartyMon1Form")] = form | 0x80
                            mem[addr("wOTPartyMon1Personality")] = selector
                            # Encounter and active fields deliberately disagree.
                            for label, value in zip(protected, (25, 1, 150, 0x60, 91, 92, 3)):
                                mem[addr(label)] = value
                            mem[addr("wInitialOptions")] = 2 if enabled else 0
                            mem[addr("wBattleType")] = battle_type
                            mem[addr("wTimeOfDay")] = time
                            base_start = addr("wCurBaseData")
                            mem[base_start:base_start + base_size] = [0x5A] * base_size
                            before = bytes(mem[record:record + stride])
                            globals_before = [mem[addr(label)] for label in protected]
                            for entries in calls.values():
                                entries.clear()
                            immune = enabled and ability in (15, 65)  # Insomnia/Vital Spirit
                            expected = battle_type == 4 and not immune and native in lists[time]
                            actual = invoke("CheckSleepingTreeMon")
                            assert actual == expected, (context, actual, expected, calls)
                            assert bytes(mem[record:record + stride]) == before, context
                            assert [mem[addr(label)] for label in protected] == globals_before, context
                            assert bytes(mem[base_start:base_start + base_size]) == bytes([0x5A] * base_size), context
                            assert not calls["GetAbility"], context
                            assert not calls["IsLegacySpeciesInNativeList"], context
                            assert len(calls["IsNativeSpeciesInListBC"]) == int(battle_type == 4 and not immune), context
                            count += 1

        # The shared matcher must compare full words, including identities
        # above the old nine-bit boundary, without touching conversion tables.
        high_cases = 0
        values = (0x01FF, 0x0200, 0x1200, 0xFFFF)
        mem[0xC280:0xC28A] = list(b"".join(n.to_bytes(2, "little") for n in (*values, 0)))
        for native in (*values, 0, 0x0100, 0x0201, 0xFF00):
            regs.B, regs.C = native >> 8, native & 255
            regs.D, regs.E, regs.HL = 0x56, 0x78, 0xC280
            assert invoke("IsNativeSpeciesInListBC") == (native in values), hex(native)
            assert (regs.B, regs.C, regs.D, regs.E) == (native >> 8, native & 255, 0x56, 0x78)
            high_cases += 1
        print(f"PASS: {count} native tree-sleep cases and {high_cases} full-word list cases; "
              "generated identity/personality, ability options, sleep immunity and time lists "
              "ignore stale encounter/active fields and preserve records/base data")
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
