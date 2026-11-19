"""Dispatch strategies and the per-kg results. Pure functions, no network, no files.

An hour is a dict with at least: hour_dk ("YYYY-MM-DDTHH:MM", Danish time), price (EUR/MWh)
and co2 (g CO2/kWh). A strategy returns one bool per hour: run at full load, or stay off.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from .params import Electrolyser


def always_on(hours: list[dict]) -> list[bool]:
    return [True] * len(hours)


def lowest_n_per_day(hours: list[dict], key: str, n: int) -> list[bool]:
    """Run in the n hours with the lowest `key` on each Danish calendar day. Ties go to the earliest hour.

    A day with fewer than n hours (missing data, or the 23-hour DST day) runs in all of them.
    """
    if n < 0:
        raise ValueError("n must be 0 or more")
    days: dict[str, list[int]] = defaultdict(list)
    for i, h in enumerate(hours):
        days[h["hour_dk"][:10]].append(i)
    on = [False] * len(hours)
    for idx in days.values():
        for i in sorted(idx, key=lambda i: (hours[i][key], i))[:n]:
            on[i] = True
    return on


def cheapest_n_per_day(hours: list[dict], n: int) -> list[bool]:
    return lowest_n_per_day(hours, "price", n)


def cleanest_n_per_day(hours: list[dict], n: int) -> list[bool]:
    return lowest_n_per_day(hours, "co2", n)


def threshold(hours: list[dict], key: str, limit: float) -> list[bool]:
    """Run whenever `key` is at or below `limit`."""
    return [h[key] <= limit for h in hours]


@dataclass(frozen=True)
class Result:
    strategy: str
    hours_total: int
    full_load_hours: int
    electricity_mwh: float
    hydrogen_t: float
    eur_per_kg: float | None
    kg_co2_per_kg: float | None

    @property
    def utilisation(self) -> float:
        return self.full_load_hours / self.hours_total if self.hours_total else 0.0


def evaluate(name: str, hours: list[dict], on: list[bool], plant: Electrolyser) -> Result:
    """Totals for one strategy. Each 'on' hour draws plant.power_mw for one hour.

    EUR/kg  = sum(price x MWh) / kg H2 = mean on-hour price [EUR/MWh] x kWh/kg / 1000
    kg CO2/kg = sum(g/kWh x kWh) / 1000 / kg H2 = mean on-hour CO2 [g/kWh] x kWh/kg / 1000
    """
    if len(on) != len(hours):
        raise ValueError("one on/off flag per hour")
    run = [h for h, flag in zip(hours, on) if flag]
    mwh = plant.power_mw * len(run)
    kg = mwh * 1000 / plant.kwh_per_kg
    cost = sum(h["price"] * plant.power_mw for h in run)  # EUR
    co2_kg = sum(h["co2"] * plant.power_mw * 1000 for h in run) / 1000  # g/kWh x kWh -> g -> kg
    return Result(
        strategy=name,
        hours_total=len(hours),
        full_load_hours=len(run),
        electricity_mwh=mwh,
        hydrogen_t=kg / 1000,
        eur_per_kg=cost / kg if kg else None,
        kg_co2_per_kg=co2_kg / kg if kg else None,
    )


def strategies(n_values: list[int], price_limits: list[float], co2_limits: list[float]):
    """(name, function of hours -> on flags) for every strategy and setting in the range tested."""
    out = [("Always on", always_on)]
    out += [(f"Cheapest {n} h/day", lambda hs, n=n: cheapest_n_per_day(hs, n)) for n in n_values]
    out += [(f"Cleanest {n} h/day", lambda hs, n=n: cleanest_n_per_day(hs, n)) for n in n_values]
    out += [(f"Price <= {p:g} EUR/MWh", lambda hs, p=p: threshold(hs, "price", p)) for p in price_limits]
    out += [(f"CO2 <= {c:g} g/kWh", lambda hs, c=c: threshold(hs, "co2", c)) for c in co2_limits]
    return out
