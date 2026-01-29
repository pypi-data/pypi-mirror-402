"""Stream type classes for tap-airlines-arg."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Mapping, cast

from singer_sdk import SchemaDirectory, StreamSchema
from singer_sdk.helpers.types import Context
from tap_airlines import schemas

from tap_airlines.client import BlueprintdataStream
from tap_airlines.utils import utc_now_iso

SCHEMAS_DIR = SchemaDirectory(schemas)


class AerolineasAllFlightsStream(BlueprintdataStream):
    """Vuelos (arrivals/departures) desde /all-flights."""

    name = "aerolineas_all_flights"
    path = "/all-flights"
    primary_keys = ("id",)
    replication_key = None

    # La API devuelve una lista, así que la base (client) debe parsear bien la respuesta.
    # Schema mínimo (después lo completamos con campos reales)
    schema = StreamSchema(SCHEMAS_DIR, key="aerolineas_all_flights")

    _partitions: list[dict[str, Any]] | None = None

    @property
    def partitions(self) -> list[dict[str, Any]]:
        """Generate contexts for (airport, movtp, date)."""
        if self._partitions is None:
            self._partitions = self._build_partitions()
        return self._partitions

    def _build_partitions(self) -> list[dict[str, Any]]:
        partitions: list[dict[str, Any]] = []
        today = datetime.now(timezone.utc).date()
        for airport_iata in self.airports:
            for movtp in ("A", "D"):
                for offset in range(0, self.days_back + 1):
                    date_value = today - timedelta(days=offset)
                    partitions.append(
                        {
                            "airport_iata": airport_iata,
                            "movtp": movtp,
                            "date": date_value.isoformat(),
                        },
                    )
        return partitions

    def get_url_params(self, context: Context | None, next_page_token: Any | None):
        """Build request params for each context."""
        if isinstance(context, dict):
            ctx: dict[str, Any] = cast(dict[str, Any], context)
        elif context is not None:
            ctx = dict(context)
        else:
            ctx = {}

        airport = ctx.get("airport_iata")
        movtp = ctx.get("movtp")
        date_iso = ctx.get("date")

        if not isinstance(date_iso, str):
            msg = f"Context date must be ISO format string, got {date_iso!r}"
            raise ValueError(msg)

        try:
            date_obj = datetime.fromisoformat(date_iso).date()
        except Exception as exc:  # noqa: BLE001
            msg = f"Context date must be ISO format, got {date_iso!r}"
            raise ValueError(msg) from exc

        formatted_date = date_obj.strftime("%d-%m-%Y")
        ctx.setdefault("fetched_at", utc_now_iso())

        self.logger.info(
            "Requesting flights",
            extra={
                "airport": airport,
                "movtp": movtp,
                "date": date_iso,
            },
        )

        return {
            "c": "900",
            "idarpt": airport,
            "movtp": movtp,
            "f": formatted_date,
        }

    def post_process(self, row: dict, context: Context | None = None):
        """Attach metadata to each record."""
        context = context or {}
        row["x_fetched_at"] = context.get("fetched_at") or utc_now_iso()
        row["x_airport_iata"] = context.get("airport_iata")
        row["x_movtp"] = context.get("movtp")
        row["x_date"] = context.get("date")
        return row
