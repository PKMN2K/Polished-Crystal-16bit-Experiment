"""Fresh/New Game+ setup must start player Pokemon storage in empty native format."""
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

    def addr(name):
        return symbols[name][1]

    pyboy = PyBoy(
        str(rom),
        window="null",
        sound_emulated=False,
        cgb=True,
        log_level="ERROR",
    )
    mem, regs = pyboy.memory, pyboy.register_file

    def write(name, value):
        mem[addr(name)] = value

    def invoke(name, ticks=12):
        bank, target = symbols[name]
        bank = bank or 1
        mem[0x2000] = bank
        write("hROMBank", bank)
        mem[0xC100:0xC106] = [
            0xF3,
            0xCD,
            target & 0xFF,
            target >> 8,
            0x18,
            0xFE,
        ]
        regs.SP = 0xC0FF
        regs.PC = 0xC100
        pyboy.tick(ticks, False, False)
        assert (regs.PC, regs.SP) == (0xC104, 0xC0FF), (
            name,
            hex(regs.PC),
            hex(regs.SP),
        )

    try:
        mem[0xFF50] = 1
        mem[0xFFFF] = 0
        mem[0xFF0F] = 0
        mem[0xFF40] = 0
        mem[0xFF70] = 1

        # Leave stale table state exactly as New Game+ could after loading an
        # older session, and dirty the format words so the initializer must
        # establish the complete empty-session invariant.
        table_bank = symbols["wPokemonIndexTable"][0]
        mem[0xFF70] = table_bank
        table_start = addr("wPokemonIndexTable")
        table_end = addr("wPokemonIndexTableEnd")
        mem[table_start:table_end] = [0x5A] * (table_end - table_start)
        mem[0xFF70] = symbols["wPokemonDataFormat"][0]
        mem[addr("wPokemonDataFormat"):addr("wPokemonDataFormat") + 2] = [0, 0]
        mem[addr("wPokemonIndexTableFormat"):addr("wPokemonIndexTableFormat") + 2] = [0xAA, 0xBB]
        write("wPartyCount", 0)
        mem[0xFF70] = 1

        # Exercise the actual _NewGame_FinishSetup hook. Stub only unrelated
        # reset/UI/world setup; the new native initializer remains real.
        for name in (
            "ResetWRAM",
            "ClearSavedObjPals",
            "NewGame_ClearTileMapEtc",
            "WarnVBA",
            "SetInitialOptions",
            "ProfElmSpeech",
            "InitializeWorld",
            "FinishContinueFunction",
        ):
            bank, target = symbols[name]
            mem[bank, target] = 0xC9

        invoke("_NewGame_FinishSetup", ticks=20)

        mem[0xFF70] = symbols["wPokemonDataFormat"][0]
        assert bytes(
            mem[addr("wPokemonDataFormat"):addr("wPokemonDataFormat") + 2]
        ) == bytes([0xBC, 0x16])
        assert bytes(
            mem[addr("wPokemonIndexTableFormat"):addr("wPokemonIndexTableFormat") + 2]
        ) == bytes([0, 0])

        mem[0xFF70] = table_bank
        assert not any(mem[table_start:table_end]), "new-game conversion table retained stale entries"
        mem[0xFF70] = 1

        # The first generated player Pokemon must therefore be stored through
        # the native conversion table rather than as legacy species/form bytes.
        write("wInitialOptions", 0)
        write("wPartyCount", 0)
        write("wMonType", 0)
        write("wBattleMode", 1)
        write("wBattleType", 0)
        write("wCurPartySpecies", 1)
        write("wCurForm", 0x21)  # legacy presentation of native $0101
        write("wCurPartyLevel", 20)

        invoke("TryAddMonToParty", ticks=24)
        assert regs.F & 0x10, "first native-format party insertion failed"
        assert mem[addr("wPartyCount")] == 1
        transient = mem[addr("wPartyMon1Species")]
        assert transient != 0

        mem[0xFF70] = table_bank
        entry = addr("wPokemonIndexTableEntries") + 2 * (transient - 1)
        native = int.from_bytes(mem[entry:entry + 2], "little")
        mem[0xFF70] = 1
        assert native == 0x0101, hex(native)
        assert mem[addr("wPartyMon1Form")] & 0x3F == 0x21

        print(
            "PASS: _NewGame_FinishSetup clears stale transient state, enables native player "
            "format, and first generated $0101 party member allocates the correct native ID"
        )
    finally:
        pyboy.stop(save=False)


if __name__ == "__main__":
    main()
