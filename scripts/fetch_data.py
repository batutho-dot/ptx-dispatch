"""Download the hourly series the analysis needs into data/ (not committed).

Usage: python scripts/fetch_data.py [--force]
Energi Data Service rate-limits hard; the client waits when asked, so a full year takes minutes.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ptx_dispatch import data, params  # noqa: E402

DATA_DIR = ROOT / "data"


def path_for(name: str) -> Path:
    return DATA_DIR / f"{name}_{params.AREA}_{params.PERIOD_START[:10]}_{params.PERIOD_END[:10]}.csv"


def main(force: bool = False) -> None:
    for name in data.SERIES:
        path = path_for(name)
        if path.exists() and not force:
            print(f"{path.relative_to(ROOT)} exists, skipping (use --force to refetch)")
            continue
        print(f"Fetching {name} for {params.AREA}, {params.PERIOD_START} to {params.PERIOD_END}")
        hours = data.fetch_series(name, params.AREA, params.PERIOD_START, params.PERIOD_END)
        data.save(hours, path)
        print(f"  wrote {len(hours)} hours to {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main(force="--force" in sys.argv)
