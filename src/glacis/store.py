from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any


def path() -> Path:
    directory = Path(os.getenv("GLACIS_DATA_DIR", Path(__file__).resolve().parents[2] / "data"))
    directory.mkdir(parents=True, exist_ok=True)
    return directory / "glacis.db"


def connect(database: Path | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(database or path())
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS readings (
      reading_id TEXT PRIMARY KEY, shipment_id TEXT, sensor_id TEXT, observed_at TEXT,
      temperature_c REAL, target_min_c REAL, target_max_c REAL, location TEXT,
      state TEXT, delta_c REAL, message TEXT)""")
    return conn


def save(reading: dict[str, Any], result: dict[str, Any], database: Path | None = None) -> bool:
    with connect(database) as conn:
        cursor = conn.execute("INSERT OR IGNORE INTO readings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
            reading["reading_id"], reading["shipment_id"], reading["sensor_id"], reading["observed_at"],
            reading["temperature_c"], reading["target_min_c"], reading["target_max_c"], reading["location"],
            result["state"], result["delta_c"], result["message"],
        ))
        return cursor.rowcount == 1


def overview(database: Path | None = None) -> dict[str, Any]:
    with connect(database) as conn:
        total = conn.execute("SELECT COUNT(*) AS n FROM readings").fetchone()["n"]
        watch = conn.execute("SELECT COUNT(*) AS n FROM readings WHERE state != 'within_range'").fetchone()["n"]
        critical = conn.execute("SELECT COUNT(*) AS n FROM readings WHERE state = 'critical'").fetchone()["n"]
        readings = [dict(row) for row in conn.execute("SELECT * FROM readings ORDER BY observed_at DESC LIMIT 12").fetchall()]
    return {"total": total, "watch": watch, "critical": critical, "readings": readings}
