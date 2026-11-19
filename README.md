# ptx-dispatch

When should a grid-connected electrolyser run? This repo decides it hour by hour from the
Danish day-ahead spot price and the CO2 intensity of consumed electricity, both from
Energinet's open Energi Data Service. It compares five dispatch strategies and reports, for
each, the electricity cost and the CO2 per kg of hydrogen, and the full-load hours.

Case: a 10 MW PEM electrolyser in price area DK1, 1 October 2025 to 30 September 2026
(8,724 hours with both a price and a CO2 value).

## Results

EUR/kg H2 counts spot electricity only (no grid tariffs, taxes, capex, water or stack
replacement), so it is a lower bound on the cost of hydrogen. kg CO2/kg H2 is
attributional: average intensity of consumed electricity, not marginal emissions.
"Range" re-runs each row with the DEA 2025 lower and upper electricity use
(51.5 and 57.58 kWh/kg) instead of the central 57.5.

| Strategy | Full-load hours | Utilisation % | H2 (t) | EUR/kg H2 | EUR/kg range | kg CO2/kg H2 | kg CO2/kg range |
|---|---:|---:|---:|---:|---:|---:|---:|
| Always on | 8,724 | 100.0 | 1,517.2 | 5.82 | 5.21 to 5.83 | 5.93 | 5.31 to 5.93 |
| Cheapest 4 h/day | 1,456 | 16.7 | 253.2 | 2.81 | 2.52 to 2.82 | 6.57 | 5.89 to 6.58 |
| Cheapest 8 h/day | 2,912 | 33.4 | 506.4 | 3.41 | 3.06 to 3.42 | 6.31 | 5.65 to 6.32 |
| Cheapest 12 h/day | 4,368 | 50.1 | 759.7 | 4.12 | 3.69 to 4.13 | 6.09 | 5.46 to 6.10 |
| Cheapest 16 h/day | 5,823 | 66.7 | 1,012.7 | 4.68 | 4.19 to 4.69 | 5.99 | 5.37 to 6.00 |
| Cheapest 20 h/day | 7,275 | 83.4 | 1,265.2 | 5.19 | 4.65 to 5.20 | 5.94 | 5.32 to 5.95 |
| Cleanest 4 h/day | 1,456 | 16.7 | 253.2 | 5.83 | 5.22 to 5.84 | 3.62 | 3.25 to 3.63 |
| Cleanest 8 h/day | 2,912 | 33.4 | 506.4 | 5.93 | 5.31 to 5.93 | 4.11 | 3.68 to 4.11 |
| Cleanest 12 h/day | 4,368 | 50.1 | 759.7 | 6.01 | 5.38 to 6.01 | 4.55 | 4.08 to 4.56 |
| Cleanest 16 h/day | 5,823 | 66.7 | 1,012.7 | 6.03 | 5.40 to 6.03 | 4.98 | 4.46 to 4.99 |
| Cleanest 20 h/day | 7,275 | 83.4 | 1,265.2 | 5.95 | 5.33 to 5.96 | 5.44 | 4.87 to 5.45 |
| Price <= 0 EUR/MWh | 250 | 2.9 | 43.5 | -0.23 | -0.21 to -0.23 | 8.89 | 7.96 to 8.90 |
| Price <= 25 EUR/MWh | 974 | 11.2 | 169.4 | 0.28 | 0.25 to 0.28 | 7.07 | 6.33 to 7.08 |
| Price <= 50 EUR/MWh | 1,415 | 16.2 | 246.1 | 0.89 | 0.80 to 0.89 | 6.37 | 5.71 to 6.38 |
| Price <= 75 EUR/MWh | 2,468 | 28.3 | 429.2 | 2.08 | 1.86 to 2.08 | 5.45 | 4.88 to 5.46 |
| Price <= 100 EUR/MWh | 4,382 | 50.2 | 762.1 | 3.39 | 3.04 to 3.40 | 5.62 | 5.03 to 5.62 |
| CO2 <= 50 g/kWh | 1,566 | 18.0 | 272.3 | 4.92 | 4.40 to 4.92 | 1.83 | 1.64 to 1.83 |
| CO2 <= 100 g/kWh | 4,404 | 50.5 | 765.9 | 5.64 | 5.05 to 5.65 | 3.48 | 3.12 to 3.49 |
| CO2 <= 150 g/kWh | 6,994 | 80.2 | 1,216.3 | 5.84 | 5.23 to 5.85 | 4.83 | 4.32 to 4.83 |
| CO2 <= 200 g/kWh | 8,397 | 96.3 | 1,460.3 | 5.82 | 5.21 to 5.82 | 5.66 | 5.07 to 5.66 |

Period statistics: spot price mean 101.17, median 99.90, min -31.28, max 738.18 EUR/MWh,
with 250 hours at or below zero. CO2 intensity mean 103.1, median 99.4 g CO2/kWh.
Full output: [results/results.md](results/results.md) and [results/results.csv](results/results.csv).

What the table shows:

- **Price and CO2 pull in opposite directions in DK1 over this year.** Running only in the
  cheapest hours lowers cost (5.82 to 2.81 EUR/kg at 4 h/day) but raises CO2 per kg
  (5.93 to 6.57). Running in the cleanest hours does the reverse (3.62 kg CO2/kg at 4 h/day,
  cost about unchanged at 5.83 EUR/kg).
