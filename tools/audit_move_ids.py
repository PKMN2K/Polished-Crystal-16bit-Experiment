#!/usr/bin/env python3
"""Reject byte-only move constants at runtime and native ROM data boundaries."""
from pathlib import Path
import re
import sys

root = Path(__file__).resolve().parents[1]
constants = (root / 'constants/move_constants.asm').read_text().split('; Battle animations')[0]
names = set(re.findall(r'^\s*const\s+([A-Z][A-Z_0-9]*)', constants, re.M)) | {'BRICK_BREAK'}
problems = []
checked = 0
for directory in ('home', 'engine', 'data', 'maps'):
    for path in sorted((root/directory).rglob('*.asm')):
        if 'tilesets' in path.parts:
            continue  # Collision names such as CUT are a separate namespace.
        for number, line in enumerate(path.read_text().splitlines(), 1):
            code = line.split(';')[0].strip()
            if not code or '"' in code:
                continue
            used = set(re.findall(r'\b[A-Z][A-Z_0-9]*\b', code)) & names
            if not used:
                if re.search(r'\b(?:inc|dec) a\s*;\s*cp STRUGGLE', line):
                    problems.append((path, number, line.strip()))
                continue
            checked += 1
            opcode = code.split()[0]
            bad = opcode in {'cp', 'xor', 'db', 'dbw', 'lb', 'setval', 'loadmem'}
            bad |= bool(re.match(r'ld (?:[abcdehl]|\[hl\]),', code))
            if bad:
                problems.append((path, number, line.strip()))
for path, number, line in problems:
    print(f'{path.relative_to(root)}:{number}: byte move boundary: {line}')
print(f'{checked} symbolic move sites audited; {len(problems)} byte-only boundaries')
sys.exit(bool(problems))
