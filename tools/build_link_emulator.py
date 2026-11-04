"""Build the pinned SameBoy core and open-source CGB boot ROM for linked tests."""
import argparse
import json
from pathlib import Path
import subprocess

REVISION = 'ea667ad79aa28409f034b1fd6da7304e1844750d'
URL = 'https://github.com/LIJI32/SameBoy.git'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path('build/sameboy'))
    parser.add_argument('--rgbds', default='')
    parser.add_argument('--cc', default='gcc')
    parser.add_argument('--jobs', default='2')
    args = parser.parse_args()
    source = args.source.resolve()
    root = Path(__file__).resolve().parents[1]
    (root / 'build').mkdir(exist_ok=True)
    def run(*cmd, cwd=None): subprocess.run(cmd, cwd=cwd, check=True)
    if not source.exists():
        run('git', 'init', str(source))
        run('git', 'fetch', '--depth', '1', URL, REVISION, cwd=source)
        run('git', 'checkout', '--detach', 'FETCH_HEAD', cwd=source)
    actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip()
    if actual != REVISION: raise SystemExit(f'SameBoy revision mismatch: {actual}')
    # The archive target avoids the optional cppp public-header generator.
    # Our small adapter includes the matching Core headers directly.
    run('make', '-j' + args.jobs, 'build/lib/libsameboy.a', 'CONF=release', 'CC=' + args.cc,
        'DISABLE_REWIND=1', 'DISABLE_DEBUGGER=1', 'DISABLE_CHEATS=1', cwd=source)
    run('make', 'bootroms', 'CONF=release', 'CC=' + args.cc, 'RGBDS=' + args.rgbds, cwd=source)
    run(args.cc, '-std=gnu11', '-O2', '-fPIC', '-shared', '-Wall', '-Wextra', '-Werror',
        '-DGB_DISABLE_REWIND', '-DGB_DISABLE_DEBUGGER', '-DGB_DISABLE_CHEATS',
        '-I', str(source / 'Core'), str(root / 'tests/fixtures/link_pair.c'),
        str(source / 'build/lib/libsameboy.a'), '-lm', '-o', str(root / 'build/link_pair.so'))
    output = root / 'build/test-results/link'
    output.mkdir(parents=True, exist_ok=True)
    (output / 'emulator.json').write_text(json.dumps({'repository': URL, 'commit': REVISION,
        'model': 'CGB E', 'boot_rom': 'SameBoy open-source cgb_boot.bin',
        'license': 'MIT; see the pinned source LICENSE'}, indent=2) + '\n')


if __name__ == '__main__': main()
