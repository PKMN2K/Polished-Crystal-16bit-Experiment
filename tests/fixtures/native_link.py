"""Drive two CGBs over SameBoy's serial cable with joypad input only.

Requires native_link_test=1, NATIVE_TEST_SPECIES=767, NATIVE_TEST_MOVE=64769.
No CPU hooks, memory/register writes, ROM patches or emulator save states.
"""
import argparse
import ctypes as C
import json
from pathlib import Path
import re
from PIL import Image


class LinkedGame:
    KEYS = {key: 1 << i for i, key in enumerate(('right', 'left', 'up', 'down', 'a', 'b', 'select', 'start'))}

    def __init__(self, rom, core, boot, output):
        self.output, self.frames = output, 0
        output.mkdir(parents=True, exist_ok=True)
        self.syms = {}
        for line in rom.with_suffix('.sym').read_text().splitlines():
            fields = line.split()
            if len(fields) == 2 and ':' in fields[0]:
                self.syms[fields[1]] = tuple(int(x, 16) for x in fields[0].split(':'))
        assert 'NativeLinkScenario' in self.syms, 'build with native_link_test=1'
        self.chars = {}
        for line in (Path(__file__).resolve().parents[2] / 'constants/charmap.asm').read_text().splitlines():
            match = re.match(r'\s*charmap "([^"]+)",\s+\$([0-9a-f]+)', line, re.I)
            if match and len(match[1]) == 1: self.chars[int(match[2], 16)] = match[1]
        self.maps = {}; group = number = 0
        for line in (Path(__file__).resolve().parents[2] / 'constants/map_constants.asm').read_text().splitlines():
            if re.match(r'\s+newgroup\b', line): group += 1; number = 0
            match = re.match(r'\s+map_const (\w+),', line)
            if match: number += 1; self.maps[match[1]] = (group, number)
        self.lib = C.CDLL(str(core.resolve()))
        def api(name, result, *params):
            fn = getattr(self.lib, 'pair_' + name)
            fn.restype, fn.argtypes = result, params
            return fn
        self.new = api('new', C.c_void_p, C.c_char_p, C.c_char_p)
        self.free = api('free', None, C.c_void_p)
        self.advance = api('tick', None, C.c_void_p, C.c_uint)
        self.keys = api('keys', None, C.c_void_p, C.c_uint, C.c_uint)
        self.peek = api('read', C.c_uint8, C.c_void_p, C.c_uint, C.c_uint, C.c_uint)
        self.pixels = api('pixels', C.c_void_p, C.c_void_p, C.c_uint)
        self.bits = api('bits', C.c_uint64, C.c_void_p, C.c_uint)
        self.collisions = api('collisions', C.c_uint64, C.c_void_p, C.c_uint)
        self.pc = api('pc', C.c_uint, C.c_void_p, C.c_uint)
        self.save = api('save', C.c_int, C.c_void_p, C.c_uint, C.c_char_p)
        self.load = api('load', C.c_int, C.c_void_p, C.c_uint, C.c_char_p)
        self.paths = (str(rom.resolve()).encode(), str(boot.resolve()).encode())
        self.pair = self.new(*self.paths)
        assert self.pair, 'SameBoy failed to load ROM/boot ROM'
        self.evidence = {'passed': False, 'input': 'joypad only', 'transport': 'SameBoy serial bit callbacks',
                         'power_on_offset_8mhz_ticks': 35112, 'checkpoints': []}

    def read(self, peer, label, size=1, offset=0):
        bank, address = self.syms[label]
        return bytes(self.peek(self.pair, peer, bank, address + offset + i) for i in range(size))

    def byte(self, peer, label): return self.read(peer, label)[0]
    def word(self, peer, label): return int.from_bytes(self.read(peer, label, 2), 'little')
    def native(self, peer, table, handle):
        return int.from_bytes(self.read(peer, table, 2, (handle - 1) * 2), 'little') if handle else 0

    def party(self, peer):
        return [{'species': self.native(peer, 'wPokemonIndexTableEntries', self.byte(peer, f'wPartyMon{i}Species')),
                 'level': self.byte(peer, f'wPartyMon{i}Level'),
                 'form': self.byte(peer, f'wPartyMon{i}Form'),
                 'exp': int.from_bytes(self.read(peer, f'wPartyMon{i}Exp', 3), 'big'),
                 'id': self.read(peer, f'wPartyMon{i}ID', 2).hex(),
                 'dvs': self.read(peer, f'wPartyMon{i}DVs', 3).hex(),
                 'moves': [self.native(peer, 'wMoveIndexTableEntries', h) for h in self.read(peer, f'wPartyMon{i}Moves', 4)],
                 'pp': list(self.read(peer, f'wPartyMon{i}PP', 4))}
                for i in range(1, self.byte(peer, 'wPartyCount') + 1)]

    def text(self, peer):
        tiles = self.read(peer, 'wTilemap', 360)
        return '\n'.join(''.join(self.chars.get(x, ' ') for x in tiles[row:row+20]) for row in range(0, 360, 20))

    def in_map(self, peer, name):
        return (self.byte(peer, 'wMapGroup'), self.byte(peer, 'wMapNumber')) == self.maps[name]

    def tick(self, n=60):
        assert self.frames + n <= 200000, 'linked scenario frame budget exceeded'
        self.advance(self.pair, n); self.frames += n

    def press(self, peer, key, n=60, hold=3):
        self.keys(self.pair, peer, self.KEYS[key]); self.tick(hold)
        self.keys(self.pair, peer, 0); self.tick(n - hold)

    def walk(self, peer, axis, target):
        label = 'wPlayerMap' + axis.upper()
        def step():
            positive = self.byte(peer, label) < target
            self.press(peer, ('right' if positive else 'left') if axis == 'x' else ('down' if positive else 'up'), 24)
        self.until('walk to ' + label + '=' + str(target), lambda: self.byte(peer, label) == target, step, limit=16)

    def use_link_machine(self):
        for peer in range(2):
            right = self.byte(peer, 'hSerialConnectionStatus') == 1
            self.walk(peer, 'x', 10 if right else 7)
            self.walk(peer, 'y', 8)
            self.press(peer, 'left' if right else 'right', 24)
            self.press(peer, 'a')

    def leave_link_room(self):
        for peer in range(2):
            self.walk(peer, 'y', 10); self.walk(peer, 'x', 8)
        def leave():
            for peer in range(2):
                if not self.in_map(peer, 'POKECENTER_2F'): self.press(peer, 'down', 45, 8)
            self.tick(30)
        self.until('return to reception', lambda: all(self.in_map(i, 'POKECENTER_2F') for i in range(2)), leave, limit=40)
        self.until('reception exit movement', lambda: all(self.byte(i, 'wScriptMode') == 0 for i in range(2)), lambda: self.tick(60), limit=40)
        self.tick(120)

    def dialog(self, peer, initial=False):
        text = self.text(peer)
        if initial and 'Natures' in text and 'Abilities' in text: self.press(peer, 'start')
        elif 'Shift' in text and 'End' in text:
            self.press(peer, 'start', 30); self.press(peer, 'a')
        elif 'nickname' in text.lower() and 'Yes' in text: self.press(peer, 'b')
        else: self.press(peer, 'a')

    def until(self, description, predicate, action, limit=400):
        for attempt in range(limit):
            if predicate(): return
            if attempt and attempt % 50 == 0:
                self.checkpoint(f'progress-{self.frames}')
                print(description, self.frames, '\n--- peer ---\n'.join(self.text(i) for i in range(2)), flush=True)
            action()
        self.checkpoint('failure')
        raise AssertionError(description + ' timed out\n' + '\n--- peer ---\n'.join(self.text(i) for i in range(2)))

    def checkpoint(self, name):
        states = []
        for i in range(2):
            Image.frombytes('RGBA', (160, 144), C.string_at(self.pixels(self.pair, i), 160*144*4)).save(self.output / f'{name}-{i}.png')
            states.append({'party': self.party(i), 'serial_bits': self.bits(self.pair, i),
                           'clock_collision_warnings': self.collisions(self.pair, i),
                           'connection': self.byte(i, 'hSerialConnectionStatus'), 'pc': hex(self.pc(self.pair, i)),
                           'map': [self.byte(i, x) for x in ('wMapGroup', 'wMapNumber', 'wPlayerMapX', 'wPlayerMapY')]})
        self.evidence['checkpoints'].append({'name': name, 'frame': self.frames, 'peers': states})
        (self.output / 'results.json').write_text(json.dumps(self.evidence, indent=2) + '\n')
        print(name, self.frames, states, flush=True)

    def close(self): self.free(self.pair); self.pair = None


