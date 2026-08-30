import csv
import io

from flask import Blueprint, Response, jsonify, request, session

from routes.auth import session_required_api
from routes.db_store import load_db

exports_bp = Blueprint("exports", __name__, url_prefix="/api/export")


def _is_premium_user() -> bool:
    session_user = session.get("user") or {}
    return str(session_user.get("tier", "")).lower() == "premium"


@exports_bp.get("/csv")
@session_required_api
def export_csv():
    if not _is_premium_user():
        return jsonify({"error": "Premium only"}), 403
    export_type = request.args.get("type", "logs")
    data = load_db()
    output = io.StringIO()

    if export_type == "tasks":
        fields = ["id", "title", "status", "deadline", "created_at"]
        rows = [t for t in data["tasks"] if t.get("user_id") == session["user_id"]]
    else:
        export_type = "logs"
        fields = ["id", "date", "study_hours", "completed_tasks", "note"]
        rows = [l for l in data["logs"] if l.get("user_id") == session["user_id"]]

    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row.get(k, "") for k in fields})

    csv_data = output.getvalue()
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={export_type}.csv"},
    )


@exports_bp.get("/pdf")
@session_required_api
def export_pdf():
    if not _is_premium_user():
        return jsonify({"error": "Premium only"}), 403
    return jsonify(
        {
            "message": "Prototype mode: PDF export is not generated yet. Use /api/export/csv for downloadable data."
        }
    ), 501
