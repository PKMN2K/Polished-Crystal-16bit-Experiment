#!/usr/bin/env python3
"""Run each native-species CPU regression in a bounded, isolated process."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--timeout", type=float, default=90)
    parser.add_argument("--pattern", default="test_*.py")
    parser.add_argument("--output", type=Path, default=Path("build/test-results"))
    args = parser.parse_args()
    if args.jobs < 1 or args.timeout <= 0:
        parser.error("--jobs and --timeout must be positive")
    root = Path(__file__).resolve().parents[1]
    rom = args.rom.resolve()
    if not rom.is_file() or not rom.with_suffix(".sym").is_file():
        parser.error("ROM and matching .sym file are required")
    tests = sorted((root / "tests").glob(args.pattern))
    if not tests:
        parser.error("no tests match --pattern")
    args.output.mkdir(parents=True, exist_ok=True)

    def run(path):
        start = time.monotonic()
        logfile = args.output / (path.stem + ".log")
        with logfile.open("w") as log:
            try:
                result = subprocess.run(
                    [sys.executable, "-u", str(path), str(rom)],
                    cwd=root, stdout=log, stderr=subprocess.STDOUT,
                    timeout=args.timeout, check=False,
                )
                status = "passed" if result.returncode == 0 else "failed"
                code = result.returncode
            except subprocess.TimeoutExpired:
                status, code = "timeout", 124
                log.write(f"\nExceeded {args.timeout:g}s; test process terminated.\n")
        return dict(test=path.name, status=status, returncode=code,
                    seconds=round(time.monotonic() - start, 3), log=str(logfile))

    results = []
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(run, test) for test in tests]
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(f"{len(results)}/{len(tests)} {result['status']}: "
                  f"{result['test']} ({result['seconds']}s)", flush=True)
    results.sort(key=lambda result: result["test"])
    (args.output / "summary.json").write_text(json.dumps(results, indent=2) + "\n")
    failed = [result for result in results if result["status"] != "passed"]
    print(f"{len(results) - len(failed)}/{len(results)} test programs passed; "
          f"{len(failed)} failed or timed out.")
    return bool(failed)


if __name__ == "__main__":
    raise SystemExit(main())
