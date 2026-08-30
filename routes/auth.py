from functools import wraps

from flask import Blueprint, current_app, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash
from routes.user_store import (
    find_user_by_email,
    find_user_by_id,
    load_users,
    next_user_id,
    save_users,
    to_public_user,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
authmodule = auth_bp


def session_required_api(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({"error": "Unauthorized", "redirect": "/"}), 401
        return fn(*args, **kwargs)

    return wrapper


def _set_session_user(user: dict) -> None:
    session["user"] = {
        "id": user.get("id"),
        "tier": str(user.get("tier", "free")).lower(),
    }


@auth_bp.post("/register")
def register():
    body = request.get_json(silent=True) or {}
    full_name = str(body.get("full_name", "")).strip()
    email = str(body.get("email", "")).strip().lower()
    password = str(body.get("password", "")).strip()
    major = str(body.get("major", "")).strip()
    semester = str(body.get("semester", "")).strip()
    tier = "free"

    if not full_name or not email or not password or not major or not semester:
        return jsonify({"error": "Please complete all required fields."}), 400

    users = load_users(current_app.root_path)
    if find_user_by_email(users, email):
        return jsonify({"error": "Email is already registered."}), 409

    new_id = next_user_id(users)
    new_user = {
        "id": new_id,
        "name": full_name,
        "email": email,
        "passwordHash": generate_password_hash(password),
        "major": major,
        "semester": semester,
        "avatarUrl": "",
        "defaultReminder": "0",
        "subjects": [],
        "tier": tier,
    }
    users.append(new_user)
    save_users(current_app.root_path, users)

    session["user_id"] = new_user["id"]
    _set_session_user(new_user)
    return jsonify({"user": to_public_user(new_user)}), 201


@auth_bp.post("/login")
def login():
    body = request.get_json(silent=True) or {}
    email = str(body.get("email", "")).strip().lower()
    password = str(body.get("password", "")).strip()

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    users = load_users(current_app.root_path)
    user = find_user_by_email(users, email)
    if not user or not check_password_hash(user.get("passwordHash", ""), password):
        return jsonify({"error": "Invalid email or password."}), 401

    session["user_id"] = user["id"]
    _set_session_user(user)
    return jsonify({"user": to_public_user(user)}), 200


@auth_bp.get("/me")
@session_required_api
def me():
    users = load_users(current_app.root_path)
    user = find_user_by_id(users, session["user_id"])
    if user:
        _set_session_user(user)
        return jsonify({"user": to_public_user(user)})
    session.clear()
    return jsonify({"error": "Unauthorized", "redirect": "/"}), 401


@auth_bp.put("/profile")
@session_required_api
def update_profile():
    body = request.get_json(silent=True) or {}
    full_name = str(body.get("full_name", "")).strip()
    major = str(body.get("major", "")).strip()
    semester = str(body.get("semester", "")).strip()
    avatar_url = body.get("avatar_url", None)
    default_reminder = body.get("default_reminder", None)

    users = load_users(current_app.root_path)
    user = find_user_by_id(users, session["user_id"])
    if not user:
        session.clear()
        return jsonify({"error": "Unauthorized", "redirect": "/"}), 401

    if full_name:
        user["name"] = full_name
    if major:
        user["major"] = major
    if semester:
        user["semester"] = semester
    if avatar_url is not None:
        user["avatarUrl"] = str(avatar_url).strip()
    if default_reminder is not None:
        user["defaultReminder"] = str(default_reminder).strip() or "0"
    save_users(current_app.root_path, users)
    _set_session_user(user)
    return jsonify({"user": to_public_user(user)})


@auth_bp.post("/simulate-upgrade")
@session_required_api
def simulate_upgrade():
    users = load_users(current_app.root_path)
    user = find_user_by_id(users, session["user_id"])
    if not user:
        session.clear()
        return jsonify({"error": "Unauthorized", "redirect": "/"}), 401
    user["tier"] = "premium"
    save_users(current_app.root_path, users)
    _set_session_user(user)
    return jsonify({"user": to_public_user(user)})


@auth_bp.post("/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})
