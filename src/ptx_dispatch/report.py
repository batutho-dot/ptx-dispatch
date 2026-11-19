"""Run every strategy in the range tested and write the results table (Markdown and CSV)."""

from __future__ import annotations

import csv
from dataclasses import replace
from pathlib import Path

from . import dispatch
from .params import KWH_PER_KG_RANGE, Electrolyser

# Range tested on the strategy settings (author's choice, stated in the README).
N_VALUES = [4, 8, 12, 16, 20]
PRICE_LIMITS = [0, 25, 50, 75, 100]  # EUR/MWh
CO2_LIMITS = [50, 100, 150, 200]  # g CO2/kWh

COLUMNS = [
    "strategy", "full_load_hours", "utilisation_pct", "hydrogen_t",
    "eur_per_kg", "eur_per_kg_low", "eur_per_kg_high",
    "kg_co2_per_kg", "kg_co2_per_kg_low", "kg_co2_per_kg_high",
]


def _r(x: float | None, nd: int) -> float | None:
    return None if x is None else round(x, nd)


def rows(hours: list[dict], plant: Electrolyser | None = None,
         n_values=N_VALUES, price_limits=PRICE_LIMITS, co2_limits=CO2_LIMITS) -> list[dict]:
    plant = plant or Electrolyser()
    low = replace(plant, kwh_per_kg=KWH_PER_KG_RANGE["low"])
    high = replace(plant, kwh_per_kg=KWH_PER_KG_RANGE["high"])
    out = []
    for name, fn in dispatch.strategies(n_values, price_limits, co2_limits):
        on = fn(hours)
        c, lo, hi = (dispatch.evaluate(name, hours, on, p) for p in (plant, low, high))
        out.append({
            "strategy": name,
            "full_load_hours": c.full_load_hours,
            "utilisation_pct": round(100 * c.utilisation, 1),
            "hydrogen_t": round(c.hydrogen_t, 1),
            "eur_per_kg": _r(c.eur_per_kg, 2),
            "eur_per_kg_low": _r(lo.eur_per_kg, 2),
            "eur_per_kg_high": _r(hi.eur_per_kg, 2),
            "kg_co2_per_kg": _r(c.kg_co2_per_kg, 2),
            "kg_co2_per_kg_low": _r(lo.kg_co2_per_kg, 2),
            "kg_co2_per_kg_high": _r(hi.kg_co2_per_kg, 2),
        })
    return out


def _fmt(x) -> str:
    return "n/a" if x is None else f"{x:,.2f}" if isinstance(x, float) else f"{x:,}"


def markdown(table: list[dict]) -> str:
    head = ("| Strategy | Full-load hours | Utilisation % | H2 (t) | EUR/kg H2 | EUR/kg range "
            "| kg CO2/kg H2 | kg CO2/kg range |\n|---|---:|---:|---:|---:|---:|---:|---:|\n")
    lines = []
    for r in table:
        lines.append(
            f"| {r['strategy']} | {_fmt(r['full_load_hours'])} | {r['utilisation_pct']:.1f} "
            f"| {r['hydrogen_t']:,.1f} | {_fmt(r['eur_per_kg'])} "
            f"| {_fmt(r['eur_per_kg_low'])} to {_fmt(r['eur_per_kg_high'])} "
            f"| {_fmt(r['kg_co2_per_kg'])} "
            f"| {_fmt(r['kg_co2_per_kg_low'])} to {_fmt(r['kg_co2_per_kg_high'])} |"
        )
    return head + "\n".join(lines) + "\n"


def write(table: list[dict], out_dir: Path, header: str) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    md, csv_path = out_dir / "results.md", out_dir / "results.csv"
    md.write_text(header + "\n" + markdown(table), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(table)
    return md, csv_path
