from datetime import date, timedelta

from flask import Blueprint, jsonify, request, session

from routes.auth import session_required_api
from routes.db_store import load_db, minutes_from_log, to_date

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api")


def _is_premium_user() -> bool:
    session_user = session.get("user") or {}
    return str(session_user.get("tier", "")).lower() == "premium"


@analytics_bp.get("/analytics")
@session_required_api
def analytics():
    if not _is_premium_user():
        return jsonify({"error": "Premium only"}), 403
    range_name = request.args.get("range", "week")
    end = date.today()
    if range_name == "month":
        start = end - timedelta(days=30)
    elif range_name == "semester":
        start = end - timedelta(days=180)
    else:
        range_name = "week"
        start = end - timedelta(days=7)

    data = load_db()
    logs = [l for l in data["logs"] if l.get("user_id") == session["user_id"]]
    tasks = [t for t in data["tasks"] if t.get("user_id") == session["user_id"]]
    range_logs = [l for l in logs if to_date(l.get("date", "")) and to_date(l.get("date")) >= start]

    return jsonify(
        {
            "range": range_name,
            "total_study_hours": round(sum(float(l.get("study_hours", 0)) for l in range_logs), 2),
            "completed_tasks": sum(int(l.get("completed_tasks", 0)) for l in range_logs),
            "total_tasks": len(tasks),
            "done_tasks": len([t for t in tasks if t.get("status") == "done"]),
        }
    )


@analytics_bp.get("/recommendations")
@session_required_api
def recommendations():
    if not _is_premium_user():
        return jsonify({"error": "Premium only"}), 403
    data = load_db()

    tasks = [t for t in data["tasks"] if t.get("user_id") == session["user_id"]]
    todo_count = len([t for t in tasks if t.get("status") == "todo"])
    done_count = len([t for t in tasks if t.get("status") == "done"])

    lines = []
    if todo_count > done_count:
        lines.append("You have more pending tasks than completed ones. Try focusing on top 3 priorities today.")
    else:
        lines.append("Your completion trend is stable. Keep a fixed review slot each day.")
    lines.append("Break larger tasks into 25-minute Pomodoro sessions.")
    lines.append("Log study hours daily to improve weekly analytics quality.")
    return jsonify({"recommendations": lines, "text": " ".join(lines)})


@analytics_bp.get("/analytics/view")
@session_required_api
def analytics_view():
    if not _is_premium_user():
        return jsonify({"error": "Premium only"}), 403

    data = load_db()
    user_id = session["user_id"]
    logs = [l for l in data["logs"] if l.get("user_id") == user_id]
    tasks = [t for t in data["tasks"] if t.get("user_id") == user_id]

    by_subject = {}
    weekday_minutes = [0, 0, 0, 0, 0, 0, 0]
    for item in logs:
        subject = str(item.get("subject", "General")).strip() or "General"
        duration = minutes_from_log(item)
        by_subject[subject] = by_subject.get(subject, 0) + duration
        d = to_date(item.get("date", ""))
        if d:
            weekday_minutes[d.weekday()] += duration

    subject_rows = sorted(by_subject.items(), key=lambda pair: pair[1], reverse=True)[:6]
    subject_hours = [
        {"subject": subject, "minutes": minutes, "hours": round(minutes / 60, 1)}
        for subject, minutes in subject_rows
    ]

    total_tasks = len(tasks)
    done_tasks = len([task for task in tasks if str(task.get("status", "")).lower() == "done"])
    completion_rate = round((done_tasks / total_tasks) * 100) if total_tasks else 0

    max_day_minutes = max(weekday_minutes) if weekday_minutes else 0
    top_day_indexes = [idx for idx, minutes in enumerate(weekday_minutes) if minutes == max_day_minutes and minutes > 0]

    return jsonify(
        {
            "subject_hours": subject_hours,
            "task_completion": {
                "done": done_tasks,
                "total": total_tasks,
                "rate": completion_rate,
            },
            "productive_day": {
                "weekday_minutes": weekday_minutes,
                "top_indexes": top_day_indexes,
                "top_minutes": max_day_minutes,
            },
        }
    )


