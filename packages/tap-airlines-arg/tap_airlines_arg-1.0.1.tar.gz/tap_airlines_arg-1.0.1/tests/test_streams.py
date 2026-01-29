"""Unit tests for stream helpers."""

from __future__ import annotations

from datetime import datetime

from tap_airlines.tap import TapAirlines


def _build_stream(days_back: int = 0):
    tap = TapAirlines(
        config={
            "api_url": "https://example.com/api",
            "api_key": "dummy",
            "airports": ["AEP"],
            "days_back": days_back,
        },
    )
    return tap.discover_streams()[0]


def test_partitions_generate_expected_contexts():
    stream = _build_stream(days_back=0)
    partitions = stream.partitions

    assert len(partitions) == 2  # A/D for one airport and one day
    for ctx in partitions:
        assert ctx["airport_iata"] == "AEP"
        assert ctx["movtp"] in {"A", "D"}
        # date isoformat
        datetime.fromisoformat(ctx["date"])


def test_get_url_params_formats_date_and_sets_metadata():
    stream = _build_stream(days_back=0)
    context = stream.partitions[0]
    params = stream.get_url_params(context, None)

    assert params["c"] == "900"
    assert params["idarpt"] == context["airport_iata"]
    assert params["movtp"] == context["movtp"]

    # dd-MM-YYYY formatting
    date_obj = datetime.fromisoformat(context["date"]).date()
    assert params["f"] == date_obj.strftime("%d-%m-%Y")
    assert "fetched_at" in context


def test_post_process_adds_metadata():
    stream = _build_stream(days_back=0)
    context = stream.partitions[0]
    record = {}
    enriched = stream.post_process(record, context)

    assert enriched["x_airport_iata"] == context["airport_iata"]
    assert enriched["x_movtp"] == context["movtp"]
    assert enriched["x_date"] == context["date"]
    assert "x_fetched_at" in enriched
