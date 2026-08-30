from datetime import date, datetime, timedelta

from flask import Blueprint, jsonify, request, session

from routes.auth import session_required_api
from routes.db_store import load_db, save_db, to_date

tasks_bp = Blueprint("tasks", __name__, url_prefix="/api/tasks")


def _next_id(items: list[dict]) -> int:
    return max([item.get("id", 0) for item in items], default=0) + 1


def _to_reminder_offset(value) -> int:
    try:
        if value in ("off", "", None):
            return -1
        return int(value)
    except (TypeError, ValueError):
        return -1


def _is_overdue(task: dict) -> bool:
    if str(task.get("status", "")).lower() == "done":
        return False
    due = to_date(task.get("deadline", ""))
    if not due:
        return False
    return due < date.today()


def _due_text(task: dict) -> str:
    due = to_date(task.get("deadline", ""))
    if not due:
        return "No due date"
    return f"Due {due.strftime('%a %d %b')}"


def _pill_for_task(task: dict) -> dict:
    p = str(task.get("priority", "low")).lower()
    if p == "urgent":
        return {"text": "Urgent", "class_name": "task-list-pill--urgent"}
    if p == "high":
        return {"text": "High", "class_name": "task-list-pill--high"}
    if p == "medium":
        return {"text": "Medium", "class_name": "task-list-pill--medium"}
    return {"text": "Low", "class_name": "task-list-pill--low"}


def _due_color_class(task: dict) -> str:
    if str(task.get("status", "")).lower() == "done":
        return ""
    if _is_overdue(task):
        return "task-list-due--red"
    p = str(task.get("priority", "low")).lower()
    if p == "urgent":
        return "task-list-due--red"
    if p == "high":
        return "task-list-due--orange"
    return "task-list-due--muted"


def _task_matches_filter(task: dict, filter_name: str) -> bool:
    status = str(task.get("status", "")).lower()
    if filter_name == "pending":
        return status != "done"
    if filter_name == "done":
        return status == "done"
    if filter_name == "overdue":
        return _is_overdue(task)
    return True


def _sort_tasks_for_display(items: list[dict]) -> list[dict]:
    def due_key(task: dict):
        due = to_date(task.get("deadline", ""))
        return due.toordinal() if due else 10**9

    return sorted(
        items,
        key=lambda task: (
            str(task.get("status", "")).lower() == "done",
            due_key(task),
        ),
    )


@tasks_bp.get("")
@session_required_api
def list_tasks():
    status = request.args.get("status")
    sort = request.args.get("sort")
    user_id = session["user_id"]

    data = load_db()
    tasks = [t for t in data["tasks"] if t.get("user_id") == user_id]

    if status:
        tasks = [t for t in tasks if t.get("status") == status]

    if sort == "deadline":
        tasks.sort(key=lambda x: x.get("deadline", "9999-12-31"))
    else:
        tasks.sort(key=lambda x: x.get("id", 0), reverse=True)

    return jsonify({"tasks": tasks})


@tasks_bp.get("/view")
@session_required_api
def list_tasks_for_view():
    filter_name = str(request.args.get("filter", "all")).strip().lower()
    if filter_name not in {"all", "pending", "done", "overdue"}:
        filter_name = "all"

    data = load_db()
    user_id = session["user_id"]
    tasks = [t for t in data["tasks"] if t.get("user_id") == user_id]
    filtered = [task for task in tasks if _task_matches_filter(task, filter_name)]
    sorted_tasks = _sort_tasks_for_display(filtered)

    view_items = []
    for task in sorted_tasks:
        pill = _pill_for_task(task)
        view_items.append(
            {
                **task,
                "is_done": str(task.get("status", "")).lower() == "done",
                "is_overdue": _is_overdue(task),
                "due_text": _due_text(task),
                "due_class": _due_color_class(task),
                "pill_text": pill["text"],
                "pill_class": pill["class_name"],
            }
        )
    return jsonify({"tasks": view_items, "filter": filter_name})


@tasks_bp.post("")
@session_required_api
def create_task():
    body = request.get_json(silent=True) or {}
    title = str(body.get("title", "")).strip()
    deadline = str(body.get("deadline", "")).strip()
    if not title:
        return jsonify({"error": "title is required"}), 400
    if deadline and not to_date(deadline):
        return jsonify({"error": "deadline must be YYYY-MM-DD or ISO datetime"}), 400

    data = load_db()
    tasks = data["tasks"]
    task = {
        "id": _next_id(tasks),
        "user_id": session["user_id"],
        "title": title,
        "description": str(body.get("description", "")).strip(),
        "subject": str(body.get("subject", "")).strip() or "General",
        "priority": str(body.get("priority", "low")).strip() or "low",
        "status": str(body.get("status", "todo")).strip() or "todo",
        "deadline": deadline,
        "reminder": str(body.get("reminder", "off")).strip() or "off",
        "reminder_offset_days": _to_reminder_offset(body.get("reminder_offset_days", -1)),
        "created_at": datetime.utcnow().isoformat(),
    }
    tasks.append(task)
    save_db(data)
    return jsonify({"task": task}), 201


