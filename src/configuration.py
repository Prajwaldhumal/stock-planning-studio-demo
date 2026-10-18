"""Persistent application settings for Stock Planning Studio."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
VERSION_DIR = DATA_DIR / "versions"
CONFIG_DIR = ROOT / "config"
SETTINGS_PATH = CONFIG_DIR / "planning_rules.json"
DB_PATH = DATA_DIR / "planning_history.sqlite"

DEFAULT_SETTINGS: dict[str, Any] = {
    "transit_months": 2,
    "target_coverage_months": 1,
    "rounding_multiple": 1,
    "recommendation_method": "Coverage-based draft",
    "show_calculation_details": True,
}


def ensure_directories() -> None:
    for path in (DATA_DIR, UPLOAD_DIR, VERSION_DIR, CONFIG_DIR):
        path.mkdir(parents=True, exist_ok=True)


def load_settings() -> dict[str, Any]:
    ensure_directories()
    if not SETTINGS_PATH.exists():
        save_settings(DEFAULT_SETTINGS)
    try:
        stored = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        stored = {}
    return {**DEFAULT_SETTINGS, **stored}


def save_settings(settings: dict[str, Any]) -> None:
    ensure_directories()
    merged = {**DEFAULT_SETTINGS, **settings}
    SETTINGS_PATH.write_text(json.dumps(merged, indent=2), encoding="utf-8")
