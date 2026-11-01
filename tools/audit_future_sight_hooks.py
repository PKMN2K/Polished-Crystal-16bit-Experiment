"""Inventory direct PyBoy hooks on GetFutureSightUser across tests.

Use --strict once all existing direct hooks are migrated to the shared helper.
The default reports all remaining sites without blocking unrelated CI tests.
"""
import argparse
import ast
from pathlib import Path


def audit(root):
    findings = []
    for path in sorted((root / "tests").rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            raise SystemExit(f"Syntax error in {path}: {exc}") from exc
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                continue
            if node.func.id != "hook" or not node.args:
                continue
            if isinstance(node.args[0], ast.Constant) and node.args[0].value == "GetFutureSightUser":
                findings.append((path.relative_to(root), node.lineno))
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    findings = audit(root)
    for path, lineno in findings:
        print(f"::warning file={path},line={lineno}::Use hook_future_sight_after_push instead of a direct entry hook")
    print(f"Future Sight entry-hook audit: {len(findings)} direct registrations remain")
    if args.strict and findings:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
