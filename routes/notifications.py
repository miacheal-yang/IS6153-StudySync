from flask import Blueprint, jsonify, session

from routes.auth import session_required_api
from routes.db_store import load_db, save_db

notifications_bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")


@notifications_bp.get("")
@session_required_api
def list_notifications():
    data = load_db()
    notifications = [n for n in data["notifications"] if n.get("user_id") == session["user_id"]]
    notifications.sort(key=lambda x: x.get("id", 0), reverse=True)
    return jsonify({"notifications": notifications})


@notifications_bp.put("/read-all")
@session_required_api
def read_all_notifications():
    data = load_db()
    count = 0
    for item in data["notifications"]:
        if item.get("user_id") == session["user_id"] and not item.get("is_read", False):
            item["is_read"] = True
            count += 1
    save_db(data)
    return jsonify({"updated": count})


@notifications_bp.put("/<int:notification_id>/read")
@session_required_api
def read_notification(notification_id: int):
    data = load_db()
    for item in data["notifications"]:
        if item.get("id") == notification_id and item.get("user_id") == session["user_id"]:
            item["is_read"] = True
            save_db(data)
            return jsonify({"notification": item})
    return jsonify({"error": "Notification not found"}), 404
