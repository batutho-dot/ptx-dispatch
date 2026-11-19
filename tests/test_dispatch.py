"""Unit tests on a small fixed series. Every expected value was worked out by hand (shown inline).

Fixture: 2 days x 4 hours. Test plant: 1 MW, 50 kWh/kg, so each 'on' hour = 1 MWh = 20 kg H2.
    day 1  price  10, 40, -5, 30   co2 100,  50, 200,  80
    day 2  price  60, 20, 20, 90   co2 150, 150,  40, 300
"""

from __future__ import annotations

import pytest

from ptx_dispatch import data, dispatch, report
from ptx_dispatch.params import Electrolyser

PRICE = [10, 40, -5, 30, 60, 20, 20, 90]
CO2 = [100, 50, 200, 80, 150, 150, 40, 300]
DAYS = ["2026-01-01"] * 4 + ["2026-01-02"] * 4
HOURS = [
    {"hour_dk": f"{d}T{i % 4:02d}:00", "price": p, "co2": c}
    for i, (d, p, c) in enumerate(zip(DAYS, PRICE, CO2))
]
PLANT = Electrolyser(power_mw=1.0, kwh_per_kg=50.0)


def on_index(flags):
    return [i for i, f in enumerate(flags) if f]


def run(flags):
    return dispatch.evaluate("t", HOURS, flags, PLANT)


def test_always_on():
    r = run(dispatch.always_on(HOURS))
    # 8 h x 1 MW = 8 MWh = 8000 kWh / 50 = 160 kg
    assert r.full_load_hours == 8 and r.electricity_mwh == 8 and r.hydrogen_t == pytest.approx(0.16)
    # cost 10+40-5+30+60+20+20+90 = 265 EUR; 265 / 160 = 1.65625
    assert r.eur_per_kg == pytest.approx(1.65625)
    # CO2 (100+50+200+80+150+150+40+300) g/kWh x 1000 kWh = 1070 kg; 1070 / 160 = 6.6875
    assert r.kg_co2_per_kg == pytest.approx(6.6875)
    assert r.utilisation == 1.0


def test_cheapest_two_per_day_with_tie():
    flags = dispatch.cheapest_n_per_day(HOURS, 2)
    # day 1: -5 (idx 2), 10 (idx 0); day 2: 20 (idx 5), 20 (idx 6)
    assert on_index(flags) == [0, 2, 5, 6]
    r = run(flags)
    # 80 kg; cost 10-5+20+20 = 45 -> 0.5625; CO2 100+200+150+40 = 490 kg -> 6.125
    assert r.eur_per_kg == pytest.approx(0.5625)
    assert r.kg_co2_per_kg == pytest.approx(6.125)


def test_tie_goes_to_earliest_hour():
    # day 2 has 20 at idx 5 and idx 6; n=1 must pick idx 5
    assert on_index(dispatch.cheapest_n_per_day(HOURS, 1)) == [2, 5]


def test_cleanest_two_per_day():
    flags = dispatch.cleanest_n_per_day(HOURS, 2)
    # day 1: 50 (idx 1), 80 (idx 3); day 2: 40 (idx 6), then 150 tie -> earliest idx 4
    assert on_index(flags) == [1, 3, 4, 6]
    r = run(flags)
    # cost 40+30+60+20 = 150 / 80 kg = 1.875; CO2 50+80+150+40 = 320 / 80 = 4.0
    assert r.eur_per_kg == pytest.approx(1.875)
    assert r.kg_co2_per_kg == pytest.approx(4.0)


def test_price_threshold_includes_limit():
    assert on_index(dispatch.threshold(HOURS, "price", 20)) == [0, 2, 5, 6]


def test_negative_price_gives_negative_cost():
    r = run(dispatch.threshold(HOURS, "price", 0))
    # only -5 EUR/MWh hour: 20 kg, -5 EUR -> -0.25; CO2 200 kg / 20 = 10
    assert r.full_load_hours == 1
    assert r.eur_per_kg == pytest.approx(-0.25)
    assert r.kg_co2_per_kg == pytest.approx(10.0)


def test_co2_threshold():
    r = run(dispatch.threshold(HOURS, "co2", 50))
    # idx 1 (50) and idx 6 (40): 40 kg; cost 40+20 = 60 -> 1.5; CO2 90 kg -> 2.25
    assert r.eur_per_kg == pytest.approx(1.5)
    assert r.kg_co2_per_kg == pytest.approx(2.25)


def test_never_on_gives_none_not_zero():
    r = run(dispatch.threshold(HOURS, "price", -100))
    assert r.full_load_hours == 0 and r.eur_per_kg is None and r.kg_co2_per_kg is None


def test_short_day_runs_all_hours():
    short = HOURS[:3]  # like the 23-hour DST day: fewer hours than n
    assert on_index(dispatch.cheapest_n_per_day(short, 4)) == [0, 1, 2]


def test_size_does_not_change_per_kg_results():
    big = Electrolyser(power_mw=10.0, kwh_per_kg=50.0)
    a = run(dispatch.always_on(HOURS))
    b = dispatch.evaluate("t", HOURS, dispatch.always_on(HOURS), big)
    assert b.hydrogen_t == pytest.approx(10 * a.hydrogen_t)
    assert b.eur_per_kg == pytest.approx(a.eur_per_kg)


def test_report_range_scales_with_kwh_per_kg():
    rows = report.rows(HOURS, Electrolyser(power_mw=1.0, kwh_per_kg=57.5), [2], [20], [50])
    always = rows[0]
    # always on: mean price 33.125 EUR/MWh x kWh/kg / 1000
    assert always["eur_per_kg"] == round(33.125 * 57.5 / 1000, 2)  # 1.90
    assert always["eur_per_kg_low"] == round(33.125 * 51.5 / 1000, 2)  # 1.71
    assert always["eur_per_kg_high"] == round(33.125 * 57.58 / 1000, 2)  # 1.91
    assert [r["strategy"] for r in rows] == [
        "Always on", "Cheapest 2 h/day", "Cleanest 2 h/day", "Price <= 20 EUR/MWh", "CO2 <= 50 g/kWh"]


def test_windows_split_and_cover():
    w = data.windows("2025-10-01T00:00", "2025-11-15T00:00", 31)
    assert w == [("2025-10-01T00:00", "2025-11-01T00:00"), ("2025-11-01T00:00", "2025-11-15T00:00")]


def test_join_keeps_only_hours_with_both():
    price = {"a": ("A", 1.0), "b": ("B", 2.0)}
    co2 = {"b": ("B", 9.0), "c": ("C", 3.0)}
    hours, cov = data.join(price, co2)
    assert hours == [{"hour_utc": "b", "hour_dk": "B", "price": 2.0, "co2": 9.0}]
    assert cov["price_only"] == 1 and cov["co2_only"] == 1
