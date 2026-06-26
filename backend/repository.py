"""Data-access functions over the SQLite schema (no ORM)."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from .db import connect


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── runs ──────────────────────────────────────────────────────────
def create_run(run_id: str, input_type: str, raw_input: str | None,
               source_url: str | None, provider: str) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO runs (id, created_at, input_type, raw_input, source_url, status, provider)"
            " VALUES (?, ?, ?, ?, ?, 'queued', ?)",
            (run_id, _now(), input_type, raw_input, source_url, provider),
        )


def set_run_status(run_id: str, status: str, error: str | None = None) -> None:
    with connect() as conn:
        conn.execute("UPDATE runs SET status=?, error=? WHERE id=?", (status, error, run_id))


def get_run(run_id: str) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        return dict(row) if row else None


def delete_run(run_id: str) -> None:
    """Delete a run and all of its child rows (events, evidence, report)."""
    with connect() as conn:
        conn.execute("DELETE FROM reports WHERE run_id=?", (run_id,))
        conn.execute("DELETE FROM evidence WHERE run_id=?", (run_id,))
        conn.execute("DELETE FROM run_events WHERE run_id=?", (run_id,))
        conn.execute("DELETE FROM runs WHERE id=?", (run_id,))


def list_runs(limit: int = 50) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, created_at, input_type, raw_input, source_url, status, "
            "(SELECT recommendation FROM reports WHERE reports.run_id = runs.id) AS recommendation "
            "FROM runs ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


# ── events ────────────────────────────────────────────────────────
def add_event(run_id: str, agent: str, phase: str, message: str | None,
              payload: dict | None) -> dict:
    ts = _now()
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO run_events (run_id, ts, agent, phase, message, payload_json)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (run_id, ts, agent, phase, message, json.dumps(payload) if payload else None),
        )
        event_id = cur.lastrowid
    return {"id": event_id, "run_id": run_id, "ts": ts, "agent": agent,
            "phase": phase, "message": message, "payload": payload}


def list_events(run_id: str, after_id: int = 0) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM run_events WHERE run_id=? AND id>? ORDER BY id",
            (run_id, after_id),
        ).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["payload"] = json.loads(d.pop("payload_json")) if d.get("payload_json") else None
            out.append(d)
        return out


# ── evidence ──────────────────────────────────────────────────────
def add_evidence_bulk(run_id: str, items: list[dict]) -> None:
    if not items:
        return
    ts = _now()
    with connect() as conn:
        conn.executemany(
            "INSERT INTO evidence (run_id, title, url, snippet, source_type, retrieved_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            [(run_id, i.get("title"), i.get("url"), i.get("snippet"),
              i.get("source_type"), ts) for i in items],
        )


def list_evidence(run_id: str) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT title, url, snippet, source_type FROM evidence WHERE run_id=?",
            (run_id,),
        ).fetchall()
        return [dict(r) for r in rows]


# ── reports ───────────────────────────────────────────────────────
def save_report(run_id: str, report_md: str, report_json: dict,
                fit_score: float | None, recommendation: str, confidence: str) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO reports "
            "(run_id, report_md, report_json, fit_score, recommendation, confidence)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (run_id, report_md, json.dumps(report_json), fit_score, recommendation, confidence),
        )


def get_report(run_id: str) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM reports WHERE run_id=?", (run_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["report_json"] = json.loads(d["report_json"]) if d["report_json"] else None
        return d
