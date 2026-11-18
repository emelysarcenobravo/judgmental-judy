"""Demo accounts built from the sample profiles in judy/profiles/.

Used by the one-click "Try a demo" buttons (POST /api/auth/demo) and by seed_demo.py.
Each profile's purchases are copied into this month (same day of the month, never in the
future) and into last month at 75% of the price, so Judy has history to compare against.
"""

from datetime import date, timedelta

from werkzeug.security import generate_password_hash

from db import IntegrityError
from judy.persona import load_profile

DEMO_PASSWORD = "judy-demo-123"  # demo data only, so a shared password is fine
LAST_MONTH_SCALE = 0.75


def demo_email(profile_name):
    return f"demo-{profile_name}@judy.demo"


def reset_demo_data(db, user_id, profile, today):
    """Replace this user's budget, necessities and expenses with the profile's."""
    this_month = today.replace(day=1)
    last_month = (this_month - timedelta(days=1)).replace(day=1)

    db.execute(
        "INSERT INTO budgets (user_id, income_cents) VALUES (?, ?) "
        "ON CONFLICT (user_id) DO UPDATE SET income_cents = excluded.income_cents",
        (user_id, profile["income_cents"]),
    )
    db.execute("DELETE FROM necessities WHERE user_id = ?", (user_id,))
    for n in profile["necessities"]:
        db.execute(
            "INSERT INTO necessities (user_id, name, amount_cents) VALUES (?, ?, ?)",
            (user_id, n["name"], n["amount_cents"]),
        )
    db.execute("DELETE FROM expenses WHERE user_id = ?", (user_id,))
    for e in profile["expenses"]:
        day = int(e["spent_on"][8:10])
        copies = [
            (this_month.replace(day=min(day, today.day)), e["amount_cents"]),
            (last_month.replace(day=min(day, 28)), round(e["amount_cents"] * LAST_MONTH_SCALE)),
        ]
        for spent_on, amount in copies:
            db.execute(
                "INSERT INTO expenses (user_id, amount_cents, category, note, spent_on) VALUES (?, ?, ?, ?, ?)",
                (user_id, amount, e["category"], e["note"], spent_on.isoformat()),
            )


def get_demo_user(db, profile_name, today=None):
    """The demo user for a profile, created if needed, with fresh data. Returns the users row."""
    profile = load_profile(profile_name)
    email = demo_email(profile_name)
    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if user is None:
        try:
            db.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (profile["name"], email, generate_password_hash(DEMO_PASSWORD)),
            )
            db.commit()
        except IntegrityError:
            db.rollback()  # another visitor created it at the same moment
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

    reset_demo_data(db, user["id"], profile, today or date.today())
    db.commit()
    return user