def battle_and_reload(game, args, expected):
    for peer in (1, 0):
        game.walk(peer, 'y', 8)
        game.walk(peer, 'x', 13)
        game.walk(peer, 'y', 7)
        game.press(peer, 'up', 24); game.press(peer, 'a')
    def battle_reception():
        for peer in (1, 0):
            if not game.in_map(peer, 'COLOSSEUM'): game.dialog(peer)
    game.until('Colosseum admission', lambda: all(game.in_map(i, 'COLOSSEUM') for i in range(2)), battle_reception)
    game.tick(180)
    game.checkpoint('battle-room')
    assert [game.byte(i, 'hSerialConnectionStatus') for i in range(2)] == [1, 2]
    game.use_link_machine()
    game.until('linked battle start', lambda: all('Fight' in game.text(i) and 'Bag' in game.text(i) for i in range(2)),
               lambda: [game.dialog(i) for i in range(2) if 'Fight' not in game.text(i)])
    game.checkpoint('battle-started')
    # Switch both players to the traded wide species through the battle UI.
    for peer in range(2):
        game.press(peer, 'right'); game.press(peer, 'a')
        game.until('party menu', lambda: 'Choose a' in game.text(peer), lambda: game.dialog(peer))
        game.until('wide party slot', lambda: game.byte(peer, 'wMenuCursorY') == 2, lambda: game.press(peer, 'down', 24), limit=6)
        game.press(peer, 'a'); game.press(peer, 'a')
    seen_wide, seen_ember, spent_wide_pp = set(), set(), set()
    def fight():
        for peer in range(2):
            if game.byte(peer, 'wBattleMode') == 0:
                # One peer can return first. Pressing A there would start
                # another battle while the other peer is still returning.
                game.tick(30)
                continue
            text = game.text(peer)
            if game.word(peer, 'wBattleMonNativeSpecies') == 0x02ff:
                seen_wide.add(peer)
                for slot, handle in enumerate(game.read(peer, 'wBattleMonMoves', 4)):
                    if game.native(peer, 'wMoveIndexTableEntries', handle) == 0xfd01:
                        if game.read(peer, 'wBattleMonPP', 4)[slot] & 63 < 25: spent_wide_pp.add(peer)
            if 'Ember!' in text: seen_ember.add(peer)
            if 'Ember' in text and 'Tackle' in text:
                rows = text.splitlines()
                target = next(n for n, row in enumerate(rows) if 'Ember' in row)
                cursor = next((n for n, row in enumerate(rows) if '▶' in row), None)
                assert cursor is not None, text
                game.press(peer, 'down' if cursor < target else 'up' if cursor > target else 'a')
            elif 'Which' in text and 'Cancel' in text:
                slot = next(i for i in range(1, 3) if any(game.read(peer, f'wPartyMon{i}HP', 2)))
                game.press(peer, 'a' if game.byte(peer, 'wMenuCursorY') == slot else 'down')
            else: game.dialog(peer)
    game.until('complete linked battle', lambda: all(game.byte(i, 'wBattleMode') == 0 and game.byte(i, 'wScriptMode') == 0 for i in range(2)), fight, limit=500)
    assert seen_wide == seen_ember == spent_wide_pp == {0, 1}, (seen_wide, seen_ember, spent_wide_pp)
    game.evidence['both_peers_used_native_ember'] = True
    assert {game.byte(i, 'wBattleResult') & 15 for i in range(2)} == {0, 1}
    assert [game.party(i) for i in range(2)] == expected
    records = [[int.from_bytes(game.read(i, label, 2), 'big') for label in
                ('sLinkBattleWins', 'sLinkBattleLosses', 'sLinkBattleDraws')] for i in range(2)]
    assert sorted(records) == [[0, 1, 0], [1, 0, 0]], records
    game.evidence['battle_records'] = records
    game.checkpoint('battle-completed')
    game.leave_link_room()
    for peer in range(2):
        game.press(peer, 'start', 90)
        game.until('Save selection', lambda: '▶Save' in game.text(peer), lambda: game.press(peer, 'down', 24), limit=10)
        game.press(peer, 'a')
        game.until('game saved', lambda: 'saved' in game.text(peer).lower() and 'the game.' in game.text(peer).lower(), lambda: game.dialog(peer))
        game.tick(180)
        assert game.save(game.pair, peer, str(args.output / f'peer-{peer}.sav').encode()) == 0
    game.checkpoint('saved')
    game.free(game.pair)
    game.pair = game.new(*game.paths)
    assert game.pair
    for peer in range(2):
        assert game.load(game.pair, peer, str(args.output / f'peer-{peer}.sav').encode()) == 0
    saw_continue = set()
    def continuing():
        for peer in range(2):
            text = game.text(peer)
            if 'Continue' in text: saw_continue.add(peer)
            if game.in_map(peer, 'POKECENTER_2F') and 'Badges' not in text:
                if game.byte(peer, 'wPlayerMapY') != 8: game.press(peer, 'down', 24)
            else: game.dialog(peer)
    game.until('cold Continue and movement', lambda: all(game.in_map(i, 'POKECENTER_2F') and game.byte(i, 'wPlayerMapY') == 8 for i in range(2)), continuing)
    assert saw_continue == {0, 1}
    assert [game.party(i) for i in range(2)] == expected
    for peer in range(2):
        assert game.word(peer, 'wPokemonDataFormat') == 0x16bc
        assert game.word(peer, 'wMoveDataFormat') == 0x16bd
        assert [int.from_bytes(game.read(peer, label, 2), 'big') for label in
                ('sLinkBattleWins', 'sLinkBattleLosses', 'sLinkBattleDraws')] == records[peer]
    game.checkpoint('cold-continue')
    game.evidence['passed'] = True
    (args.output / 'results.json').write_text(json.dumps(game.evidence, indent=2) + '\n')
    print('PASS: linked trade, full animations, wide-move battle, saves and cold Continue', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    parser.add_argument('--core', type=Path, default=Path('build/link_pair.so'))
    parser.add_argument('--boot', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path('build/test-results/link'))
    args = parser.parse_args()
    game = LinkedGame(args.rom, args.core, args.boot, args.output)
    try:
        def new_games():
            for peer in range(2):
                if not game.in_map(peer, 'PLAYERS_HOUSE_2F'): game.dialog(peer, True)
        game.until('New Games', lambda: all(game.in_map(i, 'PLAYERS_HOUSE_2F') for i in range(2)), new_games)
        for peer in range(2):
            game.tick(180)
            assert game.byte(peer, 'wPartyCount') == 0
            game.press(peer, 'up', 45, 15); game.press(peer, 'a')
            game.until('peer choice', lambda: 'Prepare peer A?' in game.text(peer) and 'Yes' in game.text(peer), lambda: game.dialog(peer))
            game.press(peer, 'a' if peer == 0 else 'b')
            game.until('Cable Club', lambda: game.in_map(peer, 'POKECENTER_2F'), lambda: game.dialog(peer))
            game.tick(180)
        game.checkpoint('prepared')
        for peer in range(2):
            game.press(peer, 'up', 20); game.press(peer, 'a')
        def reception():
            for peer in range(2):
                if not game.in_map(peer, 'TRADE_CENTER'): game.dialog(peer)
        game.until('Trade Center admission', lambda: all(game.in_map(i, 'TRADE_CENTER') for i in range(2)), reception)
        game.tick(180)
        game.checkpoint('trade-room')
        assert {game.byte(i, 'hSerialConnectionStatus') for i in range(2)} == {1, 2}
        before = [game.party(i) for i in range(2)]
        assert before[0][1]['species'] == before[1][0]['species'] == 0x02ff
        assert before[0][1]['id'] != before[1][0]['id']
        handles = [game.byte(0, 'wPartyMon2Species'), game.byte(1, 'wPartyMon1Species')]
        assert handles[0] != handles[1], handles
        game.evidence['independent_wide_species_handles'] = handles
        game.use_link_machine()
        game.until('trade party menus', lambda: all('Cancel' in game.text(i) for i in range(2)), lambda: game.tick(60))
        game.checkpoint('trade-parties')
        for peer, slot in enumerate((2, 1)):
            game.until('offered party slot', lambda: game.byte(peer, 'wMenuCursorY') == slot, lambda: game.press(peer, 'down', 24), limit=6)
            game.press(peer, 'a'); game.press(peer, 'right'); game.press(peer, 'a')
        game.until('trade confirmation', lambda: all('Trade' in game.text(i) and 'Cancel' in game.text(i) and 'for' in game.text(i) for i in range(2)), lambda: game.tick(60))
        game.checkpoint('trade-confirmation')
        for peer in range(2): game.press(peer, 'a')
        expected = [[before[0][0], before[1][0]], [before[1][1], before[0][1]]]
        def traded():
            return all(game.party(i) == expected[i] and 'Cancel' in game.text(i) and 'Summary' not in game.text(i) for i in range(2))
        animation = [set(), set()]
        def animate():
            for i in range(2):
                if game.byte(i, 'wPartyCount') == 1: animation[i].add(game.word(i, 'wTradeAnimPointer'))
            game.tick(30)
        game.until('full trade and animation', traded, animate, limit=300)
        assert all(len(seen) >= 10 for seen in animation), animation
        game.evidence['observed_animation_commands'] = [len(seen) for seen in animation]
        game.checkpoint('traded')
        for peer in range(2):
            assert game.save(game.pair, peer, str(args.output / f'post-trade-peer-{peer}.sav').encode()) == 0
        for peer in range(2):
            game.until('Cancel trade menu', lambda: '▶Cancel' in game.text(peer), lambda: game.press(peer, 'up', 24), limit=8)
            game.press(peer, 'a')
        game.until('return to trade room', lambda: all(game.byte(i, 'wScriptMode') == 0 for i in range(2)), lambda: game.tick(60))
        game.tick(120)
        game.leave_link_room()
        game.checkpoint('trade-exited')
        battle_and_reload(game, args, expected)
    except BaseException:
        game.checkpoint('failure')
        raise
    finally:
        game.close()


if __name__ == '__main__': main()
