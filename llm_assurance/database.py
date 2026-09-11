from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = ROOT / "runtime" / "assurance.db"
_LOCK = Lock()


def initialize_database() -> None:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS assurance_events (
                request_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                use_case TEXT NOT NULL,
                decision TEXT NOT NULL,
                score INTEGER,
                finding_count INTEGER NOT NULL DEFAULT 0,
                policy_version TEXT NOT NULL,
                latency_ms REAL NOT NULL,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_created_at "
            "ON assurance_events(created_at DESC)"
        )


def record_event(
    *,
    request_id: str,
    event_type: str,
    use_case: str,
    decision: str,
    score: int | None,
    finding_count: int,
    policy_version: str,
    latency_ms: float,
    metadata: dict[str, Any] | None = None,
) -> None:
    initialize_database()
    event = (
        request_id,
        event_type,
        use_case[:120],
        decision,
        score,
        finding_count,
        policy_version,
        latency_ms,
        json.dumps(metadata or {}, sort_keys=True),
        datetime.now(timezone.utc).isoformat(),
    )
    with _LOCK, sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            INSERT INTO assurance_events (
                request_id, event_type, use_case, decision, score,
                finding_count, policy_version, latency_ms, metadata_json,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            event,
        )


def recent_events(limit: int = 25) -> list[dict[str, Any]]:
    initialize_database()
    with _LOCK, sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT request_id, event_type, use_case, decision, score,
                   finding_count, policy_version, latency_ms, metadata_json,
                   created_at
            FROM assurance_events
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    events = []
    for row in rows:
        event = dict(row)
        event["metadata"] = json.loads(event.pop("metadata_json"))
        events.append(event)
    return events
