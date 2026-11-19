"""Check this repository end to end. Prints `verify: PASS` or `verify: FAIL at <step>: <reason>`.

Steps: compile, unit tests, results table rebuilt from data/ matches results/results.md (skipped
with a note when data/ has not been downloaded), README carries that table, repo hygiene (no em
dashes, licence line, data/ not tracked). Usage: python verify.py (uses .venv's Python if present).
Changes nothing in the repo.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_PY = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
PY = str(VENV_PY if VENV_PY.exists() else Path(sys.executable))
ENV = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(ROOT / "src")}
TEXT = {".py", ".md", ".toml", ".txt", ".csv", ".gitignore"}


class Fail(Exception):
    pass


def step_compile():
    files = [p for d in ("src", "tests", "scripts") for p in (ROOT / d).rglob("*.py")] + [ROOT / "verify.py"]
    for path in files:
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except SyntaxError as exc:
            raise Fail(f"{path.relative_to(ROOT)}:{exc.lineno}: {exc.msg}")
    return f"{len(files)} .py files compile"


def step_tests():
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run([PY, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--basetemp", tmp],
                           cwd=ROOT, env=ENV, capture_output=True, text=True)
    last = (r.stdout.strip().splitlines() or ["no output"])[-1]
    if r.returncode != 0:
        raise Fail(last)
    return last


def _table(md: str) -> list[str]:
    return [line for line in md.splitlines() if line.startswith("| ")]


def step_results():
    """Rebuild the table from the downloaded data and compare it with the committed one."""
    sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
    committed = ROOT / "results" / "results.md"
    if not committed.exists():
        raise Fail("results/results.md missing; run python scripts/reproduce.py")
    from fetch_data import path_for  # noqa: PLC0415
    from ptx_dispatch import data, report  # noqa: PLC0415

    if not (path_for("price").exists() and path_for("co2").exists()):
        return "data/ not downloaded, rebuild skipped (run python scripts/fetch_data.py)"
    hours, cov = data.join(data.load(path_for("price")), data.load(path_for("co2")))
    if cov["joined_hours"] < 8000:
        raise Fail(f"only {cov['joined_hours']} joined hours; expected about 8760")
    fresh = _table(report.markdown(report.rows(hours)))
    old = _table(committed.read_text(encoding="utf-8"))
    if fresh != old:
        diff = next((f"{a!r} vs {b!r}" for a, b in zip(fresh, old) if a != b), "row count differs")
        raise Fail(f"rebuilt table differs from results/results.md: {diff}")
    return f"{len(fresh) - 1} table rows rebuilt from {cov['joined_hours']} hours match results/results.md"


def step_readme():
    table = _table((ROOT / "results" / "results.md").read_text(encoding="utf-8"))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    missing = [row for row in table if row not in readme]
    if missing:
        raise Fail(f"README lacks {len(missing)} results rows, first: {missing[0][:80]}")
    for needed in ("## Sources", "## Assumptions", "Danish Energy Agency", "Energinet"):
        if needed not in readme:
            raise Fail(f"README has no {needed!r}")
    if "```mermaid" not in (ROOT / "docs" / "architecture.md").read_text(encoding="utf-8"):
        raise Fail("docs/architecture.md has no Mermaid diagram")
    return "README carries the results table, assumptions, sources; Mermaid diagram present"


def step_hygiene():
    tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split()
    if any(t.startswith("data/") for t in tracked):
        raise Fail("data/ is tracked by git; it must be downloaded, not committed")
    files = [ROOT / t for t in tracked] or [p for p in ROOT.rglob("*") if ".venv" not in p.parts]
    for p in files:
        if p.is_file() and (p.suffix in TEXT or p.name in TEXT):
            if chr(0x2014) in p.read_text(encoding="utf-8"):
                raise Fail(f"em dash in {p.relative_to(ROOT)}")
    if "Copyright (c) 2026 Batu Thoms" not in (ROOT / "LICENSE").read_text(encoding="utf-8"):
        raise Fail("LICENSE copyright line wrong")
    return f"{len(files)} files: no em dashes, data/ untracked, licence line ok"


STEPS = [("compile", step_compile), ("tests", step_tests), ("results", step_results),
         ("readme", step_readme), ("hygiene", step_hygiene)]


def main() -> int:
    print(f"verify-repo: {ROOT}")
    for name, fn in STEPS:
        try:
            print(f"{name}: {fn()}")
        except Fail as exc:
            print(f"verify: FAIL at {name}: {exc}")
            return 1
        except Exception as exc:  # an unexpected crash is a failure of that step
            print(f"verify: FAIL at {name}: {type(exc).__name__}: {exc}")
            return 1
    print("verify: PASS")
    return 0


if __name__ == "__main__":
    if VENV_PY.exists() and Path(sys.executable).resolve() != VENV_PY.resolve():
        sys.exit(subprocess.run([PY, __file__, *sys.argv[1:]]).returncode)
    sys.exit(main())
