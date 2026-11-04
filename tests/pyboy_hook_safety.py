"""Safe PyBoy hook placement for the Future Sight battle routine.

An entry breakpoint on GetFutureSightUser can repeatedly fire without CPU
progress in native battle boundary regressions. Observe the next opcode.
"""


def hook_future_sight_after_push(pyboy, symbols, rom_data, offset, callback):
    bank, address = symbols["GetFutureSightUser"]
    start = offset("GetFutureSightUser")
    if rom_data[start:start + 2] != bytes((0xE5, 0xD5)):
        raise AssertionError("GetFutureSightUser prologue changed; hook needs review")
    pyboy.hook_register(bank, address + 1, callback, None)


def hook_reset_subhit_after_push(pyboy, symbols, rom_data, offset, callback):
    """Observe ResetSubHit after its LD A and fallthrough PUSH HL.

    Breakpoints on the entry opcode can cause a PyBoy tick to loop forever.
    Check the compiled layout, including the shared ResetMoveHitState entry,
    before placing the breakpoint on LD HL instead.
    """
    start = offset("ResetSubHit")
    if offset("ResetMoveHitState") != start + 2:
        raise AssertionError("ResetSubHit fallthrough changed; hook needs review")
    if rom_data[start] != 0x3E or rom_data[start + 2:start + 4] != bytes((0xE5, 0x21)):
        raise AssertionError("ResetSubHit prologue changed; hook needs review")
    bank, address = symbols["ResetSubHit"]
    pyboy.hook_register(bank, address + 3, callback, None)


def hook_user_item_after_future_sight(pyboy, symbols, rom_data, offset, callback):
    """Observe GetUserItem after its read-only Future Sight identity query.

    An entry breakpoint can recur indefinitely in the debug ROM. The following
    JR is reached on every path, before item selection or any item-state write.
    """
    start = offset("GetUserItem")
    expected = bytes((0xCD, symbols["GetFutureSightUser"][1] & 255,
                      symbols["GetFutureSightUser"][1] >> 8, 0x28))
    if rom_data[start:start + 4] != expected:
        raise AssertionError("GetUserItem prologue changed; hook needs review")
    bank, address = symbols["GetUserItem"]
    pyboy.hook_register(bank, address + 3, callback, None)
