"""tap-airlines-arg entry point."""

from __future__ import annotations

from tap_airlines.tap import TapAirlines

TapAirlines.cli()
