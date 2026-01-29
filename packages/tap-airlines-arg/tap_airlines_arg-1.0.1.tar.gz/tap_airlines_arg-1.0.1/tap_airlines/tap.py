"""tap-airlines-arg tap class (Aerolíneas / Aeropuertos Argentina)."""

from __future__ import annotations

import sys
from typing import Any

from singer_sdk import Tap
from singer_sdk import typing as th  # JSON schema typing helpers

from tap_airlines import streams
from tap_airlines.utils import (
    DEFAULT_AIRPORTS,
    DEFAULT_API_KEY,
    DEFAULT_API_URL,
    DEFAULT_DAYS_BACK,
    DEFAULT_LANGUAGE,
    DEFAULT_ORIGIN,
    DEFAULT_USER_AGENT,
    require_airports,
)

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override


class TapAirlines(Tap):
    """Singer tap para extraer vuelos desde el endpoint /all-flights."""

    name = "tap-airlines-arg"
    default_config = {
        "api_url": DEFAULT_API_URL,
        "api_key": DEFAULT_API_KEY,
        "origin": DEFAULT_ORIGIN,
        "airports": DEFAULT_AIRPORTS,
        "days_back": DEFAULT_DAYS_BACK,
        "user_agent": DEFAULT_USER_AGENT,
        "language": DEFAULT_LANGUAGE,
    }

    # Config esperada (mapea a env vars TAP_AIRLINES_*)
    config_jsonschema = th.PropertiesList(
        th.Property(
            "api_url",
            th.StringType(nullable=False),
            required=True,
            title="API URL",
            default=DEFAULT_API_URL,
            description="Base URL del API (sin /all-flights).",
        ),
        th.Property(
            "api_key",
            th.StringType(nullable=False),
            required=True,
            secret=True,
            title="API Key",
            default=DEFAULT_API_KEY,
            description="Valor del header 'Key' requerido por el endpoint.",
        ),
        th.Property(
            "origin",
            th.StringType(nullable=True),
            required=False,
            title="Origin",
            default=DEFAULT_ORIGIN,
            description="Valor del header Origin.",
        ),
        th.Property(
            "airports",
            th.ArrayType(th.StringType(nullable=False), nullable=False),
            required=True,
            title="Airports (IATA)",
            default=DEFAULT_AIRPORTS,
            description="Lista de aeropuertos IATA a consultar. Ej: ['AEP','EZE']",
        ),
        th.Property(
            "days_back",
            th.IntegerType(nullable=True),
            required=False,
            default=DEFAULT_DAYS_BACK,
            title="Days Back",
            description="Cuántos días hacia atrás consultar (1 = hoy y ayer).",
        ),
        th.Property(
            "user_agent",
            th.StringType(nullable=True),
            required=False,
            default=DEFAULT_USER_AGENT,
            title="User Agent",
            description="User-Agent para enviar en requests.",
        ),
        th.Property(
            "language",
            th.StringType(nullable=True),
            required=False,
            default=DEFAULT_LANGUAGE,
            title="Language",
            description="Header Accept-Language (default es-AR).",
        ),
    ).to_dict()

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the tap and normalize config."""
        super().__init__(*args, **kwargs)
        merged_config = {**self.default_config, **dict(self.config)}
        self._config = merged_config
        self._airports = require_airports(
            self.config.get("airports"),
            default=DEFAULT_AIRPORTS,
        )
        self._language = str(self.config.get("language") or DEFAULT_LANGUAGE)

    @property
    def airports(self) -> list[str]:
        """Normalized airports list."""
        return self._airports

    @property
    def language(self) -> str:
        """Preferred language header."""
        return self._language

    @override
    def discover_streams(self) -> list[streams.AerolineasAllFlightsStream]:
        """Return a list of discovered streams."""
        return [
            streams.AerolineasAllFlightsStream(self),
        ]

    def run_connection_test(self) -> bool:  # type: ignore[misc]
        """Override to avoid aborting after 1 record during `--test=records`."""
        return self.run_sync_dry_run(dry_run_record_limit=None, streams=self.streams.values())


if __name__ == "__main__":
    TapAirlines.cli()
