# Architecture

How a results row is made, from the open API to the table in the README.

```mermaid
flowchart LR
    API[(Energi Data Service<br/>api.energidataservice.dk)]
    subgraph energidata-mcp [energidata-mcp package, pinned commit]
        CLIENT[api.fetch_records<br/>rate-limit aware HTTP client]
        HOURLY[core.hourly<br/>average to the UTC hour]
    end
    subgraph ptx-dispatch
        FETCH[scripts/fetch_data.py<br/>month-sized windows]
        CSV[(data/*.csv<br/>not committed)]
        JOIN[data.join<br/>hours with price and CO2]
        PARAMS[params.py<br/>DEA PEM 10 MW, 57.5 kWh/kg]
        STRAT[dispatch.py<br/>always on, cheapest N, cleanest N,<br/>price and CO2 thresholds]
        EVAL[dispatch.evaluate<br/>EUR/kg, kg CO2/kg, full-load hours]
        REPORT[report.py<br/>range tested: N, limits, kWh/kg]
        OUT[(results/results.md<br/>results/results.csv)]
    end
    API -- DayAheadPrices 15 min, CO2Emis 5 min --> CLIENT --> HOURLY --> FETCH --> CSV --> JOIN --> STRAT --> EVAL --> REPORT --> OUT
    PARAMS --> EVAL
    OUT --> README[README table]
    VERIFY[verify.py] -. rebuilds and compares .-> OUT
```

- `src/ptx_dispatch/dispatch.py` holds only pure functions, so the unit tests in
  `tests/test_dispatch.py` run on an 8-hour hand-checked series without network.
- `scripts/reproduce.py` runs fetch then analysis; `verify.py` rebuilds the table from
  `data/` and fails if it differs from the committed `results/results.md`.
