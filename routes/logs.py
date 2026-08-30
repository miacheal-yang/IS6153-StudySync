from datetime import date, timedelta

from flask import Blueprint, current_app, jsonify, request, session

from routes.auth import session_required_api
from routes.db_store import load_db, save_db, to_date
from routes.user_store import find_user_by_id, load_users, save_users

logs_bp = Blueprint("logs", __name__, url_prefix="/api/logs")
subjects_bp = Blueprint("subjects", __name__, url_prefix="/api/subjects")


def _next_id(items: list[dict]) -> int:
    return max([item.get("id", 0) for item in items], default=0) + 1


def _next_subject_id(subjects: list[dict]) -> str:
    max_num = 0
    for item in subjects:
        raw = str(item.get("id", ""))
        if raw.startswith("s"):
            try:
                max_num = max(max_num, int(raw[1:]))
            except ValueError:
                pass
    return f"s{max_num + 1:03d}"


def _compute_streak_days(log_dates: set[date]) -> int:
    today = date.today()
    yesterday = today - timedelta(days=1)
    if today in log_dates:
        cursor = today
    elif yesterday in log_dates:
        cursor = yesterday
    else:
        return 0

    streak = 0
    while cursor in log_dates:
        streak += 1
        cursor = cursor - timedelta(days=1)
    return streak


def _normalize_subject_name(name: str) -> str:
    return str(name).strip()


def _save_subject_to_user_profile(user_id: str, subject_name: str) -> None:
    users = load_users(current_app.root_path)
    user = find_user_by_id(users, user_id)
    if not user:
        return
    current_subjects = user.get("subjects", [])
    if not isinstance(current_subjects, list):
        current_subjects = []
    lowered = {str(item).strip().lower() for item in current_subjects if str(item).strip()}
    if subject_name.lower() in lowered:
        return
    current_subjects.append(subject_name)
    user["subjects"] = current_subjects
    save_users(current_app.root_path, users)


def _user_subjects(data: dict, user_id: str) -> list[dict]:
    by_lower_name: dict[str, dict] = {}

    for item in data["subjects"]:
        if item.get("user_id") != user_id:
            continue
        name = _normalize_subject_name(item.get("name", ""))
        if not name:
            continue
        key = name.lower()
        by_lower_name[key] = {"id": item.get("id", ""), "name": name}

    for task in data["tasks"]:
        if task.get("user_id") != user_id:
            continue
        name = _normalize_subject_name(task.get("subject", ""))
        if not name:
            continue
        key = name.lower()
        by_lower_name.setdefault(key, {"id": "", "name": name})

    for log in data["logs"]:
        if log.get("user_id") != user_id:
            continue
        name = _normalize_subject_name(log.get("subject", ""))
        if not name:
            continue
        key = name.lower()
        by_lower_name.setdefault(key, {"id": "", "name": name})

    return sorted(by_lower_name.values(), key=lambda x: x["name"].lower())


@subjects_bp.get("")
@session_required_api
def list_subjects():
    data = load_db()
    subjects = _user_subjects(data, session["user_id"])
    return jsonify({"subjects": subjects})


@subjects_bp.post("")
@session_required_api
def create_subject():
    body = request.get_json(silent=True) or {}
    name = _normalize_subject_name(body.get("name", ""))
    if not name:
        return jsonify({"error": "name is required"}), 400

    data = load_db()
    existing = _user_subjects(data, session["user_id"])
    existing_by_name = {item["name"].strip().lower(): item for item in existing}
    key = name.lower()
    if key in existing_by_name:
        return jsonify({"subject": existing_by_name[key], "created": False}), 200

    new_subject = {"id": _next_subject_id(data["subjects"]), "user_id": session["user_id"], "name": name}
    data["subjects"].append(new_subject)
    save_db(data)
    _save_subject_to_user_profile(session["user_id"], name)
    return jsonify({"subject": {"id": new_subject["id"], "name": name}, "created": True}), 201


@logs_bp.get("")
@session_required_api
def list_logs():
    start = request.args.get("start")
    end = request.args.get("end")

    start_date = to_date(start) if start else None
    end_date = to_date(end) if end else None
    if (start and not start_date) or (end and not end_date):
        return jsonify({"error": "start/end must be YYYY-MM-DD"}), 400

    data = load_db()
    logs = [l for l in data["logs"] if l.get("user_id") == session["user_id"]]

    if start_date:
        logs = [l for l in logs if to_date(l.get("date", "")) and to_date(l.get("date")) >= start_date]
    if end_date:
        logs = [l for l in logs if to_date(l.get("date", "")) and to_date(l.get("date")) <= end_date]

    logs.sort(key=lambda x: x.get("date", ""), reverse=True)
    return jsonify({"logs": logs})


