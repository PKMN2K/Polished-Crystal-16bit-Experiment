"""Play native-identity battles, storage and lifecycle scenarios using joypad input.

Requires native_gameplay_test=1, NATIVE_TEST_SPECIES=767, NATIVE_TEST_MOVE=64769.
No CPU hooks, memory/register writes, ROM patches or emulator save states.
"""
import argparse
from io import BytesIO
import json
from pathlib import Path
import re
from pyboy import PyBoy


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('rom', type=Path)
    ap.add_argument('--output', type=Path, default=Path('build/test-results/gameplay'))
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    syms = {}
    for line in args.rom.with_suffix('.sym').read_text().splitlines():
        fields = line.split()
        if len(fields) == 2 and ':' in fields[0]:
            syms[fields[1]] = tuple(int(x, 16) for x in fields[0].split(':'))
    assert 'wNativeGameplayStage' in syms, 'build with native_gameplay_test=1'
    rom = args.rom.read_bytes()
    chars = {}
    for line in (Path(__file__).resolve().parents[2] / 'constants/charmap.asm').read_text().splitlines():
        match = re.match(r'\s*charmap "([^"]+)",\s+\$([0-9a-f]+)', line, re.I)
        if match and len(match[1]) == 1: chars[int(match[2], 16)] = match[1]
    def constant(label):
        bank, at = syms[label]
        start = bank * 0x4000 + at % 0x4000
        return int.from_bytes(rom[start:start+2], 'little')
    species, move = constant('NativeWideTestIdentity'), constant('NativeWideMoveTestIdentity')
    assert (species, move) == (0x02ff, 0xfd01)
    p = None
    frames = 0
    evidence = {'species': hex(species), 'move': hex(move), 'input': 'joypad only', 'checkpoints': []}
    def boot(ram=None, rtc=None):
        game = PyBoy(BytesIO(rom), ram_file=ram, rtc_file=rtc,
                     window='null', sound_emulated=False, cgb=True, log_level='ERROR')
        game.set_emulation_speed(0)
        return game
    def read(label, size=1, offset=0):
        if not size: return b''
        bank, at = syms[label]; at += offset
        if 0xd000 <= at < 0xe000 or 0xa000 <= at < 0xc000:
            return bytes(p.memory[bank, at:at+size])
        return bytes(p.memory[at:at+size])
    def byte(label): return read(label)[0]
    def word(label): return int.from_bytes(read(label, 2), 'little')
    def item_count(item):
        items = read('wMedicine', byte('wNumMedicine') * 2)
        return next((items[i+1] for i in range(0, len(items), 2) if items[i] == item), 0)
    def native(table, handle):
        return int.from_bytes(read(table, 2, (handle-1)*2), 'little') if handle else 0
    def party():
        return [{'species': native('wPokemonIndexTableEntries', byte(f'wPartyMon{i}Species')),
                 'form': byte(f'wPartyMon{i}Form'),
                 'level': byte(f'wPartyMon{i}Level'),
                 'exp': int.from_bytes(read(f'wPartyMon{i}Exp', 3), 'big'),
                 'moves': [native('wMoveIndexTableEntries', h) for h in read(f'wPartyMon{i}Moves', 4)],
                 'pp': list(read(f'wPartyMon{i}PP', 4))}
                for i in range(1, byte('wPartyCount')+1)]
    def text():
        tiles = read('wTilemap', 360)
        return '\n'.join(''.join(chars.get(x, ' ') for x in tiles[row:row+20]) for row in range(0, 360, 20))
    def tick(n=60):
        nonlocal frames
        assert frames + n <= 300000, 'gameplay frame budget exceeded'
        p.tick(n, True, False); frames += n
    def press(key, n=60, hold=3):
        p.button(key, hold); tick(n)
    def checkpoint(name):
        p.screen.image.save(str(args.output / (name + '.png')))
        evidence['checkpoints'].append({'name': name, 'frame': frames, 'party': party()})
        print('PASS', name, 'frame', frames, flush=True)
    def until(description, predicate, action, limit=400):
        for _ in range(limit):
            if predicate(): return
            action(text())
        raise AssertionError(description + ' timed out\n' + text())
    def in_room(): return byte('wMapGroup') == 24 and byte('wMapNumber') == 5
    def dialog(t):
        if 'Shift' in t and 'End' in t:
            press('start', 30); press('a')
        elif 'nickname' in t.lower() and 'Yes' in t and 'No' in t:
            press('b')
        else: press('a')
    def initial(t):
        if 'Natures' in t and 'Abilities' in t: press('start')
        else: dialog(t)
    def battle_identity():
        assert word('wBattleMonNativeSpecies') == species
        assert word('wEnemyMonNativeSpecies') == species
    def close_event():
        until('scenario text closes', lambda: byte('wScriptMode') == 0, lambda _: press('b'))
        tick(90)
    def fixture_event():
        assert byte('wPlayerMapY') == 6
        press('a')
    def pc_cursor(target):
        def navigate(_):
            pos = byte('wBillsPC_CursorPos')
            x, y = pos & 15, pos >> 4
            tx, ty = target & 15, target >> 4
            # The upper-left area contains the portrait, not selectable slots.
            if tx >= 2 and x != tx:
                press('right' if x < tx else 'left', 20)
            elif y != ty:
                press('down' if y < ty else 'up', 20)
            else: press('right' if x < tx else 'left', 20)
        until('PC cursor', lambda: byte('wBillsPC_CursorPos') == target, navigate, limit=20)
    def select_party(slot):
        until('party selection', lambda: byte('wMenuCursorY') == slot,
              lambda _: press('down', 20), limit=8)
        press('a')
    def save_reload(tag):
        nonlocal p
        press('start', 90)
        until('Save selection', lambda: any('▶Save' in row for row in text().splitlines()),
              lambda _: press('down', 20), limit=10)
        press('a')
        until('saved message', lambda: 'saved' in text().lower() and 'the game.' in text().lower(), dialog)
        tick(180)
        before = party()
        checkpoint(tag + 'saved')
        ram, rtc = BytesIO(), BytesIO()
        p.stop(save=True, ram_file=ram, rtc_file=rtc); p = None
        (args.output / (tag + 'scenario.ram')).write_bytes(ram.getvalue())
        (args.output / (tag + 'scenario.rtc')).write_bytes(rtc.getvalue())
        assert len(ram.getvalue()) == 32768
        ram.seek(0); rtc.seek(0)
        p = boot(ram, rtc)
        saw_continue = False
        def continuing(t):
            nonlocal saw_continue
            if 'Continue' in t: saw_continue = True
            if in_room() and 'Badges' not in t:
                press('down', 45, 15)
            else:
                press('a')
        # Loading the save publishes map IDs before the Continue confirmation.
        # Require actual overworld movement to prove confirmation and map entry.
        until('cold Continue and movement',
              lambda: in_room() and byte('wPlayerMapY') == 7, continuing)
        tick(180)
        assert saw_continue, 'save was not offered by the main menu'
        assert word('wPokemonDataFormat') == 0x16bc and word('wMoveDataFormat') == 0x16bd
        assert party() == before, ('cold reload changed party', before, party())
        checkpoint(tag + 'cold-continue')
    try:
        p = boot()
        until('New Game', in_room, initial)
        tick(180)
        assert word('wPokemonDataFormat') == 0x16bc and word('wMoveDataFormat') == 0x16bd
        assert byte('wPartyCount') == 0
        checkpoint('new-game')
        press('up', 45, 15)
        assert byte('wPlayerMapY') == 6
        press('a')
        until('gift and battle entrance', lambda: 'Fight' in text() and 'Bag' in text(), dialog)
        battle_identity()
        gifted = party()
        assert len(gifted) == 1 and gifted[0]['species'] == species
        assert gifted[0]['moves'] == [33, 45, move, 0], gifted
        checkpoint('gift-battle')
        used_ember = False
        def fight(t):
            nonlocal used_ember
            if 'Ember!' in t: used_ember = True
            if 'Tackle' in t and 'Growl' in t and 'Ember' in t:
                battle_identity()
                rows = t.splitlines()
                target = next(i for i, row in enumerate(rows) if 'Ember' in row)
                cursor = next((i for i, row in enumerate(rows) if '▶' in row), None)
                assert cursor is not None, t
                press('down' if cursor < target else 'up' if cursor > target else 'a')
            else: dialog(t)
        until('wide move battle victory', lambda: byte('wNativeGameplayStage') == 2, fight)
        won = party()
        assert used_ember, 'wide Ember use was not observed'
        assert won[0]['pp'][2] < gifted[0]['pp'][2]
        assert won[0]['exp'] > gifted[0]['exp'] and byte('wBattleResult') & 15 == 0
        checkpoint('battle-won')
        until('second encounter', lambda: 'Fight' in text() and 'Bag' in text(), dialog)
        battle_identity()
        press('down', 20); press('a', 90)
        until('ball pocket', lambda: 'Master Ball' in text(), lambda _: press('right'), limit=8)
        press('a'); press('a')
        until('capture and cleanup', lambda: byte('wNativeGameplayStage') == 3, dialog)
        until('scenario text closes', lambda: byte('wScriptMode') == 0, lambda _: press('b'))
        assert byte('wBattleMode') == 0 and byte('wBattleResult') & 0x40
        caught = party()
        assert len(caught) == 2 and all(mon['species'] == species for mon in caught), caught
        assert caught[0]['moves'] == gifted[0]['moves'] and caught[1]['level'] == 5
        checkpoint('captured')
        save_reload('')
        press('up', 45, 15)
        press('left', 45, 15)
        press('up', 20)
        fixture_event()
        until('trainer battle entrance', lambda: 'Fight' in text() and 'Bag' in text(), dialog)
        assert byte('wBattleMode') == 2 and byte('wOTPartyCount') == 2
        enemies = set()
        def trainer_fight(t):
            if 'Fight' in t and 'Bag' in t:
                enemies.add(word('wEnemyMonNativeSpecies'))
                assert word('wBattleMonNativeSpecies') == species
            if 'Tackle' in t and 'Growl' in t and 'Ember' in t:
                rows = t.splitlines()
                target = next(i for i, row in enumerate(rows) if 'Ember' in row)
                cursor = next((i for i, row in enumerate(rows) if '▶' in row), None)
                assert cursor is not None, t
                press('down' if cursor < target else 'up' if cursor > target else 'a')
            elif 'switch' in t.lower() and 'Yes' in t and 'No' in t:
                press('b')
            else: dialog(t)
        until('complete trainer battle', lambda: byte('wNativeGameplayStage') == 4, trainer_fight)
        close_event()
        assert enemies == {species, 19}, enemies
        assert byte('wBattleMode') == 0 and byte('wBattleResult') & 15 == 0
        checkpoint('trainer-battle-won')
        before_pc = party()
        fixture_event()
        until('PC choice', lambda: 'Turn Off' in text(), dialog)
        press('a', 180)
        until('PC storage opens', lambda: byte('wBillsPC_CursorPos') == 0x12 and
              any(read('wBillsPC_PartyList', 12)), dialog)
        checkpoint('pc-open')
        pc_cursor(0x30)
        press('a')
        assert 'Deposit' in text(), text()
        press('a', 180)
        until('PC deposit', lambda: byte('wPartyCount') == 1, dialog)
        assert party()[0] == before_pc[1], party()
        checkpoint('pc-deposited')
        pc_cursor(0x12)
        press('a')
        assert 'Withdraw' in text(), text()
        press('a', 180)
        until('PC withdrawal', lambda: byte('wPartyCount') == 2, dialog)
        after_pc = party()
        for field in ('species', 'form', 'level', 'exp', 'moves'):
            assert after_pc[1][field] == before_pc[0][field], (field, before_pc, after_pc)
        assert after_pc[1]['pp'] == [35, 40, 25, 0], after_pc
        checkpoint('pc-withdrawn')
        press('b'); press('b', 120)
        until('PC exit', lambda: byte('wNativeGameplayStage') == 5, lambda _: press('b'))
        close_event()
        fixture_event()
        until('daycare party menu', lambda: 'Cancel' in text() and 'Annihilape' in text(), dialog)
        select_party(2)
        until('daycare deposit', lambda: byte('wNativeGameplayStage') == 6, dialog)
        close_event()
        assert byte('wPartyCount') == 1, party()
        assert native('wPokemonIndexTableEntries', byte('wBreedMon1Species')) == species
        assert [native('wMoveIndexTableEntries', h) for h in read('wBreedMon1Moves', 4)] == before_pc[0]['moves']
        checkpoint('daycare-deposited')
        fixture_event()
        until('daycare withdrawal', lambda: byte('wNativeGameplayStage') == 7, dialog)
        close_event()
        # Daycare's existing withdrawal policy resets EXP to the level floor.
        expected_daycare = [after_pc[0], dict(after_pc[1], exp=20**3)]
        assert party() == expected_daycare, (expected_daycare, party())
        checkpoint('daycare-withdrawn')
        fixture_event()
        until('lesson gifts', lambda: byte('wNativeGameplayStage') == 8, dialog)
        close_event()
        assert len(party()) == 4 and party()[2]['species'] == 0x123
        assert party()[3]['species'] == species and party()[3]['form'] & 0x40
        assert party()[2]['moves'] == [33, 45, 43, 10], party()
        checkpoint('lesson-gifts')
        press('start', 90)
        until('Bag selection', lambda: any('▶Bag' in row for row in text().splitlines()),
              lambda _: press('down', 20), limit=10)
        press('a', 90)
        until('items pocket', lambda: 'Rare Candy' in text(), lambda _: press('left'), limit=8)
        press('a'); press('a')
        until('Candy party menu', lambda: 'Cancel' in text() and 'Egg' in text(), dialog)
        candy = byte('wCurItem')
        assert item_count(candy) == 2
        select_party(3)
        def learn(t):
            if 'Tackle' in t and 'Growl' in t and 'Leer' in t and 'Scratch' in t:
                press('a')  # Replace the first slot.
            elif 'Ember' in t and 'Growl' in t and 'Leer' in t and 'Scratch' in t:
                # The wide fixture also has Annihilape's evolution move,
                # Shadow Claw. Replace Growl while preserving native Ember.
                rows = t.splitlines()
                target = next(i for i, row in enumerate(rows) if 'Growl' in row)
                cursor = next((i for i, row in enumerate(rows) if '▶' in row), None)
                assert cursor is not None, t
                press('down' if cursor < target else 'up' if cursor > target else 'a')
            elif all(name in t for name in ('Ember', 'Shadow Claw', 'Leer', 'Scratch')):
                press('b')  # Decline the evolved fixture's level-20 Growl.
            else: dialog(t)
        until('level 20 learning and evolution',
              lambda: party()[2]['species'] == species and item_count(candy) == 1, learn)
        tick(90)
        evolved = party()[2]
        assert evolved['level'] == 20 and move in evolved['moves'], evolved
        checkpoint('learned-and-evolved-wide')
        assert 'Rare Candy' in text(), text()
        press('a'); press('a')
        until('second Candy party menu', lambda: 'Cancel' in text() and 'Egg' in text(), dialog)
        select_party(3)
        until('level 21 return evolution',
              lambda: party()[2]['species'] == 0x123 and item_count(candy) == 0, dialog)
        until('items after Candy use', lambda: 'Cancel' in text() and 'Egg' not in text(), lambda _: press('b'))
        press('b'); press('b')
        assert party()[2]['level'] == 21 and move in party()[2]['moves'], party()
        checkpoint('evolved-back')
        # Walk real overworld steps until the ordinary hatch counter expires.
        # The fixture does not change egg cycles or the hatching routines.
        press('down', 45, 15)
        def walking(t):
            if byte('wScriptMode') or 'nickname' in t.lower() or 'Huh?' in t or 'hatched' in t:
                dialog(t)
            elif byte('wPlayerMapX') >= 6:
                press('left', 45, 15)
            else:
                press('right', 45, 15)
        until('egg hatching', lambda: not party()[3]['form'] & 0x40, walking, limit=5600)
        until('hatch animation and announcement', lambda: 'out of its Egg!' in text(), dialog)
        checkpoint('hatch-animation')
        close_event()
        assert party()[3]['species'] == species and party()[3]['level'] == 1, party()
        checkpoint('hatched-wide-egg')
        before_final = party()
        if byte('wPlayerMapX') == 5: press('right', 45, 15)
        assert byte('wPlayerMapX') == 6
        press('up', 45, 15)
        fixture_event()
        until('final PC choice', lambda: 'Turn Off' in text(), dialog)
        press('a', 180)
        until('final PC storage', lambda: byte('wBillsPC_CursorPos') == 0x12, dialog)
        pc_cursor(0x31)  # Store the level-20 wide species with native Ember.
        press('a'); press('a', 180)
        until('final PC deposit', lambda: byte('wPartyCount') == 3, dialog)
        assert party() == [before_final[i] for i in (0, 2, 3)]
        press('b'); press('b', 120)
        until('final PC exit', lambda: 'Turn Off' in text(), lambda _: press('b'))
        close_event()
        checkpoint('boxed-before-reload')
        save_reload('lifecycle-')
        press('up', 45, 15)
        fixture_event()
        until('reloaded PC choice', lambda: 'Turn Off' in text(), dialog)
        press('a', 180)
        until('reloaded PC storage', lambda: byte('wBillsPC_CursorPos') == 0x12, dialog)
        press('a')
        assert 'Withdraw' in text(), text()
        press('a', 180)
        until('reloaded PC withdrawal', lambda: byte('wPartyCount') == 4, dialog)
        assert party() == [before_final[i] for i in (0, 2, 3, 1)], (before_final, party())
        checkpoint('boxed-native-ids-restored')
        evidence['frames'] = frames
        evidence['result'] = 'passed'
        (args.output / 'summary.json').write_text(json.dumps(evidence, indent=2)+'\n')
        print('PASS fresh game, wild/trainer battles, capture, PC/daycare, native move learning, two evolutions, hatching and two cold reloads; joypad only')
    except BaseException as error:
        if p:
            p.screen.image.save(str(args.output / 'failure.png'))
            (args.output / 'failure.txt').write_text(str(error)+'\n'+text()+'\n'+repr(party()))
        raise
    finally:
        if p: p.stop(save=False)


if __name__ == '__main__': main()
