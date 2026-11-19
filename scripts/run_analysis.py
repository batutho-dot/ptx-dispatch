"""Build the results table from the cached data in data/ and write results/results.md and .csv.

Usage: python scripts/run_analysis.py   (run scripts/fetch_data.py first, or use reproduce.py)
"""

from __future__ import annotations

import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from fetch_data import path_for  # noqa: E402
from ptx_dispatch import data, params, report  # noqa: E402
from ptx_dispatch.params import Electrolyser  # noqa: E402


def main() -> None:
    price, co2 = data.load(path_for("price")), data.load(path_for("co2"))
    hours, cov = data.join(price, co2)
    plant = Electrolyser()
    p = [h["price"] for h in hours]
    c = [h["co2"] for h in hours]
    header = (
        f"# Results: {plant.power_mw:g} MW PEM electrolyser, {params.AREA}, "
        f"{params.PERIOD_START[:10]} to {params.PERIOD_END[:10]} (end exclusive)\n\n"
        f"Hours with both price and CO2: {cov['joined_hours']} "
        f"(price only: {cov['price_only']}, CO2 only: {cov['co2_only']}). "
        f"Electricity use {plant.kwh_per_kg} kWh/kg (range {params.KWH_PER_KG_RANGE['low']} "
        f"to {params.KWH_PER_KG_RANGE['high']}). Spot price only, no tariffs, taxes or capex.\n\n"
        f"Spot price over the period: mean {statistics.mean(p):.2f}, median {statistics.median(p):.2f}, "
        f"min {min(p):.2f}, max {max(p):.2f} EUR/MWh; hours at or below 0: {sum(x <= 0 for x in p)}.  \n"
        f"CO2 intensity: mean {statistics.mean(c):.1f}, median {statistics.median(c):.1f}, "
        f"min {min(c):.1f}, max {max(c):.1f} g CO2/kWh.\n"
    )
    table = report.rows(hours, plant)
    md, csv_path = report.write(table, ROOT / "results", header)
    print(md.read_text(encoding="utf-8"))
    print(f"wrote {md.relative_to(ROOT)} and {csv_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