@tasks_bp.put("/<int:task_id>")
@session_required_api
def update_task(task_id: int):
    body = request.get_json(silent=True) or {}
    data = load_db()
    for task in data["tasks"]:
        if task.get("id") == task_id and task.get("user_id") == session["user_id"]:
            if "title" in body:
                task["title"] = str(body.get("title", "")).strip()
            if "description" in body:
                task["description"] = str(body.get("description", "")).strip()
            if "status" in body:
                task["status"] = str(body.get("status", "")).strip() or task.get("status", "todo")
            if "subject" in body:
                task["subject"] = str(body.get("subject", "")).strip() or task.get("subject", "General")
            if "priority" in body:
                task["priority"] = str(body.get("priority", "")).strip() or task.get("priority", "low")
            if "deadline" in body:
                deadline = str(body.get("deadline", "")).strip()
                if deadline and not to_date(deadline):
                    return jsonify({"error": "deadline must be YYYY-MM-DD or ISO datetime"}), 400
                task["deadline"] = deadline
            if "reminder" in body:
                task["reminder"] = str(body.get("reminder", "")).strip() or "off"
            if "reminder_offset_days" in body:
                task["reminder_offset_days"] = _to_reminder_offset(body.get("reminder_offset_days", -1))
            save_db(data)
            return jsonify({"task": task})
    return jsonify({"error": "Task not found"}), 404


@tasks_bp.delete("/<int:task_id>")
@session_required_api
def delete_task(task_id: int):
    data = load_db()
    old_len = len(data["tasks"])
    data["tasks"] = [
        t for t in data["tasks"] if not (t.get("id") == task_id and t.get("user_id") == session["user_id"])
    ]
    if len(data["tasks"]) == old_len:
        return jsonify({"error": "Task not found"}), 404
    save_db(data)
    return jsonify({"ok": True})


@tasks_bp.get("/upcoming")
@session_required_api
def upcoming_tasks():
    today = date.today()
    max_day = today + timedelta(days=3)
    data = load_db()
    upcoming = []
    for task in data["tasks"]:
        if task.get("user_id") != session["user_id"]:
            continue
        due = to_date(task.get("deadline", ""))
        if not due:
            continue
        if today <= due <= max_day and task.get("status") != "done":
            upcoming.append(task)
    upcoming.sort(key=lambda x: x.get("deadline", "9999-12-31"))
    return jsonify({"tasks": upcoming})


@tasks_bp.get("/calendar/week")
@session_required_api
def calendar_week():
    anchor_raw = request.args.get("date", "").strip()
    anchor = to_date(anchor_raw) or date.today()
    week_start = anchor - timedelta(days=anchor.weekday())

    data = load_db()
    user_id = session["user_id"]
    tasks = [t for t in data["tasks"] if t.get("user_id") == user_id and t.get("status") != "done"]
    logs = [l for l in data["logs"] if l.get("user_id") == user_id]

    task_by_date: dict[str, list[dict]] = {}
    for task in tasks:
        due = to_date(task.get("deadline", ""))
        if not due:
            continue
        key = due.isoformat()
        task_by_date.setdefault(key, []).append(task)

    study_dates = set()
    for log in logs:
        log_date = to_date(log.get("date", ""))
        if log_date:
            study_dates.add(log_date.isoformat())

    day_labels = ["M", "T", "W", "T", "F", "S", "S"]
    days = []
    for idx in range(7):
        d = week_start + timedelta(days=idx)
        key = d.isoformat()
        days.append(
            {
                "date": key,
                "label": day_labels[idx],
                "day": d.day,
                "has_study": key in study_dates,
                "has_deadline": key in task_by_date,
                "is_selected": key == anchor.isoformat(),
            }
        )

    selected_key = anchor.isoformat()
    selected_tasks = task_by_date.get(selected_key, [])
    return jsonify(
        {
            "selected_date": selected_key,
            "selected_title": anchor.strftime("%a %d %b"),
            "has_study": selected_key in study_dates,
            "deadlines": [
                {
                    "id": t.get("id"),
                    "title": t.get("title", "Untitled task"),
                    "description": t.get("description", ""),
                }
                for t in selected_tasks
            ],
            "days": days,
        }
    )
