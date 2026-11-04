"""Two independent peers exchange native party packets through real ROM codecs.

The harness transports serialized buffers, not cable interrupts. No ROM code is
stubbed. Both peers have different allocator histories; wide fixture ROMs also
exercise native IDs above $01ff and isolated trade-animation GC roots.
"""
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

    def addr(label):
        return syms[label][1]

    data = rom.read_bytes()

    def rom_bytes(label, size):
        bank, at = syms[label]
        offset = bank * 0x4000 + at % 0x4000
        return data[offset:offset+size]

    manifest = rom_bytes('NativeVariantIdentityTable', 46*5)
    vulpix = next(int.from_bytes(manifest[i:i+2], 'little')
                  for i in range(0, len(manifest), 5)
                  if manifest[i+2:i+5] == bytes((37, 0, 2)))
    wide = (int.from_bytes(rom_bytes('NativeWideTestIdentity', 2), 'little')
            if 'NativeWideTestIdentity' in syms else None)
    wide_move = (int.from_bytes(rom_bytes('NativeWideMoveTestIdentity', 2), 'little')
                 if 'NativeWideMoveTestIdentity' in syms else None)
    moves_offset = addr('wPartyMon1Moves') - addr('wPartyMon1')
    stride = addr('wPartyMon2') - addr('wPartyMon1')
    form = addr('wPartyMon1Form') - addr('wPartyMon1')
    unused = addr('wPartyMon1Unused') - addr('wPartyMon1')
    name_len = addr('wPartyMon2Nickname') - addr('wPartyMon1Nickname')
    packet_len = addr('wOTPartyDataEnd') - addr('wOTPartyData')
    patch_len = addr('wPlayerTrademonSpecies') - addr('wLinkMisc')
    decoded_len = addr('wLinkPlayerDataEnd') - addr('wLinkData')
    party_offset = addr('wLinkPlayerPartyMon1') - addr('wLinkData')

    class Peer:
        def __init__(self):
            self.p = PyBoy(str(rom), window='null', sound_emulated=False,
                           cgb=True, log_level='ERROR')
            self.m, self.r = self.p.memory, self.p.register_file

        def put(self, label, value):
            self.m[addr(label)] = value

        def get(self, label, length):
            return bytes(self.m[addr(label):addr(label)+length])

        def write(self, label, value):
            self.m[addr(label):addr(label)+len(value)] = list(value)

        def invoke(self, label, *, a=0, bc=0, hl=0xc280, de=0xc380):
            bank, target = syms[label]
            bank = bank or 1
            self.m[0x2000] = bank
            self.put('hROMBank', bank)
            self.m[0xc100:0xc106] = [0xf3, 0xcd, target & 255, target >> 8, 0x18, 0xfe]
            r = self.r
            r.A, r.B, r.C, r.HL, r.D, r.E = a, bc >> 8, bc & 255, hl, de >> 8, de & 255
            r.SP, r.PC = 0xc0ff, 0xc100
            for _ in range(40):
                self.p.tick(1, False, False)
                if (r.PC, r.SP) == (0xc104, 0xc0ff):
                    break
            assert (r.PC, r.SP) == (0xc104, 0xc0ff), (label, hex(r.PC), hex(r.SP), self.m[addr('hROMBank')], hex(r.HL), r.B, r.C, r.D, r.E)
            assert self.m[addr('hROMBank')] == bank and self.m[0xff70] & 7 == 1
            return bool(r.F & 0x10)

        def bc(self):
            return self.r.B*256 + self.r.C

        def reset(self, seed=0, native=True):
            self.m[0xff50] = 1
            self.m[0xffff] = self.m[0xff0f] = self.m[0xff40] = 0
            self.m[0xc000:0xd000] = [0]*0x1000
            for bank in (1, 2):
                self.m[0xff70] = bank
                self.m[0xd000:0xe000] = [0]*0x1000
            self.m[0xff70] = 1
            self.m[0x0000] = 0x0a
            self.m[0x4000] = syms['sPartyMail'][0]
            self.write('sPartyMail', bytes(addr('sPartyMailBackup')-addr('sPartyMail')))
            self.m[0x4000] = syms['sSRAMAccessCount'][0]
            self.put('sSRAMAccessCount', 0)
            self.put('wSRAMAccessCount', 1)
            self.m[0x0000] = 0
            self.write('wPokemonDataFormat', b'\xbc\x16' if native else b'\0\0')
            self.invoke('InitializeNativeMoveDataForNewGame')
            for value in range(50, 50+seed):
                self.invoke('GetPokemonIDFromIndex', hl=value)
                self.invoke('GetMoveIDFromIndex', hl=value)

        def prepare(self, identities, mode, native=True):
            self.put('wPartyCount', len(identities))
            self.put('wLinkMode', mode)
            self.write('wPlayerName', bytes([0x80]*10+[0x50]))
            self.write('wPlayerID', bytes((0xfe, 0xfd)))
            self.write('wPartyMons', bytes([0xa5]) * (6*stride))
            originals = []
            native_moves = []
            for i, (identity, metadata) in enumerate(identities):
                prefix = f'wPartyMon{i+1}'
                payload = bytearray((0xfd, 0xfe, 0xff)[j % 3] for j in range(stride))
                self.invoke('GetLegacySpeciesAndFormFromNativeIDBC', bc=identity, a=metadata)
                runtime = self.bc()
                payload[0], payload[form] = runtime & 255, runtime >> 8
                if native:
                    self.invoke('GetPokemonIDFromIndex', hl=identity)
                    payload[0] = self.r.A
                moves = [33 + i, 255, wide_move or 254, 0]
                native_moves.append(moves)
                for slot, move in enumerate(moves):
                    self.invoke('GetMoveIDFromIndex', hl=move)
                    payload[moves_offset+slot] = self.r.A
                payload[addr(prefix+'Level')-addr(prefix)] = 20
                self.write(prefix, payload)
                originals.append(bytes(payload))
                self.write(prefix+'OT', bytes([0x81+i]*10+[0x50]))
                self.write(prefix+'Nickname', bytes([0x87+i]*10+[0x50]))
            before = self.get('wPartyMons', 6*stride)
            self.invoke('ClearLinkData')
            self.invoke('Link_PrepPartyData_Gen2')
            raw = self.get('wLinkData', packet_len)
            for i, (identity, _) in enumerate(identities):
                start = 6 + party_offset + i*stride
                assert raw[start] | raw[start+unused] << 8 == identity
                assert raw[start+form] == originals[i][form] & ~0x20
            empty_start = 6 + party_offset + len(identities)*stride
            assert raw[empty_start:6+party_offset+6*stride] == bytes((6-len(identities))*stride)
            self.invoke('FixDataForLinkTransfer')
            packet = self.get('wLinkData', packet_len)
            patches = self.get('wLinkMisc', patch_len)
            assert 0xfe not in packet[6+party_offset-2:6+party_offset+6*stride]
            assert self.get('wPartyMons', 6*stride) == before
            return packet, patches, originals, raw, native_moves

        def receive(self, sent, identities):
            packet, patches, originals, raw, native_moves = sent
            self.write('wOTPartyData', packet)
            self.put('wBattleAction', 0xfe)  # serial terminator at wOTPartyDataEnd
            self.write('wPlayerTrademonSpecies', patches)
            self.invoke('Link_UnpackPartyData')
            decoded = self.get('wLinkData', decoded_len)
            assert decoded == raw[6:6+decoded_len], 'real patch-list round trip'
            assert not self.invoke('Link_LoadOTParty')
            assert self.m[addr('wOTPartyCount')] == len(identities)
            assert self.get('wOTPlayerID', 2) == bytes((0xfe, 0xfd))
            assert self.get('wOTPlayerName', 11) == bytes([0x80]*10+[0x50])
            for i, ((identity, _), original) in enumerate(zip(identities, originals)):
                prefix = f'wOTPartyMon{i+1}'
                actual = self.get(prefix, stride)
                expected = bytearray(original)
                self.invoke('GetLegacySpeciesAndFormFromNativeIDBC', bc=identity, a=original[form])
                expected[0], expected[form], expected[unused] = self.r.C, self.r.B, 0
                for slot, native_move in enumerate(native_moves[i]):
                    self.invoke('GetMoveIndexFromID', a=actual[moves_offset+slot])
                    assert self.r.HL == native_move, ('wire move identity', i, slot, self.r.HL, native_move)
                    self.invoke('GetMoveIDFromIndex', hl=native_move)
                    expected[moves_offset+slot] = self.r.A
                assert actual == expected, (hex(identity), actual.hex(), expected.hex())
                self.invoke('GetNativeSpeciesIDFromLegacyPokemonDataStruct', hl=addr(prefix), de=form)
                assert self.bc() == identity
                assert self.get(prefix+'OT', name_len) == bytes([0x81+i]*10+[0x50])
                assert self.get(prefix+'Nickname', name_len) == bytes([0x87+i]*10+[0x50])
                # Battle handoff publishes the full identity from the received slot.
                self.put('hBattleTurn', 1)
                self.invoke('SendInUserPkmn.store_native_identity', hl=addr(prefix))
                assert self.get('wEnemyMonNativeSpecies', 2) == identity.to_bytes(2, 'little')
            at = addr('wOTPartyMons') + len(identities)*stride
            if len(identities) < 6:
                assert bytes(self.m[at:addr('wOTPartyMons')+6*stride]) == bytes((6-len(identities))*stride)

    peers = [Peer(), Peer()]
    cases = 0
    try:
        roster = [(wide or 25, 0xc1), (vulpix, 0x82), (0x123, 1),
                  (129, 20), (0xfd, 1), (0xfe, 0x81)]
        for native_format in (False, True):
            for mode in (2, 3):
                for count in range(1, 7):
                    teams = [roster[:count], list(reversed(roster))[:count]]
                    packets = []
                    for i, peer in enumerate(peers):
                        peer.reset(seed=3+i*27, native=native_format)
                        packets.append(peer.prepare(teams[i], mode, native_format))
                    # Capture both outgoing packets before either receive buffer is used.
                    for i, peer in enumerate(peers):
                        peer.receive(packets[1-i], teams[1-i])
                        cases += 1
                    if wide and count == 6:
                        a = peers[0].get('wPartyMon1Species', 1)[0]
                        b = peers[1].get('wOTPartyMon1Species', 1)[0]
                        assert (a+0x80 if native_format else a) != b, 'different peers must use different handles'
                    # Run the actual post-trade copy and persistent insertion boundary.
                    for i, peer in enumerate(peers):
                        peer.put('wPartyCount', 0)
                        peer.invoke('CopyBetweenPartyAndTemp', bc=0x8101)
                        assert not peer.invoke('AddTempMonToParty')
                        peer.invoke('GetNativeSpeciesIDFromPokemonDataStruct', hl=addr('wPartyMon1'), de=form)
                        assert peer.bc() == teams[1-i][0][0]
                        for slot, native_move in enumerate(packets[1-i][4][0]):
                            peer.invoke('GetMoveIndexFromID', a=peer.get('wPartyMon1Moves',4)[slot])
                            assert peer.r.HL == native_move, 'post-trade native move identity'
                        assert peer.get('wPartyMon1Nickname',name_len)==bytes([0x87]*10+[0x50])

        peer = peers[0]
        peer.reset(native=True)
        sent = peer.prepare(roster, 3)
        valid = sent[3][6:6+decoded_len]
        # Validation failures must leave destination and allocator untouched.
        corruptions = []
        for count in (0, 7, 255):
            packet = bytearray(valid)
            packet[addr('wLinkPartyCount')-addr('wLinkData')] = count
            corruptions.append(packet)
        for identity in (0, 0xff, 0x100, 0x200, 0xffff):
            for slot in (0, 5):
                packet = bytearray(valid)
                offset = party_offset + slot*stride
                packet[offset], packet[offset+unused] = identity & 255, identity >> 8
                corruptions.append(packet)
        packet = bytearray(valid)
        packet[party_offset+form] |= 0x20
        corruptions.append(packet)
        packet = bytearray(valid)
        packet[addr('wLinkPartyCount')-addr('wLinkData')] = 1  # nonzero unused identities
        corruptions.append(packet)
        packet = bytearray(valid)
        packet[party_offset+moves_offset] = 255
        packet[addr('wLinkPlayerMoveHighs')-addr('wLinkData')] = 255
        corruptions.append(packet)
        for packet in corruptions:
            peer.write('wLinkData', packet)
            before = peer.get('wOTPartyMons', 6*stride)
            peer.m[0xff70] = 2
            table = peer.get('wPokemonIndexTable', 256)
            move_table = peer.get('wMoveIndexTable', 512)
            peer.m[0xff70] = 1
            assert peer.invoke('Link_LoadOTParty'), 'reject malformed party'
            assert peer.get('wOTPartyMons', 6*stride) == before
            peer.m[0xff70] = 2
            assert peer.get('wPokemonIndexTable', 256) == table
            assert peer.get('wMoveIndexTable', 512) == move_table
            peer.m[0xff70] = 1

        for mode in (2, 3):
            peer.put('wLinkMode', mode)
            for version, minimum, expected in ((7, 7, 1), (6, 6, 2 if mode == 2 else 0),
                                                (4, 4, 2 if mode == 2 else 0),
                                                (8, 8, 3 if mode == 2 else 0)):
                peer.write('wLinkOtherPlayerVersion', version.to_bytes(2, 'big'))
                peer.write('wLinkOtherPlayerMinTradeVersion', minimum.to_bytes(2, 'big'))
                peer.invoke('CheckCorrectLinkVersion')
                assert peer.r.A == expected, (mode, version, peer.r.A)

        if wide_move:
            sender, receiver = peers
            sender.reset(seed=3)
            sent=sender.prepare(roster,3)
            receiver.reset(seed=0)
            receiver.m[0xff70]=2
            receiver.write('wMoveIndexTableEntries',b''.join(n.to_bytes(2,'little') for n in range(1,231)))
            receiver.put('wMoveIndexTableUsedSlots',230)
            receiver.m[0xff70]=1
            receiver.receive(sent,roster)
            receiver.m[0xff70]=2
            assert receiver.get('wMoveIndexTableUsedSlots',1)[0] < 230, 'move GC not forced'
            receiver.m[0xff70]=1

        if wide:
            # Force the first received wide allocation to collect a full local
            # table while future wire records and raw receive bytes are present.
            sender, receiver = peers
            sender.reset()
            sent = sender.prepare(roster, 3)
            receiver.reset(seed=30)
            receiver.prepare([(0xfe, 1)], 3)
            for value in range(1, 254):
                receiver.m[0xff70] = 2
                full = receiver.m[addr('wPokemonIndexTable')] == 100
                receiver.m[0xff70] = 1
                if full:
                    break
                receiver.invoke('GetPokemonIDFromIndex', hl=value)
            assert full, 'fixture must fill allocator before receive'
            receiver.receive(sent, roster)
            receiver.m[0xff70] = 2
            assert receiver.m[addr('wPokemonIndexTable')] < 100, 'receive must collect'
            receiver.m[0xff70] = 1
            for prefix in ('wPlayerTrademon', 'wOTTrademon',
                           'wLinkTradeSendmon', 'wLinkTradeGetmon'):
                peer.reset()
                peer.invoke('GetLegacySpeciesAndFormFromNativeIDBC', bc=wide, a=0x81)
                peer.put(prefix+'Species', peer.r.C)
                peer.put(prefix+'Form', peer.r.B)
                for value in range(1, 230):
                    peer.invoke('GetPokemonIDFromIndex', hl=value)
                peer.invoke('GetNativeSpeciesIDFromLegacyPokemonDataStruct',
                            hl=addr(prefix+'Species'), de=addr(prefix+'Form')-addr(prefix+'Species'))
                assert peer.bc() == wide, (prefix, 'trade animation GC root')
        print(f'PASS: {cases} two-peer native packet transfers; real serial escaping, '
              'battle/trade handoffs, metadata, empty slots, invalid IDs and version rejection; '
              f'species={hex(wide) if wide else "ordinary"}, moves={hex(wide_move) if wide_move else "ordinary"}; no ROM stubs, cable timing not emulated')
    finally:
        for peer in peers:
            peer.p.stop(save=False)


if __name__ == '__main__':
    main()