- **Cheap electricity costs full-load hours.** Every row below 2 EUR/kg runs under
  1,500 full-load hours a year. Once capex is counted (not done here), low full-load hours
  raise the cost per kg again, so the electricity-only optimum is not the plant optimum.
- **Electricity use matters about 10 percent.** Moving from 57.5 to 51.5 kWh/kg lowers both
  EUR/kg and kg CO2/kg by 10.4 percent in every row; the DEA upper value changes them by
  0.1 percent.

## How the model works

- Each hour the plant is either off or at full load (10 MW). Each "on" hour uses 10 MWh and
  makes 10,000 / 57.5 = 173.9 kg H2.
- EUR/kg = mean spot price of the on-hours (EUR/MWh) x 57.5 kWh/kg / 1000.
- kg CO2/kg = mean CO2 intensity of the on-hours (g/kWh) x 57.5 kWh/kg / 1000.
- Full-load hours = number of on-hours (each at 100 percent load).
- Strategies:
  - **Always on**: every hour.
  - **Cheapest N h/day**: the N lowest-price hours of each Danish calendar day.
  - **Cleanest N h/day**: the N lowest-CO2 hours of each Danish calendar day.
  - **Price threshold**: every hour with price at or below the limit.
  - **CO2 threshold**: every hour with CO2 intensity at or below the limit.
  - Ties go to the earliest hour. A day with fewer than N hours runs all of them.

## Assumptions

| Item | Value | Source or reason |
|---|---|---|
| Electrolyser type and size | PEM, 10 MW electricity input | Author's choice; matches DEA data sheet "80 PEMEC 10 MW" |
| Electricity use, stack plus balance of plant | 57.5 kWh/kg H2 (2025 central) | Danish Energy Agency (2026), sheet 80 PEMEC 10 MW |
| Range tested on electricity use | 51.5 to 57.58 kWh/kg (2025 lower, upper) | Same row |
| Load | On/off at 100 percent, hourly | Simplification. DEA lists PEM minimum stack load 15 percent and cold start 15 min (2025), both below the hourly resolution; part load, start-up losses and degradation are not modelled |
| Price area and period | DK1, 2025-10-01 to 2026-10-01 (end exclusive) | Author's choice; DayAheadPrices starts 2025-10-01 |
| Electricity price | Day-ahead spot, EUR/MWh, 15-min values averaged to the hour | Energinet (2026a) |
| CO2 intensity | Measured average of consumed electricity, g CO2/kWh, 5-min values averaged to the hour | Energinet (2026b) |
| Cost scope | Spot electricity only | Author's choice: lower bound |
| Hours used | 8,724 of 8,760; 36 hours have a price but no CO2 value and are left out | Data coverage |

Range tested on the strategy settings: N = 4, 8, 12, 16, 20 h/day; price limits 0, 25, 50,
75, 100 EUR/MWh; CO2 limits 50, 100, 150, 200 g CO2/kWh.

Known limitations:

- CO2Emis is Energinet's initial data; Energinet points to the Declaration Grid Emission
  dataset for later, revised values. One hour (2026-03-29 03:00 Danish time, the night the
  clocks go forward) carries -213.1 g CO2/kWh in the source. It is used as published; it is
  one hour of 8,724.
- Average, not marginal, emissions: a new 10 MW load is assumed not to change the grid mix.
- Perfect foresight: the strategies see the whole day's price and CO2 in advance. Day-ahead
  prices are known the day before; measured CO2 is not.
- No storage or offtake constraint: hydrogen is assumed taken whenever it is made.

## Reproduce

Needs Python 3.11 or newer, git and network access.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python scripts\reproduce.py
.venv\Scripts\python verify.py
```

`reproduce.py` downloads the two series into `data/` (not committed; the API rate limit makes
this take about half an hour), then writes `results/results.md` and `results/results.csv`.
`verify.py` compiles, runs the unit tests, rebuilds the table from `data/` and checks it
matches the committed one, and checks the README carries it.

The API calls go through the client of
[energidata-mcp](https://github.com/batutho-dot/energidata-mcp), installed from a pinned
commit, so the two repos share one tested Energi Data Service client.

Layout: [docs/architecture.md](docs/architecture.md) (diagram),
`src/ptx_dispatch/` (parameters, data, dispatch, report), `scripts/` (fetch, analyse,
reproduce), `tests/` (unit tests on an 8-hour hand-checked series).

## Sources

Danish Energy Agency (2026) *Technology data for energy carrier generation and conversion:
data sheets* (version 0015, sheet '80 PEMEC 10 MW') [Excel workbook]. Copenhagen: Danish
Energy Agency. Available at: https://ens.dk/en/analyses-and-statistics/technology-data-renewable-fuels
(Accessed: 19 November 2026).

Energinet (2026a) *Day-Ahead Prices* [dataset]. Energi Data Service. Available at:
https://www.energidataservice.dk/tso-electricity/DayAheadPrices (Accessed: 19 November 2026).

Energinet (2026b) *CO2 Emission* [dataset]. Energi Data Service. Available at:
https://www.energidataservice.dk/tso-electricity/CO2Emis (Accessed: 19 November 2026).

## Licence

MIT, see [LICENSE](LICENSE). The DEA data sheets are licensed CC BY 4.0 (stated in the workbook).
