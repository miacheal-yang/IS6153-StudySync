import json
from datetime import date, datetime
from pathlib import Path

from flask import current_app

DEFAULT_DB = {
    "users": [],
    "tasks": [],
    "logs": [],
    "notifications": [],
    "subjects": [],
}


def db_path() -> Path:
    return Path(current_app.config["DB_FILE"])


def load_db() -> dict:
    path = db_path()
    if not path.exists():
        return dict(DEFAULT_DB)
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return dict(DEFAULT_DB)
    data = json.loads(text)
    for key, default in DEFAULT_DB.items():
        data.setdefault(key, list(default))
    return data


def save_db(data: dict) -> None:
    db_path().write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def to_date(value):
    try:
        raw = str(value)
        if "T" in raw:
            return datetime.fromisoformat(raw).date()
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def minutes_from_log(log: dict) -> int:
    try:
        duration = int(log.get("duration_minutes", 0))
    except (TypeError, ValueError):
        duration = 0
    if duration > 0:
        return duration
    try:
        hours = int(log.get("hours", 0))
    except (TypeError, ValueError):
        hours = 0
    try:
        minutes = int(log.get("minutes", 0))
    except (TypeError, ValueError):
        minutes = 0
    return max(0, hours * 60 + minutes)


def iso_today() -> str:
    return date.today().isoformat()
