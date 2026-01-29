"""Utility helpers for tap-airlines-arg."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Iterable

DEFAULT_API_URL = "https://webaa-api-h4d5amdfcze7hthn.a02.azurefd.net/web-prod/v1/api-aa"
DEFAULT_API_KEY = "HieGcY2nFreIsNLuo5EbXCwE7g0aRzTN"
DEFAULT_ORIGIN = "https://www.aeropuertosargentina.com"
DEFAULT_USER_AGENT = "Mozilla/5.0"
DEFAULT_LANGUAGE = "es-AR"
DEFAULT_AIRPORTS = ["AEP", "EZE"]
DEFAULT_DAYS_BACK = 1


def parse_airports(raw: Any) -> list[str]:
    """Parse airports value from config or env into a list of IATA codes."""
    if raw is None:
        return []

    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = [part.strip() for part in raw.split(",") if part.strip()]
    elif isinstance(raw, (list, tuple, set)):
        parsed = list(raw)
    else:
        parsed = []

    airports: list[str] = []
    for airport in parsed:
        if airport is None:
            continue
        airport_str = str(airport).strip().upper()
        if airport_str:
            airports.append(airport_str)
    return airports


def require_airports(raw: Any, default: Iterable[str] | None = None) -> list[str]:
    """Return parsed airports or raise a helpful error."""
    airports = parse_airports(raw)
    if not airports and default:
        airports = parse_airports(default)
    if not airports:
        msg = (
            "Config 'airports' must be a JSON array of IATA codes "
            'e.g. ["AEP","EZE"].'
        )
        raise ValueError(msg)
    return airports


def coerce_days_back(raw: Any, default: int = DEFAULT_DAYS_BACK) -> int:
    """Parse days_back into a non-negative integer."""
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = default
    return max(value, 0)


def coerce_language(raw: Any) -> str:
    """Return language header value, defaulting to es-AR."""
    if raw is None:
        return DEFAULT_LANGUAGE
    lang = str(raw).strip()
    return lang or DEFAULT_LANGUAGE


def utc_now_iso() -> str:
    """Return current UTC time as an ISO8601 string with Z suffix."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00",
        "Z",
    )
