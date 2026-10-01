from __future__ import annotations

from datetime import datetime
import math
from typing import Any

REQUIRED = {"reading_id", "shipment_id", "sensor_id", "observed_at", "temperature_c", "target_min_c", "target_max_c", "location"}


class ContractError(ValueError):
    pass


def validate(reading: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(reading, dict):
        raise ContractError("reading must be a JSON object")
    missing = REQUIRED.difference(reading)
    if missing:
        raise ContractError(f"missing: {', '.join(sorted(missing))}")
    unexpected = set(reading).difference(REQUIRED)
    if unexpected:
        raise ContractError(f"unexpected: {', '.join(sorted(unexpected))}")
    if not all(isinstance(reading[key], str) and reading[key].strip() for key in ("reading_id", "shipment_id", "sensor_id", "location")):
        raise ContractError("identifiers and location must be non-empty strings")
    try:
        datetime.fromisoformat(str(reading["observed_at"]).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractError("observed_at must be ISO-8601") from exc
    for key in ("temperature_c", "target_min_c", "target_max_c"):
        if isinstance(reading[key], bool) or not isinstance(reading[key], (int, float)):
            raise ContractError(f"{key} must be numeric")
        if not math.isfinite(reading[key]):
            raise ContractError(f"{key} must be finite")
    if reading["target_min_c"] >= reading["target_max_c"]:
        raise ContractError("target_min_c must be lower than target_max_c")
    return reading
