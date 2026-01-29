# tap-airlines-arg

[![Python](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12-blue)](#)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Singer tap (Meltano Singer SDK) that pulls Argentina Airports `/all-flights` data and emits JSON records ready for any Singer target.

<details>
<summary>Table of contents</summary>

- [What it does](#what-it-does)
- [Quickstart](#quickstart)
- [Configuration](#configuration)
- [Use cases](#use-cases)
- [Data schema](#data-schema)
- [Performance](#performance)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

</details>

## What it does
- Builds partitions for every airport + movement (A/D) for each day from today back to `days_back`.
- Adds metadata (`x_fetched_at`, `x_airport_iata`, `x_movtp`, `x_date`) while keeping all source fields (`additionalProperties: true`).
- Authenticates via header `Key` plus `Origin`, `User-Agent`, and optional `Accept-Language`.
- Emits a single stream: `aerolineas_all_flights`.

```
API (/all-flights) → tap-airlines-arg → Singer target → Warehouse / files
```

## Quickstart

One flow for both CLI and Meltano users:

```bash
# 1) Install (uv keeps deps pinned)
uv sync

# 2) Minimal config (defaults are public; override api_key if you have a private one)
cat > config.local.json <<'EOF'
{
  "api_url": "https://webaa-api-h4d5amdfcze7hthn.a02.azurefd.net/web-prod/v1/api-aa",
  "api_key": "HieGcY2nFreIsNLuo5EbXCwE7g0aRzTN",
  "airports": ["AEP", "EZE"],
  "days_back": 1,
  "origin": "https://www.aeropuertosargentina.com",
  "user_agent": "Mozilla/5.0",
  "language": "es-AR"
}
EOF

# 3) Run the tap end-to-end (emits JSONL)
uv run tap-airlines-arg --config config.local.json --test=records > output/aerolineas_all_flights.jsonl

# (Optional) Same config via Meltano with target-jsonl
uv run meltano --environment dev run tap-airlines-arg target-jsonl
```

## Configuration

| Parameter    |       Type     |                            Default                              |     Description       |
| ---          | ---            |           ---                                                   |           ---         |
| `api_url`    | string   |`https://webaa-api-h4d5amdfcze7hthn.a02.azurefd.net/web-prod/v1/api-aa`| Base URL`/all-flights`|
| `api_key`    | string         | `HieGcY2nFreIsNLuo5EbXCwE7g0aRzTN`                              | Header `Key` value.   |
| `origin`     | string         | `https://www.aeropuertosargentina.com`                          | header sent to the API|
| `airports`   | array[string]  |`["AEP","EZE"]`                               | IATA codes to query. JSON array preferred|
| `days_back`  | integer        |      `1`                      | Days back from today (UTC, inclusive). `0` = only today.|
| `user_agent` | string         | `Mozilla/5.0`                                                    | `User-Agent` header. |
| `language`   | string         | `es-AR`                                                      | `Accept-Language` header.|

Tips:
- Config keys map to env vars when using `--config=ENV` (e.g., `TAP_AIRLINES_API_KEY`, `TAP_AIRLINES_AIRPORTS`).
- Keep `days_back` small for frequent runs; increase only for backfills.

## Use cases
- Daily sync of arrivals/departures for one or more airports into a warehouse.
- Historical backfill for a short window (e.g., last 7–14 days) to analyze delays or cancellations.
- Lightweight monitoring pipeline that forwards fresh records to a downstream alerting system via a Singer target.

## Data schema
- Core fields include schedule/estimate times (`stda`, `etda`, `atda`), flight identifiers (`id`, `nro`, `idaerolinea`, `aerolinea`), movement (`mov`), status, gate/sector/belt, aircraft info, and weather snippets.
- Metadata appended by the tap: `x_fetched_at`, `x_airport_iata`, `x_movtp`, `x_date`.
- Full schema: `tap_airlines/schemas/aerolineas_all_flights.json` (kept flexible with `additionalProperties: true`).

## Performance
- The endpoint is single-page; expect tens to a few hundred records per airport/day. Typical default run (AEP+EZE, `days_back=1`) stays fast on a laptop.
- Throughput is target-dependent; the tap overhead is minimal and comfortably handles hundreds of records per second.
- Recommended `days_back`: 0–3 for routine jobs, up to 14 for backfills. Beyond that, consider chunking runs to avoid large date spans.

## Troubleshooting
- **Invalid airports format**: must be JSON array (e.g., `["AEP","EZE"]`). Strings like `"AEP,EZE"` are normalized, but empty arrays fail validation. Fix the config and rerun.
- **API authentication failures**: `401/403` responses mean the `Key` header is missing or invalid. Verify `api_key`, `Origin`, and `User-Agent` match the API expectations.
- **Rate limiting**: `429` with retry headers. The tap retries automatically; keep `days_back` small and avoid rapid re-runs. Back off and retry later if limits persist.
- **Empty responses**: typically happens when the airport/movement/date has no flights or dates are out of range. Check `days_back`, confirm the airport code, and inspect logs for the requested `airport/movtp/date`.

## Contributing
Short changes are welcome. Please keep schemas in sync, add/update tests when touching logic, and follow the developer notes in `AGENTS.md`. Open issues or PRs if anything is unclear.
