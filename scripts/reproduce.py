"""One command from a clean checkout to the results table: download (if missing), then analyse.

Usage: python scripts/reproduce.py [--force]
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fetch_data  # noqa: E402
import run_analysis  # noqa: E402

if __name__ == "__main__":
    fetch_data.main(force="--force" in sys.argv)
    run_analysis.main()
