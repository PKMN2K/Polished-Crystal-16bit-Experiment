"""Breed, collect and hatch native identities through the real daycare UI.

Requires native_breeding_test=1, NATIVE_TEST_SPECIES=767, NATIVE_TEST_MOVE=64769.
No hooks, memory/register writes, ROM patches, save states or shortened timers.
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
    ap.add_argument('--output', type=Path, default=Path('build/test-results/breeding'))
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    syms = {}
    for line in args.rom.with_suffix('.sym').read_text().splitlines():
        fields = line.split()
        if len(fields) == 2 and ':' in fields[0]:
            syms[fields[1]] = tuple(int(x, 16) for x in fields[0].split(':'))
    assert 'NativeBreedingScenario' in syms, 'build with native_breeding_test=1'
    rom = args.rom.read_bytes()
    def constant(label):
        bank, at = syms[label]
        start = bank * 0x4000 + at % 0x4000
        return int.from_bytes(rom[start:start+2], 'little')
    species, move = constant('NativeWideTestIdentity'), constant('NativeWideMoveTestIdentity')
    assert (species, move) == (0x02ff, 0xfd01)
    chars = {}
    for line in (Path(__file__).resolve().parents[2] / 'constants/charmap.asm').read_text().splitlines():
        match = re.match(r'\s*charmap "([^"]+)",\s+\$([0-9a-f]+)', line, re.I)
        if match and len(match[1]) == 1: chars[int(match[2], 16)] = match[1]
    p = None
    frames = 0
    evidence = {'species': hex(species), 'move': hex(move), 'input': 'joypad only', 'checkpoints': []}
    def boot(ram=None, rtc=None):
        game = PyBoy(BytesIO(rom), ram_file=ram, rtc_file=rtc, window='null',
                     sound_emulated=False, cgb=True, log_level='ERROR')
        game.set_emulation_speed(0)
        return game
    def read(label, size=1, offset=0):
        bank, at = syms[label]; at += offset
        if 0xd000 <= at < 0xe000 or 0xa000 <= at < 0xc000:
            return bytes(p.memory[bank, at:at+size])
        return bytes(p.memory[at:at+size])
    def byte(label): return read(label)[0]
    def word(label): return int.from_bytes(read(label, 2), 'little')
    def native(table, handle):
        return int.from_bytes(read(table, 2, (handle-1)*2), 'little') if handle else 0
    def mon(prefix):
        return {'species': native('wPokemonIndexTableEntries', byte(prefix+'Species')),
                'form': byte(prefix+'Form'), 'level': byte(prefix+'Level'),
                'exp': int.from_bytes(read(prefix+'Exp', 3), 'big'),
                'id': read(prefix+'ID', 2).hex(), 'dvs': read(prefix+'DVs', 3).hex(),
                'personality': byte(prefix+'Personality'), 'ball': byte(prefix+'CaughtBall') & 31,
                'moves': [native('wMoveIndexTableEntries', h) for h in read(prefix+'Moves', 4)],
                'pp': list(read(prefix+'PP', 4))}
    def party(): return [mon(f'wPartyMon{i}') for i in range(1, byte('wPartyCount')+1)]
    def parents():
        return [mon(f'wBreedMon{i}') if byte(flag) & 1 else None
                for i, flag in ((1, 'wDayCareMan'), (2, 'wDayCareLady'))]
    def position(): return (byte('wPlayerMapX'), byte('wPlayerMapY'))
    def daycare(): return (byte('wMapGroup'), byte('wMapNumber')) == (11, 3)
    def route(): return (byte('wMapGroup'), byte('wMapNumber')) == (11, 1)
    def text():
        tiles = read('wTilemap', 360)
        return '\n'.join(''.join(chars.get(x, ' ') for x in tiles[row:row+20]) for row in range(0, 360, 20))
    def tick(n=60):
        nonlocal frames
        assert frames + n <= 650000, 'breeding frame budget exceeded'
        p.tick(n, True, False); frames += n
    def press(key, n=60, hold=3):
        p.button(key, hold); tick(n)
    def until(description, predicate, action, limit=400):
        for _ in range(limit):
            if predicate(): return
            action(text())
        raise AssertionError(description + ' timed out at ' + str(position()) + '\n' + text())
    def dialog(t):
        if 'Shift' in t and 'End' in t:
            press('start', 30); press('a')
        elif 'nickname' in t.lower() and 'Yes' in t and 'No' in t: press('b')
        else: press('a')
    def initial(t):
        if 'Natures' in t and 'Abilities' in t: press('start')
        else: dialog(t)
    def close_event():
        until('NPC dialogue closes', lambda: byte('wScriptMode') == 0, lambda _: press('b'))
        tick(90)
    def walk(x, y):
        def step(_):
            px, py = position()
            press(('right' if px < x else 'left') if px != x else
                  ('down' if py < y else 'up'), 45, 15)
        until('walk to ' + str((x, y)), lambda: position() == (x, y), step, limit=40)
    def checkpoint(name):
        p.screen.image.save(str(args.output / (name + '.png')))
        evidence['checkpoints'].append({'name': name, 'frame': frames, 'party': party(),
                                        'parents': parents(), 'position': position()})
        print('PASS', name, 'frame', frames, flush=True)
    def save_reload(tag):
        nonlocal p
        assert daycare() and position() == (9, 9)
        press('start', 90)
        until('Save selection', lambda: any('▶Save' in row for row in text().splitlines()),
              lambda _: press('down', 20), limit=10)
        press('a')
        until('saved message', lambda: 'saved' in text().lower() and 'the game.' in text().lower(), dialog)
        tick(180)
        before, deposited = party(), parents()
        checkpoint(tag + '-saved')
        ram, rtc = BytesIO(), BytesIO()
        p.stop(save=True, ram_file=ram, rtc_file=rtc); p = None
        (args.output / (tag + '.ram')).write_bytes(ram.getvalue())
        (args.output / (tag + '.rtc')).write_bytes(rtc.getvalue())
        assert len(ram.getvalue()) == 32768
        ram.seek(0); rtc.seek(0)
        p = boot(ram, rtc)
        saw_continue = False
        def continuing(t):
            nonlocal saw_continue
            if 'Continue' in t: saw_continue = True
            if daycare() and 'Badges' not in t: press('down', 45, 15)
            else: press('a')
        until('cold Continue and movement', lambda: daycare() and position() == (9, 10), continuing)
        tick(180)
        assert saw_continue
        assert word('wPokemonDataFormat') == 0x16bc and word('wMoveDataFormat') == 0x16bd
        assert party() == before, ('party changed after cold Continue', before, party())
        for old, new in zip(deposited, parents()):
            if old is None: assert new is None
            else:
                # The required real overworld step awards one daycare EXP.
                assert new['exp'] == old['exp'] + 1, (old, new)
                assert {k: v for k, v in new.items() if k != 'exp'} == {k: v for k, v in old.items() if k != 'exp'}
        checkpoint(tag + '-cold-continue')
        walk(9, 9)
    try:
        p = boot()
        until('New Game', lambda: (byte('wMapGroup'), byte('wMapNumber')) == (24, 5), initial)
        tick(180)
        assert byte('wPartyCount') == 0
        press('up', 45, 15); press('a')
        until('daycare fixture entrance', daycare, dialog)
        tick(180); close_event()
        gifted = party()
        assert [m['species'] for m in gifted] == [species, 132, 25], gifted
        assert gifted[0]['moves'] == [33, 45, move, 0] and gifted[0]['ball'] == 2
        checkpoint('parents-ready')
        for x, y, facing, count, label in ((6, 8, 'up', 2, 'wide-parent-deposited'),
                                           (10, 7, 'left', 1, 'ditto-deposited')):
            walk(x, 9); walk(x, y); press(facing, 20); press('a')
            until(label, lambda: byte('wPartyCount') == count, dialog)
            close_event()
            checkpoint(label)
            walk(x, 9)
        for old, new in zip(gifted[:2], parents()):
            assert new['exp'] >= old['exp']
            assert {k: v for k, v in new.items() if k != 'exp'} == {k: v for k, v in old.items() if k != 'exp'}, (old, new)
        assert byte('wDayCareMan') & 0x20 and byte('wBreedingCompatibility') > 0
        walk(9, 9); save_reload('parents')
        direction = 'left'
        def stroll(_):
            nonlocal direction
            x, y = position()
            assert daycare() and y == 9, position()
            if x <= 6: direction = 'right'
            elif x >= 9: direction = 'left'
            press(direction, 45, 15)
        until('ordinary breeding steps', lambda: byte('wDayCareMan') & 0x40, stroll, limit=6000)
        checkpoint('egg-ready')
        assert byte('wPartyCount') == 1
        # The front door opens into the fenced pen. The west door reaches
        # Grandpa on the public side of Route 34.
        walk(5, 9); walk(5, 8); press('left', 90, 15)
        until('exit to Route 34', route, lambda _: press('left', 45, 15), limit=10)
        tick(180)
        walk(13, 18); walk(13, 20); walk(14, 20); press('up', 20); press('a')
        until('collect bred Egg', lambda: byte('wPartyCount') == 2, dialog)
        close_event()
        egg = party()[1]
        assert egg['species'] == species and egg['form'] & 0x40 and egg['level'] == 1, egg
        assert egg['moves'] == [33, move, 0, 0] and egg['pp'] == [35, 25, 0, 0], egg
        assert egg['ball'] == gifted[0]['ball'] and egg['id'] == gifted[0]['id'], egg
        assert byte('wPartyMon2Happiness') > 0
        checkpoint('bred-egg-collected')
        walk(13, 20); walk(13, 18); walk(14, 18); press('right', 90, 15)
        until('return inside daycare', daycare, lambda _: press('right', 45, 15), limit=10)
        tick(180)
        walk(5, 9)
        for x, y, facing, count, flag in ((6, 8, 'up', 3, 'wDayCareMan'),
                                        (10, 7, 'left', 4, 'wDayCareLady')):
            walk(x, 9); walk(x, y); press(facing, 20); press('a')
            until('withdraw parent', lambda: byte('wPartyCount') == count, dialog)
            close_event()
            assert not byte(flag) & 1
            walk(x, 9)
        for old, new in zip(gifted[:2], party()[2:]):
            assert all(new[k] == old[k] for k in ('species', 'form', 'id', 'dvs', 'personality', 'ball', 'moves', 'pp')), (old, new)
            assert new['level'] >= old['level'] and new['exp'] >= old['exp']
        checkpoint('parents-withdrawn')
        walk(9, 9); save_reload('egg')
        hatch_cycles = byte('wPartyMon2Happiness')
        evidence['initial_hatch_cycles'] = hatch_cycles
        until('ordinary Egg hatching steps', lambda: not byte('wPartyMon2Form') & 0x40,
              lambda t: dialog(t) if byte('wScriptMode') or 'Huh?' in t else stroll(t), limit=8000)
        until('complete hatch animation', lambda: 'out of its Egg!' in text(), dialog)
        checkpoint('bred-egg-hatched')
        close_event()
        child = party()[1]
        assert child['species'] == species and child['form'] == egg['form'] & ~0x40
        assert all(child[k] == egg[k] for k in ('level', 'id', 'dvs', 'personality', 'ball', 'moves', 'pp')), (egg, child)
        walk(9, 9)
        save_reload('hatched')
        evidence['frames'], evidence['result'] = frames, 'passed'
        (args.output / 'summary.json').write_text(json.dumps(evidence, indent=2) + '\n')
        print('PASS daycare deposits, natural breeding, Egg collection, inherited native move/ball, parent withdrawal, natural hatching and three cold reloads; joypad only')
    except BaseException as error:
        if p:
            p.screen.image.save(str(args.output / 'failure.png'))
            (args.output / 'failure.txt').write_text(str(error) + '\n' + text() + '\n' + repr(party()) + '\n' + repr(parents()))
        raise
    finally:
        if p: p.stop(save=False)


if __name__ == '__main__': main()
