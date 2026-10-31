"""CPU tests for species-dependent held items, Natural Cure and write-back.

Usage: python tests/test_battle_item_identity.py ROM.gbc
Requires PyBoy 2.7.0 and matching .sym; no gameplay save is loaded.
"""
import argparse
from pathlib import Path
from pyboy import PyBoy


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    args = parser.parse_args()
    symbols = {}
    for line in args.rom.with_suffix('.sym').read_text().splitlines():
        fields = line.split()
        if len(fields) == 2 and ':' in fields[0]:
            symbols[fields[1]] = tuple(int(x, 16) for x in fields[0].split(':'))
    def addr(name):
        return symbols[name][1]
    rom = args.rom.read_bytes()
    bank, address = symbols['NativeVariantIdentityTable']
    offset = bank * 0x4000 + address - 0x4000
    armored = next(int.from_bytes(rom[i:i + 2], 'little') for i in range(offset, offset + 500, 5)
                   if int.from_bytes(rom[i + 2:i + 4], 'little') == 150 and rom[i + 4] == 2)
    p = PyBoy(str(args.rom), window='null', sound_emulated=False, cgb=True, log_level='ERROR')
    m, r = p.memory, p.register_file
    stride = addr('wPartyMon2Species') - addr('wPartyMon1Species')
    def write(name, value):
        m[addr(name)] = value
    def reset(marker, slot, turn):
        for bank in (1, 2):
            m[0xFF70] = bank
            m[0xD000:0xE000] = [0] * 4096
        m[0xFF70] = 1
        write('wPokemonDataFormat', marker & 255)
        m[addr('wPokemonDataFormat') + 1] = marker >> 8
        write('wCurBattleMon', slot)
        write('wCurOTMon', slot)
        write('hBattleTurn', turn)
        write('wPlayerFutureSightCount', 0)
        write('wEnemyFutureSightCount', 0)
        write('wInitialOptions', 255)
    def party(enemy, slot, species, form=1, native=None, marker=0):
        prefix = 'wOTPartyMon1' if enemy else 'wPartyMon1'
        at = addr(prefix + 'Species') + slot * stride
        m[at] = 7 if marker == 0x16BC and not enemy else species
        m[addr(prefix + 'Form') + slot * stride] = form
        if not enemy:
            m[0xFF70] = 2
            start = addr('wPokemonIndexTableEntries') + 12
            m[start:start + 2] = list((native or species).to_bytes(2, 'little'))
            m[0xFF70] = 1
        return at
    def call(name, bc=100):
        bank, target = symbols[name]
        bank = bank or 1
        m[0x2000] = bank
        write('hROMBank', bank)
        m[0xFF70] = 1
        m[0xC100:0xC106] = [0xF3, 0xCD, target & 255, target >> 8, 0x18, 0xFE]
        r.B, r.C, r.D, r.E, r.HL = bc >> 8, bc & 255, 0x56, 0x78, 0xC222
        r.SP, r.PC = 0xC0FF, 0xC100
        p.tick(2, False, False)
        assert r.PC == 0xC104, (name, hex(r.PC))
        assert r.SP == 0xC0FF
        assert m[0xFF70] & 7 == 1
        assert m[addr('hROMBank')] == bank
    counts = dict(items=0, cure=0, writeback=0)
    try:
        m[0xFF50] = 1
        m[0xFFFF] = m[0xFF0F] = m[0xFF40] = 0
        for marker in (0, 0x16BC, 0x00BC, 0x1600):
            for slot in range(6):
                for turn in (0, 1):
                    for fn, species, item, expected in (
                        ('UnevolvedEviolite', 1, 0xA4, 150),
                        ('UnevolvedEviolite', 3, 0xA4, 100),
                        ('UnevolvedEviolite', 1, 0, 100),
                        ('DittoMetalPowder', 132, 0xBC, 150),
                        ('DittoMetalPowder', 25, 0xBC, 100),
                        ('DittoMetalPowder', 132, 0, 100),
                    ):
                        reset(marker, slot, turn)
                        for enemy in (False, True):
                            party(enemy, slot, species, marker=marker)
                        write('wBattleMonItem', item)
                        write('wEnemyMonItem', item)
                        call(fn)
                        assert (r.B << 8 | r.C) == expected, (fn, marker, slot, turn, r.B, r.C)
                        assert m[addr('hBattleTurn')] == turn
                        counts['items'] += 1
                    for player_armored in (False, True):
                        for enemy_armored in (False, True):
                            reset(marker, slot, turn)
                            party(False, slot, 150 if player_armored else 25,
                                  2 if player_armored else 1, armored if player_armored else 25, marker)
                            party(True, slot, 150 if enemy_armored else 25, 2 if enemy_armored else 1)
                            write('wBattleMonItem', 0xBE)
                            write('wEnemyMonItem', 0xBE)
                            call('UserCanLoseItem')
                            assert bool(r.F & 0x80) == (player_armored or enemy_armored), (marker, slot, turn, player_armored, enemy_armored)
                            assert m[addr('hBattleTurn')] == turn
                            counts['items'] += 1
                for egg in (False, True):
                    reset(marker, slot, 0)
                    # Earlier slots are Eggs so only the selected Staryu runs.
                    for i in range(slot + 1):
                        party(False, i, 120, 0x41 if i < slot or egg else 1, marker=marker)
                        m[addr('wPartyMon1Personality') + i * stride] = 0x40  # Natural Cure
                        m[addr('wPartyMon1Status') + i * stride] = 8
                    write('wPartyCount', slot + 1)
                    call('RunPostBattleAbilities')
                    assert m[addr('wPartyMon1Status') + slot * stride] == (8 if egg else 0)
                    for i in range(slot):
                        assert m[addr('wPartyMon1Status') + i * stride] == 8
                    counts['cure'] += 1
                for enemy in (False, True):
                    reset(marker, slot, 0)
                    prefix = 'wOTPartyMon1' if enemy else 'wPartyMon1'
                    battle = 'wEnemyMon' if enemy else 'wBattleMon'
                    at = addr(prefix + 'Species') + slot * stride
                    before = [(i * 7 + 3) & 255 for i in range(stride)]
                    m[at:at + stride] = before
                    start = addr(prefix + 'Level') - addr(prefix + 'Species')
                    length = addr(battle + 'MaxHP') - addr(battle + 'Level')
                    data = [20, 8, 0, 0, 25]
                    assert len(data) == length
                    m[addr(battle + 'Level'):addr(battle + 'MaxHP')] = data
                    call('UpdateEnemyMonInParty' if enemy else 'UpdateBattleMonInParty')
                    expected = before.copy()
                    expected[start:start + length] = data
                    assert m[at:at + stride] == expected
                    counts['writeback'] += 1
        print('PASS:', counts, 'CPU cases; both sides, six slots, marker variants, held-item rules, Natural Cure/Egg exclusion and identity-preserving HP/status write-back')
    finally:
        p.stop(save=False)


if __name__ == '__main__':
    main()
