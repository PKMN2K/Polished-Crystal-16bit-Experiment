"""Wide catalog identity integration; requires a native-test ROM, no ROM stubs."""
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
            syms[fields[1]] = tuple(int(v, 16) for v in fields[0].split(':'))
    def addr(label): return syms[label][1]
    data = rom.read_bytes()
    bank, at = syms['NativeWideTestIdentity']
    offset = bank * 0x4000 + at - 0x4000
    native = int.from_bytes(data[offset:offset+2], 'little')
    assert native > 0x1ff
    p = PyBoy(str(rom), window='null', sound_emulated=False, cgb=True, log_level='ERROR')
    m, r = p.memory, p.register_file
    def put(label, value): m[addr(label)] = value
    def get(label, length): return bytes(m[addr(label):addr(label)+length])
    def write(label, data): m[addr(label):addr(label)+len(data)] = list(data)
    def word(label, value): write(label, value.to_bytes(2, 'little'))
    def bc(): return r.B * 256 + r.C
    def invoke(label, a=0, bc=0, hl=0xc280, de=0xc380, ticks=6, wram=1):
        m[0xff70] = wram
        bank, target = syms[label]
        bank = bank or 1
        m[0x2000] = bank
        put('hROMBank', bank)
        m[0xc100:0xc106] = [0xf3, 0xcd, target & 255, target >> 8, 0x18, 0xfe]
        r.A, r.B, r.C, r.HL, r.D, r.E = a, bc >> 8, bc & 255, hl, de >> 8, de & 255
        r.SP, r.PC = 0xc0ff, 0xc100
        p.tick(ticks, False, False)
        assert (r.PC, r.SP) == (0xc104, 0xc0ff), (label, hex(r.PC), hex(r.SP))
        assert m[addr('hROMBank')] == bank, label
        assert m[0xff70] & 7 == wram, label
        return bool(r.F & 0x10)
    try:
        m[0xff50] = 1
        m[0xffff] = m[0xff0f] = m[0xff40] = 0
        for bank in (1, 2):
            m[0xff70] = bank
            m[0xd000:0xe000] = [0]*0x1000
        m[0xff70] = 1
        invoke('GetRootSpeciesFromNativeIDBC', bc=native)
        assert bc() == native, 'ROM must contain the wide root fixture'
        for raw in (1, 0x21, 0x81, 0xc1):
            invoke('GetLegacySpeciesAndFormFromNativeIDBC', bc=native, a=raw)
            runtime = bc()
            assert runtime & 0x2000 and 0x80 < (runtime & 255) <= 0xe4, hex(runtime)
            assert runtime >> 8 == raw | 0x20
            invoke('GetSpeciesAndFormIndex', bc=runtime)
            assert bc() == native-1, hex(bc())
            invoke('GetCosmeticSpeciesAndFormIndex', bc=runtime)
            assert bc() == native-1
        invoke('GetLegacySpeciesAndFormFromNativeIDBC', bc=native, a=1)
        runtime = bc()
        invoke('GetBaseDataFromNativeIDBC', bc=0x123)
        expected_stats = get('wCurBaseData', addr('wCurBaseDataEnd')-addr('wCurBaseData'))
        put('wCurSpecies', runtime & 255)
        put('wCurForm', runtime >> 8)
        invoke('GetBaseData')
        assert get('wCurBaseData', len(expected_stats)) == expected_stats
        invoke('GetPokemonNameFromNativeIDBC', bc=0x123)
        expected_name = get('wStringBuffer1', 11)
        word('wNamedObjectIndex', runtime)
        invoke('GetPokemonName')
        assert get('wStringBuffer1', 11) == expected_name
        invoke('GetPokedexFlagIndex', bc=runtime)
        assert r.D*256+r.E == 0x18a, hex(r.D*256+r.E)
        invoke('GetNationalDexNumber', bc=runtime)
        assert bc() == 290, bc()
        word('wPokemonDataFormat', 0x16bc)
        for enemy in (False, True):
            put('wMonType', int(enemy))
            put('wBattleMode', 1)
            put('wBattleType', 0)
            put('wCurPartySpecies', runtime & 255)
            put('wCurForm', runtime >> 8)
            put('wCurPartyLevel', 20)
            assert invoke('TryAddMonToParty', ticks=30)
            prefix = 'wOTPartyMon1' if enemy else 'wPartyMon1'
            invoke('GetNativeSpeciesIDFromLegacyPokemonDataStruct' if enemy else 'GetNativeSpeciesIDFromPokemonDataStruct',
                   hl=addr(prefix+'Species'), de=addr(prefix+'Form')-addr(prefix+'Species'))
            assert bc() == native, (prefix, hex(bc()))
            assert m[addr(prefix+'Level')] == 20
            assert int.from_bytes(get(prefix+'MaxHP', 2), 'big') > 0
        # Consume an actual compiled native encounter record, then run the full
        # wild generator (form choice, stats, held item, moves and PP).
        put('wWildMonDataBank', syms['NativeWideTestIdentity'][0])
        invoke('LoadLegacyWildmonFromHL', hl=addr('NativeWideTestIdentity'))
        assert r.HL == addr('NativeWideTestIdentity') + 3
        runtime = bc()
        put('wTempEnemyMonSpecies', runtime & 255)
        put('wWildMonForm', runtime >> 8)
        put('wCurPartyLevel', 20)
        invoke('LoadEnemyWildmon', ticks=30)
        invoke('GetNativeSpeciesIDFromLegacyPokemonDataStruct', hl=addr('wOTPartyMon1Species'),
               de=addr('wOTPartyMon1Form')-addr('wOTPartyMon1Species'))
        assert bc() == native
        assert m[addr('wOTPartyCount')] == 1
        assert m[addr('wOTPartyMon1Moves')] and m[addr('wOTPartyMon1PP')]

        # Catching copies the actual opponent record and converts the player slot.
        put('wPartyCount', 2)
        opponent = get('wOTPartyMon1Species', addr('wOTPartyMon2Species')-addr('wOTPartyMon1Species'))
        invoke('CopyCaughtPokemonToParty', a=1)
        invoke('GetNativeSpeciesIDFromPokemonDataStruct', hl=addr('wPartyMon2Species'),
               de=addr('wPartyMon2Form')-addr('wPartyMon2Species'))
        assert bc() == native
        assert get('wOTPartyMon1Species', len(opponent)) == opponent

        # Full PC serializer/deserializer, including live stat reconstruction.
        put('wMonType', 0)
        put('wCurPartyMon', 0)
        invoke('CopyPkmnToTempMon')
        invoke('SetTempPartyMonData')
        hp = get('wTempMonMaxHP', 12)
        assert any(hp)
        invoke('EncodeTempMon')
        assert m[addr('wEncodedTempMonSpecies')] == native & 255
        assert get('wEncodedTempMonExtra', 2)[1] == native >> 8
        invoke('ChecksumTempMon')
        assert r.F & 0x80
        encoded = get('wEncodedTempMonSpecies', addr('wEncodedTempMonEnd')-addr('wEncodedTempMonSpecies'))
        write('wTempMonSpecies', bytes(addr('wTempMonExtra')+3-addr('wTempMonSpecies')))
        write('wEncodedTempMonSpecies', encoded)
        assert not invoke('DecodeTempMon', ticks=40)
        assert get('wTempMonMaxHP', 12) == hp
        invoke('GetNativeSpeciesIDFromLegacyPokemonDataStruct', hl=addr('wTempMonSpecies'),
               de=addr('wTempMonForm')-addr('wTempMonSpecies'))
        assert bc() == native

        # Real cry and compressed front-picture lookup, not patched pointers.
        invoke('LoadCryFromNativeIDBC', bc=0x123)
        expected_cry = get('wCryPitch', 4)
        assert not invoke('LoadCryFromNativeIDBC', bc=native)
        assert get('wCryPitch', 4) == expected_cry
        frames = []
        for identity in (0x2123, runtime):
            put('wCurPartySpecies', identity & 255)
            put('wCurForm', identity >> 8)
            invoke('PrepareFrontpic', ticks=20)
            invoke('GetPaddedFrontpicAddress')
            pointer = r.D*256+r.E
            m[0xff70] = syms['wDecompressScratch'][0]
            frames.append(bytes(m[pointer:pointer+7*7*16]))
            m[0xff70] = 1
        assert frames[0] == frames[1] and any(frames[1])
        put('hBattleTurn', 1)
        invoke('SendInUserPkmn.store_native_identity', hl=addr('wOTPartyMon1Species'))
        assert get('wEnemyMonNativeSpecies', 2) == native.to_bytes(2, 'little')
        put('wEnemyMonForm', 1)
        assert not invoke('PrepareEnemyBattlePictureIdentity')
        invoke('GetSpeciesAndFormIndex', bc=m[addr('wCurForm')]*256+m[addr('wCurPartySpecies')])
        assert bc() == native-1

        # Evolution eligibility and target decode both directions across $01ff.
        put('wCurPartyMon', 0)
        put('wEvolutionOldSpecies', runtime & 255)
        put('wEvolutionOldForm', runtime >> 8)
        put('wPartyMon1Level', 20)
        invoke('CheckHowToEvolve')
        assert r.F & 0x80, 'wide species must wait until level 21'
        put('wPartyMon1Level', 21)
        invoke('CheckHowToEvolve')
        assert not r.F & 0x80
        invoke('GetSpeciesAndFormIndex', bc=int.from_bytes(get('wEvolutionNewSpecies', 2), 'little'))
        assert bc() == 0x122
        put('wMonType', 0)
        put('wCurPartySpecies', 0x23)
        put('wCurForm', 0x21)
        put('wCurPartyLevel', 20)
        assert invoke('TryAddMonToParty', ticks=30)
        put('wCurPartyMon', 2)
        put('wEvolutionOldSpecies', 0x23)
        put('wEvolutionOldForm', 0x21)
        invoke('CheckHowToEvolve')
        assert not r.F & 0x80
        invoke('GetSpeciesAndFormIndex', bc=int.from_bytes(get('wEvolutionNewSpecies', 2), 'little'))
        assert bc() == native-1
        # A target with low byte $ff must not terminate the evolution scanner.
        invoke('GetEvosAttacksPointerFromNativeIDBC', bc=0x123)
        pointer = r.HL
        invoke('SkipEvolutionData', hl=pointer)
        assert r.HL == pointer + 6, (hex(r.HL), hex(pointer))

        # The actual daycare generator consumes native hatchling records.
        stride = addr('wPartyMon2Species')-addr('wPartyMon1Species')
        for parent, female in ((1, True), (2, False)):
            write(f'wBreedMon{parent}Species', get('wPartyMon1Species', addr('wBreedMon1Level')-addr('wBreedMon1Species')+1))
            put(f'wBreedMon{parent}Form', (runtime >> 8) | (0x80 if female else 0))
        invoke('DayCare_GenerateEgg', ticks=60)
        assert m[addr('wTempMonForm')] & 0x40
        invoke('GetNativeSpeciesIDFromLegacyPokemonDataStruct', hl=addr('wTempMonSpecies'),
               de=addr('wTempMonForm')-addr('wTempMonSpecies'))
        assert bc() == native, ('egg', hex(bc()), get('wTempMonSpecies', 1).hex(), get('wTempMonForm', 1).hex(), get('wCurForm', 1).hex(), get('wCurPartySpecies', 1).hex())
        assert m[addr('wTempMonLevel')] == 1

        # Pokédex construction, selection and search retain native words.
        write('wPokedexSeen', bytes(addr('wEndPokedexSeen')-addr('wPokedexSeen')))
        write('wPokedexCaught', bytes(addr('wEndPokedexCaught')-addr('wPokedexCaught')))
        for field in ('wPokedexSeen', 'wPokedexCaught'):
            m[addr(field)+0x18a//8] = 1 << (0x18a % 8)
        put('wPokedexMode', 1)
        invoke('Pokedex_InitData', ticks=240)
        dex_bank = syms['wDexMons'][0]
        m[0xff70] = dex_bank
        entry = addr('wDexMons') + 289*3
        assert bytes(m[entry:entry+2]) == native.to_bytes(2, 'little')
        m[0xff70] = 1
        put('wPokedex_DisplayMode', 0)
        put('wPokedex_Offset', 57)
        put('wPokedex_CursorPos', 4)
        invoke('Pokedex_GetCursorSpecies')
        invoke('GetSpeciesAndFormIndex', bc=bc())
        assert bc() == native-1
        put('wPokedex_SearchOrder', 1)
        write('wPokedex_SearchData', bytes(addr('wPokedex_SearchDataEnd')-addr('wPokedex_SearchData')))
        invoke('Pokedex_GetSearchResults', ticks=240)
        assert not r.F & 0x80
        m[0xff70] = dex_bank
        assert get('wDexMons', 2) == native.to_bytes(2, 'little')
        m[0xff70] = 1
        assert int.from_bytes(get('wTempDexSeen', 2), 'big') == 1

        # Persist the full conversion table and player records through both saves.
        for prefix, save, verify, load, save_data, load_data in (
            ('s', 'SavePokemonIndexTable', 'VerifyPokemonIndexTable', 'LoadPokemonIndexTable', 'SavePokemonData', 'LoadPokemonData'),
            ('sBackup', 'SaveBackupPokemonIndexTable', 'VerifyBackupPokemonIndexTable', 'LoadBackupPokemonIndexTable', 'SaveBackupPokemonData', 'LoadBackupPokemonData'),
        ):
            def saved_call(label):
                m[0] = 0x0a
                m[0x4000] = syms['sSRAMAccessCount'][0]
                put('sSRAMAccessCount', 0)
                put('wSRAMAccessCount', 1)
                invoke(label, ticks=20)
            saved_call(save_data)
            saved_call(save)
            saved_call(verify)
            assert r.F & 0x80, prefix
            write('wPartyMon1Species', bytes(stride))
            m[0xff70] = 2
            write('wPokemonIndexTable', bytes(256))
            m[0xff70] = 1
            saved_call(load_data)
            saved_call(load)
            invoke('GetNativeSpeciesIDFromPokemonDataStruct', hl=addr('wPartyMon1Species'),
                   de=addr('wPartyMon1Form')-addr('wPartyMon1Species'))
            assert bc() == native, prefix

        # Independently exercise runtime GC roots after overflowing all 100 slots.
        for species, form in (
            ('wOTPartyMon6Species', 'wOTPartyMon6Form'),
            ('wLinkPlayerPartyMon1Species', 'wLinkPlayerPartyMon1Form'),
            ('wTempMonSpecies', 'wTempMonForm'),
            ('wEnemyMonSpecies', 'wEnemyMonForm'),
            ('wCurSpecies', 'wCurForm'),
        ):
            for bank in range(1, 8):
                m[0xff70] = bank
                m[0xd000:0xe000] = [0]*4096
            m[0xc200:0xd000] = [0]*0xe00
            m[0xff70] = 1
            invoke('GetLegacySpeciesAndFormFromNativeIDBC', bc=native, a=1)
            handle = bc()
            m[0xff70] = syms[species][0] or 1
            put(species, handle & 255)
            put(form, handle >> 8)
            m[0xff70] = 1
            for value in range(0x1000, 0x1000+210):
                invoke('GetPokemonIDFromIndex', hl=value, ticks=1)
            invoke('GetNativeRootFromRuntimeBC', bc=handle)
            assert bc() == native, (species, hex(bc()))
        print(f'PASS: native ${native:04x}: codecs, generation/catching, PC, cry/frontpic, evolution, daycare egg, Pokédex, primary/backup saves, GC pressure; no ROM stubs')
    finally:
        p.stop(save=False)


if __name__ == '__main__':
    main()
