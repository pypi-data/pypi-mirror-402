#!/usr/bin/env python
"""Generate/refresh the all-flights schema from a live API sample."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

from tap_airlines.utils import (
    DEFAULT_AIRPORTS,
    DEFAULT_API_KEY,
    DEFAULT_API_URL,
    DEFAULT_LANGUAGE,
    DEFAULT_ORIGIN,
    DEFAULT_USER_AGENT,
    parse_airports,
)

SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / "tap_airlines"
    / "schemas"
    / "aerolineas_all_flights.json"
)


def _required_env(name: str, fallback: str | None = None) -> str:
    value = os.getenv(name) or fallback
    if not value:
        sys.exit(f"Missing required environment variable: {name}")
    return value


def _build_headers(api_key: str) -> dict[str, str]:
    return {
        "Key": api_key,
        "Origin": os.getenv("TAP_AIRLINES_ORIGIN", DEFAULT_ORIGIN),
        "User-Agent": os.getenv("TAP_AIRLINES_USER_AGENT", DEFAULT_USER_AGENT),
        "Accept-Language": os.getenv("TAP_AIRLINES_LANGUAGE", DEFAULT_LANGUAGE),
    }


def _coerce_date(raw_date: str | None) -> datetime.date:
    if raw_date:
        try:
            return datetime.fromisoformat(raw_date).date()
        except ValueError as exc:
            msg = "TAP_AIRLINES_DATE must be YYYY-MM-DD if provided."
            raise SystemExit(msg) from exc
    return datetime.now(timezone.utc).date()


def main() -> None:
    api_url = _required_env("TAP_AIRLINES_API_URL", DEFAULT_API_URL).rstrip("/")
    api_key = _required_env("TAP_AIRLINES_API_KEY", DEFAULT_API_KEY)

    airports = parse_airports(os.getenv("TAP_AIRLINES_AIRPORTS") or DEFAULT_AIRPORTS)
    if not airports:
        sys.exit('Set TAP_AIRLINES_AIRPORTS as a JSON array, e.g. ["AEP","EZE"].')

    movtp = os.getenv("TAP_AIRLINES_MOVTP", "A")
    sample_date = _coerce_date(os.getenv("TAP_AIRLINES_DATE"))
    params = {
        "c": "900",
        "idarpt": airports[0],
        "movtp": movtp,
        "f": sample_date.strftime("%d-%m-%Y"),
    }

    url = f"{api_url}/all-flights"
    response = requests.get(
        url,
        headers=_build_headers(api_key),
        params=params,
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    records = payload if isinstance(payload, list) else [payload]

    properties: dict[str, dict[str, object]] = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        for key in record:
            properties.setdefault(key, {"type": ["string", "null"]})

    # Metadata fields we always add
    metadata_fields = {
        "x_fetched_at": {"type": ["string", "null"], "format": "date-time"},
        "x_airport_iata": {"type": ["string", "null"]},
        "x_movtp": {"type": ["string", "null"]},
        "x_date": {"type": ["string", "null"], "format": "date"},
    }
    properties.update({k: properties.get(k, v) for k, v in metadata_fields.items()})
    context_fields = {
        "airport_iata": {"type": ["string", "null"]},
        "movtp": {"type": ["string", "null"]},
        "date": {"type": ["string", "null"], "format": "date"},
    }
    properties.update({k: properties.get(k, v) for k, v in context_fields.items()})

    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": properties,
        "additionalProperties": True,
    }

    SCHEMA_PATH.write_text(
        json.dumps(schema, indent=4, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote schema with {len(properties)} properties to {SCHEMA_PATH}")


if __name__ == "__main__":
    main()
