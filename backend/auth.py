import re
import sqlite3
from functools import wraps

from flask import Blueprint, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_db

auth = Blueprint("auth", __name__, url_prefix="/api/auth")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def public_user(row):
    return {"id": row["id"], "name": row["name"], "email": row["email"]}


def current_user():
    user_id = session.get("user_id")
    if user_id is None:
        return None
    return get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def login_required(view):
    """Use on any route that needs a logged-in user: @login_required"""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            return {"error": "Please log in first"}, 401
        return view(*args, **kwargs)
    return wrapped


@auth.post("/signup")
def signup():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name:
        return {"error": "Name is required"}, 400
    if not EMAIL_RE.match(email):
        return {"error": "Enter a valid email"}, 400
    if len(password) < 8:
        return {"error": "Password must be at least 8 characters"}, 400

    db = get_db()
    try:
        cur = db.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(password)),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return {"error": "An account with that email already exists"}, 409

    session.clear()
    session["user_id"] = cur.lastrowid
    return {"user": public_user(current_user())}, 201


@auth.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    # Same message either way, so the form doesn't reveal which emails have accounts.
    if user is None or not check_password_hash(user["password_hash"], password):
        return {"error": "Incorrect email or password"}, 401

    session.clear()
    session["user_id"] = user["id"]
    return {"user": public_user(user)}


@auth.post("/logout")
def logout():
    session.clear()
    return {"ok": True}


@auth.get("/me")
def me():
    user = current_user()
    return {"user": public_user(user) if user else None}
