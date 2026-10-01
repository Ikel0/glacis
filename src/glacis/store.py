from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from pathlib import Path
from typing import Any


class ReadingConflictError(ValueError):
    """Raised when a reading identifier is reused with another payload."""


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
      state TEXT, delta_c REAL, message TEXT, fingerprint TEXT)""")
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(readings)")}
    if "fingerprint" not in columns:
        conn.execute("ALTER TABLE readings ADD COLUMN fingerprint TEXT")
    return conn


def fingerprint(reading: dict[str, Any]) -> str:
    payload = json.dumps(reading, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def save(reading: dict[str, Any], result: dict[str, Any], database: Path | None = None) -> bool:
    with connect(database) as conn:
        conn.execute("BEGIN IMMEDIATE")
        digest = fingerprint(reading)
        existing = conn.execute("SELECT * FROM readings WHERE reading_id = ?", (reading["reading_id"],)).fetchone()
        if existing:
            stored = {key: existing[key] for key in (
                "reading_id", "shipment_id", "sensor_id", "observed_at", "temperature_c",
                "target_min_c", "target_max_c", "location",
            )}
            stored_digest = existing["fingerprint"] or fingerprint(stored)
            if stored_digest != digest:
                raise ReadingConflictError("reading_id already exists with a different payload")
            return False
        conn.execute("""INSERT INTO readings (
          reading_id, shipment_id, sensor_id, observed_at, temperature_c, target_min_c,
          target_max_c, location, state, delta_c, message, fingerprint
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
            reading["reading_id"], reading["shipment_id"], reading["sensor_id"], reading["observed_at"],
            reading["temperature_c"], reading["target_min_c"], reading["target_max_c"], reading["location"],
            result["state"], result["delta_c"], result["message"], digest,
        ))
        return True


def overview(database: Path | None = None) -> dict[str, Any]:
    with connect(database) as conn:
        total = conn.execute("SELECT COUNT(*) AS n FROM readings").fetchone()["n"]
        watch = conn.execute("SELECT COUNT(*) AS n FROM readings WHERE state != 'within_range'").fetchone()["n"]
        critical = conn.execute("SELECT COUNT(*) AS n FROM readings WHERE state = 'critical'").fetchone()["n"]
        readings = [dict(row) for row in conn.execute("SELECT * FROM readings ORDER BY observed_at DESC LIMIT 12").fetchall()]
    return {"total": total, "watch": watch, "critical": critical, "readings": readings}
