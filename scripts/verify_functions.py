"""Function-by-function check. Runs the tests under coverage, then for every function in src/opsmcp says how much of it the tests ran,
and which test files mention it by name. Writes docs/verification.md. Run from the repo folder:  .venv/bin/python scripts/verify_functions.py"""
import ast
import json
import pathlib
import re
import subprocess
import sys

root = pathlib.Path(__file__).resolve().parents[1]
py = sys.executable
subprocess.run([py, "-m", "coverage", "run", "--source=src/opsmcp", "-m", "pytest", "-q"], cwd=root, check=True, capture_output=True)
subprocess.run([py, "-m", "coverage", "json", "-q", "-o", ".cov.json"], cwd=root, check=True)
cov = json.loads((root / ".cov.json").read_text())["files"]
tests = {p.name: p.read_text() for p in (root / "tests").glob("test_*.py")}
rows = []
for rel, data in sorted(cov.items()):
    path = root / rel
    tree = ast.parse(path.read_text())
    ran, missed = set(data["executed_lines"]), set(data["missing_lines"])
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            stmts = {n.lineno for n in ast.walk(node) if isinstance(n, ast.stmt) and n is not node}
            total, miss = len(stmts & (ran | missed)), sorted(stmts & missed)
            named = sorted(t for t, body in tests.items() if re.search(rf"\b{re.escape(node.name)}\b", body))
            rows.append((path.name, node.lineno, node.name, total, miss, named))
full = sum(1 for r in rows if not r[4])
out = ["# Function-by-function check", "", f"Made by `scripts/verify_functions.py`. {len(rows)} functions, {full} fully run by the tests, {len(rows) - full} with lines the tests never reach.", "",
       "| File | Line | Function | Lines run | Missing lines | Tests that name it |", "|---|---|---|---|---|---|"]
for name, line, fn, total, miss, named in sorted(rows):
    out.append(f"| {name} | {line} | `{fn}` | {total - len(miss)}/{total} | {', '.join(map(str, miss[:8])) or '-'} | {', '.join(n.replace('test_', '').replace('.py', '') for n in named[:4]) or '(only through other tests)'} |")
(root / "docs" / "verification.md").write_text("\n".join(out) + "\n")
(root / ".cov.json").unlink()
print(f"functions: {len(rows)}, fully run: {full}, with gaps: {len(rows) - full}")
for name, line, fn, total, miss, _ in sorted(rows):
    if miss:
        print(f"  {name}:{line} {fn}  missing lines {miss[:10]}")
