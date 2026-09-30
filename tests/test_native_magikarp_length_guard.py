"""Generated native identity gates the real wild Magikarp length retry logic."""
import argparse
from pathlib import Path
from pyboy import PyBoy


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('rom', type=Path)
    rom = ap.parse_args().rom
    syms = {}
    for line in rom.with_suffix('.sym').read_text().splitlines():
        f = line.split()
        if len(f) == 2 and ':' in f[0]:
            syms[f[1]] = tuple(int(v, 16) for v in f[0].split(':'))
    def addr(label):
        return syms[label][1]
    data = rom.read_bytes()
    bank, target = syms['CheckValidMagikarpLength.CheckMagikarpArea']
    pos = bank * 0x4000 + target - (0x4000 if bank else 0)
    assert data[pos] == data[pos + 7] == 0xFA
    assert data[pos + 3] == data[pos + 10] == 0xFE
    lake = (data[pos + 4], data[pos + 11])
    p = PyBoy(str(rom), window='null', sound_emulated=False, cgb=True, log_level='ERROR')
    mem, regs = p.memory, p.register_file
    calls, rolls = [], []
    length = 1200
    def calc(_):
        calls.append(('calc', regs.D << 8 | regs.E, regs.B << 8 | regs.C))
        mem[addr('wMagikarpLengthMmHi')] = length >> 8
        mem[addr('wMagikarpLengthMmLo')] = length & 255
    def random(_):
        calls.append(('random', regs.A))
        regs.A = rolls.pop(0) if rolls else 255
    for name, callback in [('CalcMagikarpLength', calc), ('RandomRange', random)]:
        b, a = syms[name]
        mem[b, a] = 0xC9
        p.hook_register(b, a, callback, None)
    def invoke(label):
        b, a = syms[label]
        mem[0x2000] = b
        mem[addr('hROMBank')] = b
        mem[0xC100:0xC106] = [0xF3, 0xCD, a & 255, a >> 8, 0x18, 0xFE]
        regs.SP, regs.PC = 0xC0FF, 0xC100
        p.tick(2, False, False)
        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF), (label, hex(regs.PC), hex(regs.SP), b, hex(a), mem[addr('hROMBank')], calls, sorted((v[1], k) for k, v in syms.items() if v[0] == b and v[1] <= regs.PC)[-5:], list(mem[regs.SP:0xC0FF]), {k: syms[k] for k in ('CalcMagikarpLength', 'RandomRange', 'GetNativeSpeciesIDFromLegacyPokemonDataStruct', 'GetNativeSpeciesIndexFromLegacyForm', 'GetSpeciesAndFormIndex', 'PopBCDEHL')}, (species, form, gender), hex(regs.HL), (regs.B, regs.C))
        assert mem[addr('hROMBank')] == b
        return bool(regs.F & 0x10), bool(regs.F & 0x80)
    try:
        mem[0xFF50] = 1
        mem[0xFFFF] = mem[0xFF0F] = mem[0xFF40] = 0
        mem[0xFF70] = 1
        start = addr('wOTPartyMon1Species')
        stride = addr('wOTPartyMon2Species') - start
        cases = [(129, f, True) for f in range(1, 21)] + [(129, 0x21, False), (25, 1, False), (1, 0x21, False), (0, 0, False)]
        count = 0
        for species, form, match in cases:
            for gender in (0, 0x80):
                mem[start:start + stride] = [0xA5] * stride
                mem[addr('wOTPartyMon1Species')] = species
                mem[addr('wOTPartyMon1Form')] = form | gender
                mem[addr('wTempEnemyMonSpecies')] = 25 if match else 129
                mem[addr('wEnemyMonSpecies')] = 25 if match else 129
                mem[addr('wEnemyMonNativeSpecies'):addr('wEnemyMonNativeSpecies') + 2] = [25 if match else 129, 0]
                before = bytes(mem[start:start + stride])
                regs.B, regs.C, regs.D, regs.E, regs.HL = 0x12, 0x34, 0x56, 0x78, 0xC280
                assert invoke('IsGeneratedWildMagikarp')[1] == match, (species, form, gender)
                assert (regs.B, regs.C, regs.D, regs.E, regs.HL) == (0x12, 0x34, 0x56, 0x78, 0xC280)
                calls.clear()
                rolls.clear()
                mem[addr('wMapGroup')], mem[addr('wMapNumber')] = 0, 0
                mem[addr('wMagikarpLengthMmHi')], mem[addr('wMagikarpLengthMmLo')] = 0xAB, 0xCD
                assert not invoke('CheckValidMagikarpLength')[0]
                assert calls == ([('calc', addr('wOTPartyMon1DVs'), addr('wPlayerID'))] if match else []), (species, form, calls)
                if not match:
                    assert (mem[addr('wMagikarpLengthMmHi')], mem[addr('wMagikarpLengthMmLo')]) == (0xAB, 0xCD)
                assert bytes(mem[start:start + stride]) == before
                count += 1
        scenarios = [
            (1599, False, [1, 1], False, [20, 5]),
            (1600, False, [1, 1], True, [20, 5]),
            (1615, False, [1, 1], True, [20, 5]),
            (1616, False, [1], True, [20]),
            (1616, False, [0], False, [20]),
            (1600, False, [1, 0], False, [20, 5]),
            (1000, True, [2], True, [5]),
            (1000, True, [0], False, [5]),
            (1000, True, [1], False, [5]),
            (1024, True, [2], False, [5]),
            (1616, True, [0, 2], False, [20, 5]),
        ]
        for length, at_lake, values, retry, ranges in scenarios:
            mem[addr('wOTPartyMon1Species')], mem[addr('wOTPartyMon1Form')] = 129, 1
            mem[addr('wMapGroup')], mem[addr('wMapNumber')] = lake if at_lake else (0, 0)
            calls.clear()
            rolls[:] = values
            assert invoke('CheckValidMagikarpLength')[0] == retry, (length, at_lake, values, calls)
            assert calls == [('calc', addr('wOTPartyMon1DVs'), addr('wPlayerID'))] + [('random', n) for n in ranges]
            assert not rolls
            count += 1
        print(f'PASS: {count} native Magikarp identity/length cases; cosmetic forms, conflicting encounter/active identities, full-word collision, size and Lake of Rage retry boundaries')
    finally:
        p.stop(save=False)


if __name__ == '__main__':
    main()