@logs_bp.post("")
@session_required_api
def create_log():
    body = request.get_json(silent=True) or {}
    log_date = str(body.get("date", date.today().isoformat())).strip()
    if not to_date(log_date):
        return jsonify({"error": "date must be YYYY-MM-DD"}), 400

    subject = _normalize_subject_name(body.get("subject", ""))
    if not subject:
        return jsonify({"error": "subject is required"}), 400

    try:
        hours = int(body.get("hours", 0))
        minutes = int(body.get("minutes", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "hours/minutes must be integers"}), 400
    if hours < 0 or hours > 12:
        return jsonify({"error": "hours must be between 0 and 12"}), 400
    if minutes not in {0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55}:
        return jsonify({"error": "minutes must be one of 0,5,10,...,55"}), 400

    try:
        duration_minutes = int(body.get("duration_minutes", hours * 60 + minutes))
    except (TypeError, ValueError):
        return jsonify({"error": "duration_minutes must be an integer"}), 400
    if duration_minutes <= 0:
        return jsonify({"error": "duration must be greater than 0"}), 400

    mood = str(body.get("mood", "")).strip().lower()
    if mood and mood not in {"focused", "neutral", "low"}:
        return jsonify({"error": "mood must be focused|neutral|low"}), 400

    data = load_db()
    user_id = session["user_id"]
    has_log_for_date = any(item.get("user_id") == user_id and item.get("date") == log_date for item in data["logs"])

    matching_subject = None
    for item in data["subjects"]:
        if item.get("user_id") == user_id and str(item.get("name", "")).strip().lower() == subject.lower():
            matching_subject = item
            break
    if matching_subject is None:
        data["subjects"].append({"id": _next_subject_id(data["subjects"]), "user_id": user_id, "name": subject})
        _save_subject_to_user_profile(user_id, subject)

    try:
        completed_tasks = int(body.get("completed_tasks", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "completed_tasks must be an integer"}), 400

    log = {
        "id": _next_id(data["logs"]),
        "user_id": user_id,
        "date": log_date,
        "subject": subject,
        "hours": hours,
        "minutes": minutes,
        "duration_minutes": duration_minutes,
        "study_hours": round(duration_minutes / 60, 2),
        "mood": mood or "neutral",
        "completed_tasks": completed_tasks,
        "note": str(body.get("note", "")).strip(),
    }
    data["logs"].append(log)

    user_log_dates = {
        d for d in [to_date(item.get("date", "")) for item in data["logs"] if item.get("user_id") == user_id] if d
    }
    streak_days = _compute_streak_days(user_log_dates)

    save_db(data)
    return jsonify({"log": log, "streak_days": streak_days, "has_log_for_date": has_log_for_date}), 201


@logs_bp.delete("/<int:log_id>")
@session_required_api
def delete_log(log_id: int):
    data = load_db()
    old_len = len(data["logs"])
    data["logs"] = [
        l for l in data["logs"] if not (l.get("id") == log_id and l.get("user_id") == session["user_id"])
    ]
    if len(data["logs"]) == old_len:
        return jsonify({"error": "Log not found"}), 404
    save_db(data)
    return jsonify({"ok": True})


@logs_bp.get("/summary")
@session_required_api
def logs_summary():
    today = date.today()
    month_start = date(today.year, today.month, 1)
    week_start = today.fromordinal(today.toordinal() - 6)

    data = load_db()
    logs = [l for l in data["logs"] if l.get("user_id") == session["user_id"]]
    month_logs = [l for l in logs if to_date(l.get("date", "")) and to_date(l.get("date")) >= month_start]
    week_logs = [l for l in logs if to_date(l.get("date", "")) and to_date(l.get("date")) >= week_start]
    date_set = {d for d in [to_date(l.get("date", "")) for l in logs] if d}

    completed_tasks = sum(int(l.get("completed_tasks", 0)) for l in month_logs)
    total_study_hours = round(sum(float(l.get("study_hours", 0)) for l in month_logs), 2)
    week_study_hours = round(sum(float(l.get("study_hours", 0)) for l in week_logs), 2)
    return jsonify(
        {
            "month_completed_tasks": completed_tasks,
            "month_study_hours": total_study_hours,
            "week_study_hours": week_study_hours,
            "streak_days": _compute_streak_days(date_set),
        }
    )
