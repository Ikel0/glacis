from __future__ import annotations

from typing import Any


def assess(reading: dict[str, Any]) -> dict[str, Any]:
    if reading["target_min_c"] <= reading["temperature_c"] <= reading["target_max_c"]:
        return {"state": "within_range", "delta_c": 0.0, "message": "consigne respectée"}
    delta = reading["temperature_c"] - reading["target_max_c"] if reading["temperature_c"] > reading["target_max_c"] else reading["target_min_c"] - reading["temperature_c"]
    state = "critical" if delta >= 3 else "watch"
    direction = "au-dessus" if reading["temperature_c"] > reading["target_max_c"] else "en dessous"
    return {"state": state, "delta_c": round(delta, 1), "message": f"{delta:.1f} °C {direction} de la consigne"}
