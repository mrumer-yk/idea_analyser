"""SQLite connection + schema bootstrap.

We use the stdlib ``sqlite3`` module (no ORM) to keep data access transparent
and dependency-free. Each call opens a short-lived connection; SQLite handles
concurrent readers fine and our write volume is low.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .config import get_settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id          TEXT PRIMARY KEY,
    created_at  TEXT NOT NULL,
    input_type  TEXT NOT NULL,            -- 'text' | 'url'
    raw_input   TEXT,
    source_url  TEXT,
    status      TEXT NOT NULL,            -- queued | running | done | error
    provider    TEXT,
    error       TEXT
);

CREATE TABLE IF NOT EXISTS run_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      TEXT NOT NULL REFERENCES runs(id),
    ts          TEXT NOT NULL,
    agent       TEXT NOT NULL,
    phase       TEXT NOT NULL,            -- started | finished | error | info
    message     TEXT,
    payload_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_run_events_run ON run_events(run_id, id);

CREATE TABLE IF NOT EXISTS evidence (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id       TEXT NOT NULL REFERENCES runs(id),
    title        TEXT,
    url          TEXT NOT NULL,
    snippet      TEXT,
    source_type  TEXT,                    -- pricing|gov|appstore|forum|news|other
    retrieved_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_evidence_run ON evidence(run_id);

CREATE TABLE IF NOT EXISTS reports (
    run_id         TEXT PRIMARY KEY REFERENCES runs(id),
    report_md      TEXT,
    report_json    TEXT,
    fit_score      REAL,
    recommendation TEXT,
    confidence     TEXT
);
"""


def _db_path() -> Path:
    return Path(get_settings().database_path)


def init_db() -> None:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.executescript(SCHEMA)


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(_db_path(), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
