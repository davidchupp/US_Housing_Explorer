# US Housing Price Explorer

Explore and estimate US home prices from public sales data.

Public property-sales data is messy: every county names its columns differently,
prices come as `"$415,000"`, coordinates are sometimes `(0, 0)`, and duplicates are
common. This project turns that into a clean, consistent dataset and builds analysis,
an API and a map on top of it.

## Status

| Milestone | Status |
|---|---|
| 1. Ingestion & cleaning pipeline, CLI, tests, CI | ✅ done |
| 2. REST API (FastAPI) for summaries and lookups | ⏳ next |
| 3. Geospatial features from OpenStreetMap (schools, transit, parks) | planned |
| 4. Price-estimate model | planned |
| 5. Interactive web map | planned |

## Quick start

```bash
git clone https://github.com/davidchupp/US_Housing_Explorer.git
cd US_Housing_Explorer
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

pytest                                            # run tests
housing-explorer clean data/sample/sales_sample.csv -o data/processed/clean.csv
housing-explorer summary data/sample/sales_sample.csv
```

Example output:

```
rows in: 14  rows kept: 9
  dropped      1  coordinates_outside_us
  dropped      1  duplicate
  dropped      1  missing_required_value
  dropped      1  price_out_of_range
  dropped      1  sqft_out_of_range
```

## How cleaning works

1. **Column mapping:** known aliases (`Sale Price`, `price`, `SALEPRICE` …) map to one schema.
2. **Type parsing:** currency strings, thousands separators, dates and ZIP+4 codes are normalised.
3. **Validation:** rows are dropped, with a reason, when required values are missing,
   prices or square footage are implausible, or coordinates fall outside the US.
4. **Deduplication:** by sale ID when available, otherwise by price + date + location.
5. **Derived fields:** `price_per_sqft`.

Every dropped row is counted in a `CleaningReport`, so nothing disappears silently.

## Project layout

```
src/housing_explorer/
  ingest.py   load + clean raw CSVs
  geo.py      distance helpers (haversine, nearest point)
  stats.py    summaries by ZIP code and month
  cli.py      command-line interface
tests/        pytest suite
data/sample/  small hand-made sample used by the tests (not real sales)
```

## Data sources (planned)

- County assessor / open-data portal sales exports
- US Census American Community Survey (income, housing by tract)
- OpenStreetMap (points of interest)

## License

MIT
