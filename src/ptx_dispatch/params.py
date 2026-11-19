"""Every technical number the model uses, with the place it comes from.

Source for the electrolyser: Danish Energy Agency (2026) Technology Data: Renewable fuels,
version 0015, data sheet "80 PEMEC 10 MW" (file data_sheets_for_renewable_fuels_15_with_index_
alldata_long.xlsx, downloaded 2026-11-19 from https://ens.dk/en/analyses-and-statistics/
technology-data-renewable-fuels). Row "Electricity consumption [stack+BOP level, kWh/kgH2]",
year 2025: central 57.5, lower 51.5, upper 57.58. Row "Typical total plant size [MW input_e]": 10.

Choices made by the author (not from a source): the 10 MW size, PEM over alkaline, the 2025
column, price area DK1, the period, spot price only, measured average CO2 intensity.
"""

from __future__ import annotations

from dataclasses import dataclass

DEA_SHEET = "Danish Energy Agency (2026), Technology Data: Renewable fuels v0015, sheet 80 PEMEC 10 MW"


@dataclass(frozen=True)
class Electrolyser:
    """A grid-connected electrolyser run on/off at full load, hour by hour."""

    power_mw: float = 10.0  # DEA sheet 80 PEMEC 10 MW, "Typical total plant size [MW input_e]"
    kwh_per_kg: float = 57.5  # DEA sheet 80 PEMEC 10 MW, stack+BOP, 2025 central


# Range tested on electricity use: DEA 2025 lower and upper estimates, same row.
KWH_PER_KG_RANGE = {"low": 51.5, "central": 57.5, "high": 57.58}

# Run settings (author's choices, stated in the README).
AREA = "DK1"
PERIOD_START = "2025-10-01T00:00"  # Danish local time; DayAheadPrices starts 2025-10-01
PERIOD_END = "2026-10-01T00:00"  # exclusive
