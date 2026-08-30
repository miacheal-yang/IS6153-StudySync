from flask import Blueprint, redirect, render_template, session

landing_bp = Blueprint("landing", __name__)


@landing_bp.route("/")
def landing_page():
    if session.get("user_id"):
        return redirect("/dashboard")
    return render_template("landing.html")


@landing_bp.route("/login")
def login_page():
    if session.get("user_id"):
        return redirect("/dashboard")
    return render_template("login.html")


@landing_bp.route("/register")
def register_page():
    if session.get("user_id"):
        return redirect("/dashboard")
    return render_template("register.html")
