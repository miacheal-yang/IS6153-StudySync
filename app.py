from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, session

from routes.auth import auth_bp
from routes.analytics import analytics_bp
from routes.dashboard import dashboard_bp
from routes.exports import exports_bp
from routes.landing import landing_bp
from routes.logs import logs_bp, subjects_bp
from routes.notifications import notifications_bp
from routes.tasks import tasks_bp
from routes.user_store import ensure_user_storage, find_user_by_id, load_users, to_public_user


def create_app() -> Flask:
    def current_public_user():
        user_id = session.get("user_id")
        if not user_id:
            return None
        users = load_users(app.root_path)
        user = find_user_by_id(users, user_id)
        if not user:
            return None
        return to_public_user(user)

    app = Flask(__name__)
    app.config["SECRET_KEY"] = "studytrackr-dev-secret-key"
    app.config["ALLOWED_ORIGINS"] = {
        "http://127.0.0.1:5000",
        "http://localhost:5000",
        "http://127.0.0.1:63342",
        "http://localhost:63342",
    }

    storage_dir = Path(app.root_path) / "LocalStorage"
    storage_dir.mkdir(exist_ok=True)
    db_file = storage_dir / "db.json"
    legacy_db_file = Path(app.root_path) / "data" / "db.json"
    if not db_file.exists() and legacy_db_file.exists():
        db_file.write_text(legacy_db_file.read_text(encoding="utf-8"), encoding="utf-8")
    if not db_file.exists():
        db_file.write_text(
            '{"users": [], "tasks": [], "logs": [], "notifications": [], "subjects": []}',
            encoding="utf-8",
        )
    ensure_user_storage(app.root_path)

    app.config["DB_FILE"] = str(db_file)
    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(subjects_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(exports_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(landing_bp)

    @app.before_request
    def check_session_for_protected_routes():
        path = request.path
        if request.method == "OPTIONS" and path.startswith("/api/"):
            return ("", 204)
        if path.startswith("/static/"):
            return None
        if path.startswith("/api/") and not path.startswith("/api/auth/"):
            if not session.get("user_id"):
                return jsonify({"error": "Unauthorized", "redirect": "/"}), 401
        return None

    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get("Origin")
        if origin and origin in app.config["ALLOWED_ORIGINS"]:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        return response

    @app.route("/dashboard")
    def dashboard():
        if not session.get("user_id"):
            return redirect("/")
        return render_template("dashboard.html", user=current_public_user())

    @app.route("/tasks")
    def tasks_page():
        if not session.get("user_id"):
            return redirect("/")
        view = str(request.args.get("view", "tasks")).strip().lower()
        if view not in {"tasks", "calendar"}:
            view = "tasks"
        return render_template("tasks.html", user=current_public_user(), task_view=view)

    @app.route("/log")
    def log_page():
        if not session.get("user_id"):
            return redirect("/")
        return render_template("log.html", user=current_public_user())

    @app.route("/analytics")
    def analytics_page():
        if not session.get("user_id"):
            return redirect("/")
        user = current_public_user()
        if not user:
            return redirect("/")
        if not user.get("is_premium"):
            return redirect("/profile")
        return render_template("analytics.html", user=user)

    @app.route("/profile")
    def profile_page():
        if not session.get("user_id"):
            return redirect("/")
        return render_template("profile.html", user=current_public_user())

    @app.route("/notifications")
    def notifications_page():
        if not session.get("user_id"):
            return redirect("/")
        return render_template("notifications.html", user=current_public_user())

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
