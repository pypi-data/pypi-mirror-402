# AGENTS.md - AI Agent Development Guide for tap-airlines-arg

Guidance for contributors and AI agents working on this Singer tap.

## Project Overview

- **Type**: Singer Tap (Meltano Singer SDK)
- **Source**: blueprintdata / Airports Argentina `/all-flights`
- **Auth**: API Key (header `Key`)
- **Streams**: REST, single stream today (`aerolineas_all_flights`)

## Request Flow Diagram

```
Config → Build Partitions → For each (airport, movtp, date) → API Request → Parse → Enrich → Emit Record
```

## Understanding Partitions

- Defined in `AerolineasAllFlightsStream._build_partitions` (`tap_airlines/streams.py`).
- Dimensions: `airport_iata` (config), `movtp` in `("A","D")`, `date` for each day from `today` back to `days_back` (inclusive, UTC).
- Partitions are cached per run (`self._partitions`), so changes to `days_back` or `airports` require re-instantiation.

## Real API Response Example (/all-flights)

Representative JSON shape (truncated fields):

```json
{
  "id": "7839435",
  "stda": "2024-01-05T12:30:00Z",
  "arpt": "AEP",
  "idaerolinea": "AR",
  "aerolinea": "Aerolíneas Argentinas",
  "mov": "A",
  "nro": "AR1502",
  "status": "Land",
  "destorig": "MDZ",
  "IATAdestorig": "MDZ",
  "etda": "2024-01-05T12:35:00Z",
  "sector": "A",
  "termsec": "A",
  "gate": "15",
  "belt": "3",
  "sdtempunit": "C",
  "sdtemp": "23",
  "sdphrase": "Parcialmente nublado",
  "acftype": "73H",
  "blockon": null,
  "blockoff": null,
  "x_fetched_at": "2024-01-05T12:33:12Z",
  "x_airport_iata": "AEP",
  "x_movtp": "A",
  "x_date": "2024-01-05"
}
```

Fields may vary; the tap keeps `additionalProperties: true`.

## Common Development Tasks

**Test a single partition/context**
- Narrow inputs to reduce contexts: set `airports=["AEP"]` and `days_back=0` in config.
- For a true single-context check, run a Python snippet:
  ```bash
  python3 - <<'PY'
  from tap_airlines.tap import TapAirlines
  tap = TapAirlines(config={
      "api_url": "https://webaa-api-h4d5amdfcze7hthn.a02.azurefd.net/web-prod/v1/api-aa",
      "api_key": "HieGcY2nFreIsNLuo5EbXCwE7g0aRzTN",
      "airports": ["AEP"],
      "days_back": 0,
  })
  stream = tap.discover_streams()[0]
  ctx = stream.partitions[0]
  records = list(stream.get_records(context=ctx))
  print(ctx, len(records))
  PY
  ```

**Debug API requests**
- Run with detailed logs: `LOGLEVEL=DEBUG uv run tap-airlines-arg --config config.json --test=records`.
- Each request logs `airport/movtp/date`. Inspect HTTP status or retry info in the debug output.

**Add a new metadata field**
- Add to `post_process` in `tap_airlines/streams.py` and update the JSON schema (`tap_airlines/schemas/aerolineas_all_flights.json` or regen via `scripts/generate_schema.py`).
- Include the field in tests (`tests/test_streams.py`) to prevent regressions.

**Modify date range logic**
- Edit `_build_partitions` to change the date window or movements. Keep `days_back` non-negative (`coerce_days_back`).
- If adding start/end dates, normalize to UTC and update tests around partition counts.

## Adding a New Stream (complete example)

```python
from singer_sdk import typing as th
from tap_airlines.client import BlueprintdataStream


class MyNewStream(BlueprintdataStream):
    name = "my_new_stream"
    path = "/api/v1/my_resource"
    primary_keys = ("id",)
    replication_key = None

    schema = th.PropertiesList(
        th.Property("id", th.StringType, required=True),
        th.Property("name", th.StringType),
        th.Property("updated_at", th.DateTimeType),
    ).to_dict()

    # Optional: pagination if the endpoint pages
    # def get_new_paginator(self):
    #     return JSONPathPaginator("$.next")
```

Register it in `TapAirlines.discover_streams`:

```python
def discover_streams(self):
    return [
        streams.AerolineasAllFlightsStream(self),
        streams.MyNewStream(self),
    ]
```

## Pagination for this API

- `/all-flights` is single-page; `BlueprintdataStream.get_new_paginator` returns `None`.
- If a new endpoint needs pagination, prefer SDK paginators:
  ```python
  from singer_sdk.pagination import SinglePagePaginator
  def get_new_paginator(self):
      return SinglePagePaginator()
  ```
  Swap in `HeaderLinkPaginator`, `SimpleHeaderPaginator`, or `JSONPathPaginator` as needed.

## State and Incremental Sync

- Current stream is full-table per partition (no `replication_key`).
- State is still emitted so downstream targets can store it; if you add incremental behavior, set `replication_key` and rely on SDK state handling.

## Testing

- Install deps: `uv sync`
- Full suite: `uv run pytest`
- Targeted test: `uv run pytest tests/test_streams.py -k partitions`

## Configuration Reference (dev view)

Defined in `tap_airlines/tap.py` with defaults in `tap_airlines/utils.py`. Env var pattern: `TAP_AIRLINES_<UPPER_KEY>`.

## Best Practices

- Log with context (`airport`, `movtp`, `date`) for traceability.
- Keep schemas permissive but update when adding metadata.
- Avoid direct state mutations; let the SDK handle it.
- Add type hints and tests for new logic.

## File Structure

```
tap-airlines-arg/
├── tap_airlines/
│   ├── tap.py          # Main tap class
│   ├── client.py       # API client + auth/headers
│   ├── streams.py      # Stream definitions, partitions, post-process
│   └── schemas/        # JSON schemas
├── scripts/generate_schema.py
├── tests/
└── README.md, AGENTS.md
```

## Additional Resources

- User docs: `README.md`
- Config reference: `CONFIGURATION.md`
- Quickstart: `QUICKSTART.md`
- Singer SDK: https://sdk.meltano.com
- Singer Spec: https://hub.meltano.com/singer/spec
