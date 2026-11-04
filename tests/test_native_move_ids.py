"""Native move allocation, lookups, learning, persistence and remapping on real CPU code."""
import argparse
from pathlib import Path
from pyboy import PyBoy


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('rom', type=Path)
    rom = ap.parse_args().rom
    syms = {}
    for line in rom.with_suffix('.sym').read_text().splitlines():
        fields = line.split()
        if len(fields) == 2 and ':' in fields[0]:
            syms[fields[1]] = tuple(int(x, 16) for x in fields[0].split(':'))
    data = rom.read_bytes()
    def addr(label): return syms[label][1]
    def rb(label, n, offset=0):
        bank, at = syms[label]
        at = bank*0x4000 + at%0x4000 + offset
        return data[at:at+n]
    wide = int.from_bytes(rb('NativeWideMoveTestIdentity', 2), 'little') if 'NativeWideMoveTestIdentity' in syms else None
    alias = int.from_bytes(rb('NativeWideMoveTestAlias', 2), 'little') if wide else 33
    p = PyBoy(str(rom), window='null', sound_emulated=False, cgb=True, log_level='ERROR')
    m, r = p.memory, p.register_file
    def write(label, values):
        at = addr(label)
        if isinstance(values, int): m[at] = values
        else: m[at:at+len(values)] = list(values)
    def read(label, n=1): return bytes(m[addr(label):addr(label)+n])
    def call(label, a=0, bc=0, de=0xc380, hl=0xc280, stop=None):
        observed = []
        if stop:
            p.hook_register(*syms[stop], lambda _: observed.append(True), None)
        bank, target = syms[label]; bank = bank or 1
        m[0x2000] = bank; write('hROMBank', bank)
        m[0xc100:0xc106] = [0xf3, 0xcd, target&255, target>>8, 0x18, 0xfe]
        r.A, r.B, r.C, r.D, r.E, r.HL = a, bc>>8, bc&255, de>>8, de&255, hl
        r.SP, r.PC = 0xc0ff, 0xc100
        for _ in range(80):
            p.tick(1, False, False)
            if observed or (r.PC, r.SP) == (0xc104, 0xc0ff): break
        if stop:
            p.hook_deregister(*syms[stop])
            assert observed, (label, 'did not reach', stop, hex(r.PC))
            return r.A
        assert (r.PC, r.SP) == (0xc104, 0xc0ff), (label, hex(r.PC), hex(r.SP), r.A, hex(r.HL))
        assert m[addr('hROMBank')] == bank and m[0xff70]&7 == 1, (label, 'bank leak')
        return r.A
    def index(handle):
        call('GetMoveIndexFromID', a=handle); return r.HL
    def handle(native): return call('GetMoveIDFromIndex', hl=native)
    def ids(label): return [index(x) for x in read(label, 4)]
    def reset():
        m[0xff50] = 1
        m[0xffff] = m[0xff0f] = m[0xff40] = 0
        m[0xc000:0xd000] = [0]*0x1000
        for bank in (1,2):
            m[0xff70] = bank; m[0xd000:0xe000] = [0]*0x1000
        m[0xff70] = 1
        # Keep SRAM initialized and the engine's nested SRAM bookkeeping valid.
        m[0x0000] = 10
        for bank in (0,1,2,3):
            m[0x4000] = bank; m[0xa000:0xc000] = [0]*0x2000
        m[0x0000] = 0
        write('wSRAMAccessCount', 1)
        call('InitializeNativeMoveDataForNewGame')
        assert read('wMoveDataFormat',2) == bytes((0xbd,0x16))
    try:
        reset()
        assert handle(0) == 0 and index(0) == 0
        # Force every move away from its numeric ID and compare all eight properties.
        handle(200)
        write('wInitialOptions', 1 << 7)  # PSS_OPT
        abnormal = set()
        for offset in range(0, 128, 2):
            move = int.from_bytes(rb('AbnormalContactMoves', 2, offset), 'little')
            if move == 0xffff: break
            abnormal.add(move)
        else: raise AssertionError('missing contact-list terminator')
        checks = 0
        for native in range(1,256):
            h = handle(native)
            assert index(h) == native, ('identity', native, h)
            write('wCurPlayerMove', h)
            raw = rb('MoveData',8,(native-1)*8)
            for prop in range(8):
                actual = call('GetMoveProperty', a=h, hl=addr('Moves')+prop)
                assert actual == (h if prop == 0 else raw[prop]), ('property', native, prop, actual, raw[prop])
                checks += 1
            call('GetFixedMoveStruct', a=h, de=addr('wPlayerMoveStruct'))
            assert read('wPlayerMoveStruct',8) == bytes([h])+raw[1:], ('struct', native)
            call('_CheckContactMove')
            contact = native == 255 or raw[7] == (1 if native in abnormal else 0)
            assert bool(r.F & 0x10) == (not contact), ('contact', native)
            write('wNamedObjectIndex',h); call('GetMoveName')
            nameptr = int.from_bytes(rb('MoveNamePointers',2,(native-1)*2),'little')
            namebank=syms['MoveNamePointers'][0]
            expected=data[namebank*0x4000+nameptr%0x4000:][:13]
            assert read('wStringBuffer1',13)==expected, ('name',native)
            call('NativeGetMoveDescription', a=h)
            assert r.HL==int.from_bytes(rb('MoveDescriptionPointers',2,(native-1)*2),'little')
            call('LoadNativeMoveAnimation',a=h)
            assert read('wBattleAnimAddress',2)==rb('MoveAnimationPointers',2,(native-1)*2)
        print(f'PASS {checks} move properties plus 255 names, descriptions, structs, animations and contact classifications')
        reset()
        native_ids=[33,255,wide or 85,98]
        handles=[handle(x) for x in native_ids]
        assert handles[0] != 33
        write('wPartyCount',2)
        for prefix in ('wPartyMon1','wPartyMon2','wBreedMon1','wBreedMon2'):
            write(prefix+'Species',25);write(prefix+'Form',1);write(prefix+'Moves',handles)
        for n in range(1,256): handle(n)
        call('MoveTableGarbageCollection')
        for prefix in ('wPartyMon1','wPartyMon2','wBreedMon1','wBreedMon2'):
            assert ids(prefix+'Moves')==native_ids, ('gc',prefix)
        for suffix,save,load in [('', 'SavePokemonData','LoadPokemonData'),('Backup','SaveBackupPokemonData','LoadBackupPokemonData')]:
            call(save)
            m[0x0000]=10;m[0x4000]=syms['s'+suffix+'NativeMoves'][0]
            assert read('s'+suffix+'NativeMoves',8)==b''.join(x.to_bytes(2,'little') for x in native_ids)
            call('VerifyNativeMoveData',hl=addr('s'+suffix+'NativeMovesMagic'))
            assert r.F&0x80, ('save integrity',suffix)
            call('ClearMoveIndexTable')
            for n in range(120,145): handle(n)
            call(load)
            for prefix in ('wPartyMon1','wPartyMon2','wBreedMon1','wBreedMon2'):
                assert ids(prefix+'Moves')==native_ids, ('load',suffix,prefix)
            m[0x0000]=10;m[0x4000]=syms['s'+suffix+'NativeMoves'][0]
            m[addr('s'+suffix+'NativeMoves')+1]^=0x80
            call('VerifyNativeMoveData',hl=addr('s'+suffix+'NativeMovesMagic'))
            assert not r.F&0x80, ('corruption',suffix)
        print('PASS GC roots and primary/backup native move save-load remapping; corrupted sidecars rejected')
        reset()
        handles=[handle(x) for x in native_ids]
        write('wTempMonSpecies',25);write('wTempMonForm',1)
        write('wTempMonMoves',handles);write('wTempMonLevel',20)
        write('wTempMonNickname', [0x80]*10+[0x53]);write('wTempMonOT',[0x81]*7+[0x53])
        write('wCurSpecies',25);write('wCurForm',1);call('GetBaseData')
        call('CalcExpAtLevel',de=20*256)
        write('wTempMonExp',read('hProduct',4)[1:])
        call('EncodeTempMon')
        encoded=read('wEncodedTempMon',51)
        assert read('wEncodedTempMonMoves',4)==bytes(x&255 for x in native_ids)
        assert read('wEncodedTempMonMoveHighs',4)==bytes(x>>8 for x in native_ids)
        call('ClearMoveIndexTable')
        for n in range(120,145):handle(n)
        call('DecodeTempMon')
        assert not r.F&0x10, 'box decode carry'
        assert ids('wTempMonMoves')==native_ids
        assert read('wTempMonLevel')==bytes([20]), ('level',read('wTempMonLevel'))
        write('wEncodedTempMon', encoded)
        m[addr('wEncodedTempMonMoveHighs')]^=0x80
        call('DecodeTempMon');assert r.F&0x10, 'box high-byte corruption'
        print('PASS 51-byte PC record round trip with remapped handles, derived level and move-high integrity')
        # Every physical PC slot, including the slack, must map to disjoint
        # 51-byte records in all three SRAM sections of both database halves.
        reset()
        locations=[]
        for half in (1,2):
            slot=1
            for section in 'ABC':
                prefix=f'sBoxMons{half}{section}'
                count=(addr(prefix+'End')-addr(prefix+'Mons'))//51
                for offset in range(count):
                    call('OpenPokeDB',de=(half<<8)|slot)
                    assert r.HL==addr(prefix+'Mons')+offset*51, ('PC geometry',half,slot)
                    at=r.HL
                    m[at]=half;m[at+50]=slot
                    locations.append((half,slot,at))
                    call('CloseSRAM')
                    slot+=1
            assert slot==208, ('database capacity',half,slot)
        for half,slot,expected_at in locations:
            call('OpenPokeDB',de=(half<<8)|slot)
            assert r.HL==expected_at and (m[r.HL],m[r.HL+50])==(half,slot), ('PC overlap',half,slot)
            call('CloseSRAM')
        print('PASS all 414 physical PC records, retaining 400 usable Pokemon slots')

        reset()
        handle(200)
        write('wCurPartyLevel',1)
        call('FillMoves',bc=0x101,de=addr('wTempMonMoves'))
        assert ids('wTempMonMoves')==[wide or 33,0,0,0], ('FillMoves',ids('wTempMonMoves'))
        call('GetNextMove',bc=0x101,de=0)
        assert r.A==1 and index(r.D)==(wide or 33)
        write('wTempTMHM',1);h=call('GetTMHMMove')
        assert index(h)==int.from_bytes(rb('TMHMMoves',2),'little')
        write('wLinkMode',3);write('wLinkBattleRNCount',0)
        write('wLinkBattleRNs', [255 if wide else 32,0,0,0,0,0,0,0,0,0])
        h=call('GetRandomNativeMove');assert index(h)==(wide or 33)
        if wide:
            # The low byte collides with existing moves and the $0100+ control namespace.
            h=handle(wide);assert index(h)==wide
            call('GetMoveProperty',a=h,hl=addr('Moves')+2);assert r.A==40
            call('LoadNativeMoveAnimation',a=h);assert read('wBattleAnimAddress',2)==rb('MoveAnimationPointers',2,(alias-1)*2)
            for label,size in [('NativeMoveStreamFixture',None),('NativeMoveWordFixture',2)]:
                at=addr(label)
                for native in [0,33,255,wide]:
                    h=call('ReadMoveWordFromHL' if size else 'ReadMoveIDFromHL',a=syms[label][0],hl=at)
                    next_at=r.HL
                    assert index(h)==native,(label,native,h,index(h))
                    assert next_at-at==(size or (1 if native<255 else 3))
                    at=next_at
        print(f'PASS native learnset/TM/random readers; wide fixture {hex(wide) if wide else "not enabled"}')

        # Actual battle data/priority/damage commands, on both sides, with handles
        # deliberately different from native IDs. Fixtures include both a
        # physical contact move (Tackle) and a special non-contact move (Ember).
        damage_results = []
        for side in (0,1):
            for native in ([alias,wide] if wide else [33]):
                reset();handle(200)
                h=handle(native)
                write('wInitialOptions',1<<7)
                write('wBattleMode',1);write('wPartyCount',1);write('wOTPartyCount',1)
                write('wBattleMonNativeSpecies', bytes([25,0]))
                write('wEnemyMonNativeSpecies', bytes([133,0]))
                for prefix,species in [('wBattleMon',25),('wEnemyMon',133)]:
                    write(prefix+'Species',species);write(prefix+'Form',1)
                    write(prefix+'Level',50);write(prefix+'Moves',[h,0,0,0]);write(prefix+'PP',[35,0,0,0])
                    for stat in ['HP','MaxHP','Attack','Defense','SpclAtk','SpclDef','Speed']:
                        label=prefix+stat
                        if label not in syms:
                            label=prefix+{'SpclAtk':'SpAtk','SpclDef':'SpDef'}.get(stat,stat)
                        write(label,bytes([0,200 if stat in ('HP','MaxHP') else 100]))
                write('wPartyMon1Level',50);write('wOTPartyMon1Level',50)
                write('wPlayerStatLevels',[7]*7);write('wEnemyStatLevels',[7]*7)
                write('hBattleTurn',side)
                write('wCurPlayerMove' if side==0 else 'wCurEnemyMove',h)
                call('UpdateMoveData')
                move_struct='wPlayerMoveStruct' if side==0 else 'wEnemyMoveStruct'
                assert read(move_struct)[0]==h
                assert call('GetMovePriority')==0x80
                call('_CheckContactMove')
                assert bool(r.F & 0x10) == (alias == 52), ('wide contact', side, native)
                call('BattleCommand_damagestats')
                bc=r.B*256+r.C;de=r.D*256+r.E
                call('BattleCommand_damagecalc',bc=bc,de=de)
                call('BattleCommand_stab')
                damage=int.from_bytes(read('wCurDamage',2),'big')
                assert 1 <= damage < 200, ('battle damage',side,native,damage)
                assert index(read(move_struct)[0])==native
                damage_results.append((side,native,damage))
        if wide:
            assert damage_results[0][2]==damage_results[1][2]
            assert damage_results[2][2]==damage_results[3][2]
        print('PASS real move data, priority, contact and damage/STAB calculations on both battle sides:',damage_results)
        if wide:
            reset();handle(200);h=handle(wide)
            write('wTempMonSpecies',1);write('wTempMonForm',1)
            call('InheritEggMove',de=h<<8)
            assert ids('wTempMonMoves')[0]==wide, 'egg move inheritance'
            write('wTempMonMoves',bytes(4))
            call('InheritLevelMove',de=h<<8)
            assert ids('wTempMonMoves')[0]==wide, 'level move inheritance'
            # Primeape's fixture evolution requires the wide move; the native
            # word reader supplies its name without dropping the high byte.
            call('GetEvolutionData',bc=0x139)
            name=read('wStringBuffer4',13)
            write('wNamedObjectIndex',h);call('GetMoveName')
            assert name.split(bytes([0x53]))[0]==read('wStringBuffer1',13).split(bytes([0x53]))[0]
            write('wPartyMon1Species',1);write('wPartyMon1Form',1);write('wPartyMon1Level',5)
            call('GetForgottenMoves')
            assert index(read('wMoveScreenMoves')[0])==wide, ('move relearner',read('wMoveScreenMoves',8),read('wPartyMon1Moves',4),read('wCurPartyMon'),read('wPartyMon1Level'),read('wCurForm'),hex(r.HL))
            write('wPartyMon1Species',3);write('wPartyMon1Moves',[h,0,0,0])
            write('wTempSpecies',3);write('wCurForm',1);write('wCurPartyLevel',32)
            call('LearnEvolutionMove')  # already known; must return without a prompt
            write('wCurPartySpecies',68);write('wCurForm',1);write('wPutativeTMHMMove',h)
            call('CanLearnTMHMMove');assert r.C, 'wide TM compatibility bit'
            reset();handle(200)
            call('GiveSpecialEgg',hl=addr('OddEggs'))
            assert ids('wPartyMon1Moves')[0]==wide, 'special egg'
            reset();handle(200)
            call('BT_AppendOTMon',bc=0)
            assert ids('wOTPartyMon1Moves')[0]==wide, 'battle tower'
            reset();handle(200)
            trainer,group,mapno=rb('NativeMoveReaderManifest',3)
            write('wOtherTrainerClass',trainer);write('wOtherTrainerID',1)
            call('ReadTrainerParty')
            assert read('wOTPartyCount')[0]==6
            assert ids('wOTPartyMon1Moves')[0]==wide, 'trainer native stream'
            reset();handle(200)
            write('wMapGroup',group);write('wMapNumber',mapno)
            write('wCurPartySpecies',100);write('wCurForm',1)
            call('CheckUniqueWildMove')
            assert ids('wOTPartyMon1Moves')[1]==wide, 'unique wild move'
            for command,fixture in [('Script_givepoke','NativeMoveGiftScriptFixture'),('Script_loadmove','NativeMoveLoadScriptFixture')]:
                reset();handle(200)
                write('hScriptBank',syms[fixture][0])
                write('hScriptPos',(addr(fixture)+1).to_bytes(2,'little'))
                call(command, stop='GivePoke.added' if command=='Script_givepoke' else None)
                assert wide in ids('wPartyMon1Moves'), (command, ids('wPartyMon1Moves'))
            print('PASS wide IDs through egg/level inheritance, evolution parameter, special egg, trainer, tower, wild, gift insertion boundary and load-move script readers')

    finally:
        p.stop(save=False)

if __name__ == '__main__': main()
