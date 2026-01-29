"""Tests standard tap features using the built-in SDK tests library."""

from __future__ import annotations

import os
from datetime import datetime, timezone

from singer_sdk.streams import rest as rest_stream
from singer_sdk.testing import get_tap_test_class

from tap_airlines.tap import TapAirlines

# Avoid reading real .env/credentials during SDK contract tests
os.environ["TAP_AIRLINES_API_URL"] = "https://example.com/api"
os.environ["TAP_AIRLINES_API_KEY"] = "dummy"
os.environ["TAP_AIRLINES_AIRPORTS"] = '["AEP"]'


def _fake_request_records(self, context):
    context = context or {
        "airport_iata": "AEP",
        "movtp": "A",
        "date": datetime.now(timezone.utc).date().isoformat(),
    }

    record = {key: None for key in self.schema["properties"].keys()}
    record.update(
        {
            "id": "1",
            "stda": datetime.now(timezone.utc).isoformat(),
        },
    )
    enriched = self.post_process(record, context)
    for key in ("airport_iata", "movtp", "date"):
        enriched.pop(key, None)
    allowed_keys = set(self.schema["properties"].keys())
    yield {key: enriched.get(key) for key in allowed_keys}


rest_stream.RESTStream.request_records = _fake_request_records  # type: ignore[method-assign]

SAMPLE_CONFIG = {
    "api_url": "https://example.com/api",
    "api_key": "dummy",
    "airports": ["AEP"],
}


TestTapAirlines = get_tap_test_class(
    tap_class=TapAirlines,
    config=SAMPLE_CONFIG,
)
