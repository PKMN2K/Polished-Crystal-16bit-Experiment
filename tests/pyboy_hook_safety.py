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
