"""Create demo accounts from the sample profiles, so you can log in as them.

Run from backend/ with your venv active:

    python -m judy.seed_demo                  # profiles' dates moved into the current month
    python -m judy.seed_demo --month 2026-11  # or pick the month

Each profile in judy/profiles/ becomes a user:
    email:    demo-<profile file name>@judy.demo   (e.g. demo-tier3_disappointed@judy.demo)
    password: judy-demo-123

Safe to re-run: it deletes and recreates only these demo users.
Careful: if DATABASE_URL is set in backend/.env this writes to the SHARED Supabase database.
"""

import argparse
import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")  # before importing db

from werkzeug.security import generate_password_hash  # noqa: E402

from db import DATABASE_URL, connect  # noqa: E402
from judy.persona import list_profiles, load_profile  # noqa: E402

DEMO_PASSWORD = "judy-demo-123"


def demo_email(profile_name):
    return f"demo-{profile_name}@judy.demo"


def seed(db, profile_name, month):
    profile = load_profile(profile_name)
    email = demo_email(profile_name)

    # Remove the old copy first (children before parent: SQLite doesn't enforce the cascade).
    old = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if old:
        for table in ("expenses", "necessities", "budgets"):
            db.execute(f"DELETE FROM {table} WHERE user_id = ?", (old["id"],))
        db.execute("DELETE FROM users WHERE id = ?", (old["id"],))

    user_id = db.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?) RETURNING id",
        (profile["name"], email, generate_password_hash(DEMO_PASSWORD)),
    ).fetchone()["id"]

    db.execute(
        "INSERT INTO budgets (user_id, income_cents) VALUES (?, ?)",
        (user_id, profile["income_cents"]),
    )
    for n in profile["necessities"]:
        db.execute(
            "INSERT INTO necessities (user_id, name, amount_cents) VALUES (?, ?, ?)",
            (user_id, n["name"], n["amount_cents"]),
        )
    for e in profile["expenses"]:
        spent_on = month + e["spent_on"][7:]  # keep the day, swap "2026-11" for the chosen month
        db.execute(
            "INSERT INTO expenses (user_id, amount_cents, category, note, spent_on) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, e["amount_cents"], e["category"], e["note"], spent_on),
        )
    db.commit()
    return email


def main():
    parser = argparse.ArgumentParser(description="Create demo accounts from the sample profiles.")
    parser.add_argument("--month", default=date.today().strftime("%Y-%m"), help="e.g. 2026-11")
    args = parser.parse_args()

    target = "the SHARED Supabase database (DATABASE_URL)" if DATABASE_URL else "your local SQLite file"
    print(f"This will create demo users in {target}.")
    if DATABASE_URL and input("Type yes to continue: ").strip().lower() != "yes":
        raise SystemExit("Cancelled.")

    db = connect()
    for name in list_profiles():
        print(f"  {seed(db, name, args.month)}")
    db.close()
    print(f"Done. Log in with any of those emails and the password {DEMO_PASSWORD}")


if __name__ == "__main__":
    main()