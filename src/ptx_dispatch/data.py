"""Download hourly spot price and CO2 intensity from Energi Data Service and cache them as CSV.

The HTTP client and the sub-hourly to hourly averaging come from the energidata-mcp package
(same author, public repo), so this repo does not duplicate the API code.
"""

from __future__ import annotations

import csv
import time
from datetime import datetime, timedelta
from pathlib import Path

import anyio
from energidata_mcp import api, core

# dataset, UTC time column, Danish time column, value column, unit
SERIES = {
    "price": ("DayAheadPrices", "TimeUTC", "TimeDK", "DayAheadPriceEUR", "EUR/MWh"),
    "co2": ("CO2Emis", "Minutes5UTC", "Minutes5DK", "CO2Emission", "g CO2/kWh"),
}
CHUNK_DAYS = 31  # one request per month-sized window keeps each answer small


def windows(start: str, end: str, days: int = CHUNK_DAYS) -> list[tuple[str, str]]:
    """Split [start, end) into consecutive windows of at most `days` days."""
    fmt = "%Y-%m-%dT%H:%M"
    a, stop = datetime.strptime(start, fmt), datetime.strptime(end, fmt)
    out = []
    while a < stop:
        b = min(a + timedelta(days=days), stop)
        out.append((a.strftime(fmt), b.strftime(fmt)))
        a = b
    return out


def fetch_series(name: str, area: str, start: str, end: str) -> list[dict]:
    """All hours of one series for one price area, averaged to the hour on the UTC clock."""
    dataset, utc_key, dk_key, value_key, _ = SERIES[name]
    records: list[dict] = []
    for a, b in windows(start, end):
        print(f"  {dataset} {area} {a} to {b} ...", flush=True)
        records += _fetch_with_retry(dataset, a, b, area)
    hours = core.hourly(records, utc_key, dk_key, value_key)
    # windows do not overlap, but keep one row per UTC hour to be safe
    return list({h["hour_utc"]: h for h in hours}.values())


RATE_LIMIT_RETRIES = 5
RATE_LIMIT_PAUSE_S = 65


def _fetch_with_retry(dataset: str, a: str, b: str, area: str) -> list[dict]:
    """The client waits once on HTTP 429; a long download can hit the limit again, so wait and retry."""
    for attempt in range(RATE_LIMIT_RETRIES + 1):
        try:
            return anyio.run(api.fetch_records, dataset, a, b, area)
        except api.ApiError as err:
            if "429" not in str(err) or attempt == RATE_LIMIT_RETRIES:
                raise
            print(f"    rate limited, waiting {RATE_LIMIT_PAUSE_S} s (retry {attempt + 1})", flush=True)
            time.sleep(RATE_LIMIT_PAUSE_S)
    raise AssertionError("unreachable")


def save(hours: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["hour_utc", "hour_dk", "value", "samples"])
        w.writeheader()
        w.writerows(hours)


def load(path: Path) -> dict[str, tuple[str, float]]:
    """Read a cached CSV as {hour_utc: (hour_dk, value)}."""
    with path.open(encoding="utf-8") as f:
        return {r["hour_utc"]: (r["hour_dk"], float(r["value"])) for r in csv.DictReader(f)}


def join(price: dict, co2: dict) -> tuple[list[dict], dict]:
    """Hours that have both a price and a CO2 value, sorted by UTC hour, plus a coverage report."""
    both = sorted(set(price) & set(co2))
    hours = [
        {"hour_utc": h, "hour_dk": price[h][0], "price": price[h][1], "co2": co2[h][1]}
        for h in both
    ]
    report = {
        "price_hours": len(price),
        "co2_hours": len(co2),
        "joined_hours": len(both),
        "price_only": len(set(price) - set(co2)),
        "co2_only": len(set(co2) - set(price)),
    }
    return hours, report
