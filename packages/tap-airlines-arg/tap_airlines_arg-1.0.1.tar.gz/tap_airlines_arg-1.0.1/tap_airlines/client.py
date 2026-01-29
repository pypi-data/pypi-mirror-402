"""REST client handling, including BlueprintdataStream base class."""

from __future__ import annotations

import decimal
import sys
from functools import cached_property
from typing import TYPE_CHECKING, Any

from singer_sdk.authenticators import APIKeyAuthenticator
from singer_sdk.helpers.jsonpath import extract_jsonpath
from singer_sdk.streams import RESTStream

from tap_airlines.utils import (
    DEFAULT_AIRPORTS,
    DEFAULT_LANGUAGE,
    DEFAULT_ORIGIN,
    DEFAULT_USER_AGENT,
    coerce_language,
    coerce_days_back,
    require_airports,
)

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

if TYPE_CHECKING:
    from collections.abc import Iterable

    import requests
    from singer_sdk.helpers.types import Context
    from tap_airlines.tap import TapAirlines


class BlueprintdataStream(RESTStream):
    """Base stream para Aeropuertos Argentina (all-flights)."""

    records_jsonpath = "$[*]"
    extra_retry_statuses = (429, 500, 502, 503, 504)

    @cached_property
    def airports(self) -> list[str]:
        """Airports parsed from config."""
        tap = getattr(self, "_tap", None)
        if tap and "TapAirlines" in globals() and isinstance(tap, TapAirlines):
            return list(tap.airports)
        return require_airports(self.config.get("airports"), default=DEFAULT_AIRPORTS)

    @cached_property
    def days_back(self) -> int:
        """Non-negative days_back value."""
        return coerce_days_back(self.config.get("days_back"))

    @cached_property
    def language(self) -> str:
        """Language header value."""
        tap = getattr(self, "_tap", None)
        if tap and "TapAirlines" in globals() and isinstance(tap, TapAirlines):
            return str(tap.language)
        return coerce_language(self.config.get("language"))

    @cached_property
    def origin(self) -> str:
        """Origin header value."""
        return str(self.config.get("origin") or DEFAULT_ORIGIN)

    @cached_property
    def user_agent(self) -> str:
        """User-Agent header value."""
        return str(self.config.get("user_agent") or DEFAULT_USER_AGENT)

    @override
    @property
    def url_base(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        return self.config["api_url"].rstrip("/")

    @override
    @property
    def authenticator(self) -> APIKeyAuthenticator:
        """Return API key authenticator (header Key: <api_key>)."""
        return APIKeyAuthenticator(
            key="Key",
            value=self.config["api_key"],
            location="header",
        )

    @override
    @property
    def http_headers(self) -> dict[str, str]:
        """Headers requeridos por el endpoint."""
        return {
            "Origin": self.origin,
            "User-Agent": self.user_agent,
            "Accept-Language": self.language or DEFAULT_LANGUAGE,
        }

    @override
    def get_new_paginator(self) -> None:
        """Sin paginación para este endpoint."""
        return None

    @override
    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parsea la respuesta JSON (lista)."""
        yield from extract_jsonpath(
            self.records_jsonpath,
            input=response.json(parse_float=decimal.Decimal),
        )
