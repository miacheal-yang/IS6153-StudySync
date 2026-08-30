from datetime import date, timedelta

from flask import Blueprint, jsonify, session

from routes.auth import session_required_api
from routes.db_store import load_db, to_date

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


def _is_premium_user() -> bool:
    session_user = session.get("user") or {}
    return str(session_user.get("tier", "")).lower() == "premium"


def _recent_log(logs: list[dict]) -> dict | None:
    if not logs:
        return None
    sorted_logs = sorted(
        logs,
        key=lambda item: (
            str(item.get("date", "")),
            int(item.get("id", 0)),
        ),
        reverse=True,
    )
    latest = sorted_logs[0]
    return {
        "id": latest.get("id"),
        "date": latest.get("date"),
        "subject": latest.get("subject", ""),
        "study_hours": latest.get("study_hours", 0),
        "note": latest.get("note", ""),
    }


def _recommendation_text(tasks: list[dict]) -> str:
    todo_count = len([t for t in tasks if t.get("status") == "todo"])
    done_count = len([t for t in tasks if t.get("status") == "done"])
    if todo_count > done_count:
        return "You have more pending tasks than completed ones. Try focusing on top 3 priorities today."
    return "Your completion trend is stable. Keep a fixed review slot each day."


def _urgency(priority: str) -> dict:
    level = str(priority or "medium").lower()
    if level == "high":
        return {"text": "Urgent", "class_name": "urgent"}
    if level == "low":
        return {"text": "Low", "class_name": "low"}
    return {"text": "Medium", "class_name": "medium"}


@dashboard_bp.get("/summary")
@session_required_api
def dashboard_summary():
    data = load_db()
    user_id = session["user_id"]
    tasks = [t for t in data["tasks"] if t.get("user_id") == user_id]
    logs = [l for l in data["logs"] if l.get("user_id") == user_id]

    today = date.today()
    max_day = today + timedelta(days=3)
    upcoming = []
    for task in tasks:
        due = to_date(task.get("deadline", ""))
        if not due:
            continue
        if today <= due <= max_day and task.get("status") != "done":
            upcoming.append(task)
    upcoming.sort(key=lambda item: item.get("deadline", "9999-12-31"))
    upcoming_cards = []
    for task in upcoming[:2]:
        urgency = _urgency(task.get("priority", "medium"))
        due = to_date(task.get("deadline", ""))
        due_text = f"Due {due.strftime('%a %d %b')}" if due else "No due date"
        upcoming_cards.append(
            {
                "id": task.get("id"),
                "title": task.get("title", "Untitled task"),
                "due_text": due_text,
                "urgency_text": urgency["text"],
                "urgency_class": urgency["class_name"],
            }
        )

    open_tasks = [task for task in tasks if task.get("status") != "done"]
    high = len([task for task in open_tasks if str(task.get("priority", "")).lower() == "high"])
    medium = len([task for task in open_tasks if str(task.get("priority", "")).lower() == "medium"])
    pressure_score = min(100, high * 35 + medium * 18 + max(len(open_tasks) - high - medium, 0) * 10)
    pressure_score = max(5, pressure_score or 10)

    recommendation = None
    if _is_premium_user():
        recommendation = {
            "is_premium": True,
            "text": _recommendation_text(tasks),
        }
    else:
        recommendation = {
            "is_premium": False,
            "text": "Upgrade to Premium to get AI recommendations.",
        }

    recent = _recent_log(logs)
    if recommendation.get("is_premium"):
        smart_text = recommendation.get("text", "No recommendation yet.")
    elif recent and recent.get("date"):
        subject = str(recent.get("subject", "General")).strip() or "General"
        hours = float(recent.get("study_hours", 0) or 0)
        smart_text = f"Recent log: {subject} {hours:g}h. {len(upcoming)} task{'s' if len(upcoming) != 1 else ''} due soon."
    else:
        smart_text = "No pending tasks - keep your momentum going."

    return jsonify(
        {
            "tasks_due_count": len(upcoming),
            "upcoming_tasks": upcoming_cards,
            "recent_log": recent,
            "recommendation": recommendation,
            "smart_text": smart_text,
            "pressure_score": pressure_score,
        }
    )
