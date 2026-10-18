"""SQLite-backed revision history for draft and approved shipment plans."""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from .configuration import DB_PATH, ensure_directories


def _connect() -> sqlite3.Connection:
    ensure_directories()
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db() -> None:
    with _connect() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS plan_revisions (
                revision_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                workbook_name TEXT NOT NULL,
                sheet_name TEXT NOT NULL,
                section_title TEXT NOT NULL,
                part_number TEXT NOT NULL,
                planning_month TEXT NOT NULL,
                revision_type TEXT NOT NULL,
                status TEXT NOT NULL,
                notes TEXT,
                quantities_json TEXT NOT NULL,
                demand_json TEXT NOT NULL DEFAULT '{}'
            )
        """)
        columns = {row[1] for row in con.execute("PRAGMA table_info(plan_revisions)").fetchall()}
        if "demand_json" not in columns:
            con.execute("ALTER TABLE plan_revisions ADD COLUMN demand_json TEXT NOT NULL DEFAULT '{}' ")


def save_revision(*, workbook_name: str, sheet_name: str, section_title: str,
                  part_number: str, planning_month: str, revision_type: str,
                  status: str, notes: str, quantities: dict[str, Any],
                  demand_overrides: dict[str, Any] | None = None) -> str:
    init_db()
    revision_id = uuid.uuid4().hex[:12].upper()
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    quantity_json = json.dumps({str(k): int(round(float(v))) for k, v in quantities.items()}, sort_keys=True)
    demand_json = json.dumps({str(k): max(0.0, float(v)) for k, v in (demand_overrides or {}).items()}, sort_keys=True)
    with _connect() as con:
        con.execute("""
            INSERT INTO plan_revisions
            (revision_id, created_at, workbook_name, sheet_name, section_title, part_number,
             planning_month, revision_type, status, notes, quantities_json, demand_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (revision_id, timestamp, workbook_name, sheet_name, section_title, part_number,
              planning_month, revision_type, status, notes.strip(), quantity_json, demand_json))
    return revision_id


def list_revisions(limit: int = 100) -> list[dict[str, Any]]:
    init_db()
    with _connect() as con:
        rows = con.execute("SELECT * FROM plan_revisions ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    return [dict(row) for row in rows]


def get_revision(revision_id: str) -> dict[str, Any] | None:
    init_db()
    with _connect() as con:
        row = con.execute("SELECT * FROM plan_revisions WHERE revision_id = ?", (revision_id,)).fetchone()
    if not row:
        return None
    result = dict(row)
    result["quantities"] = json.loads(result.pop("quantities_json"))
    result["demand_overrides"] = json.loads(result.pop("demand_json", "{}"))
    return result


def quantities_from_revision(revision: dict[str, Any]) -> dict[str, int]:
    if "quantities" in revision:
        payload = revision["quantities"]
    else:
        payload = json.loads(revision.get("quantities_json", "{}"))
    return {str(k): int(v) for k, v in payload.items()}
