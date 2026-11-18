"""Create (or reset) a demo account for every sample profile, so you can log in as them.

Run from backend/ with your venv active:

    python -m judy.seed_demo

Each profile in judy/profiles/ becomes a user:
    email:    demo-<profile file name>@judy.demo   (e.g. demo-level3_disappointed@judy.demo)
    password: judy-demo-123

Visitors can also skip this and click "Try a demo" on the login page, which does the same
thing for one profile. Safe to re-run: it only resets these demo users' data.
Careful: if DATABASE_URL is set in backend/.env this writes to the SHARED Supabase database.
"""

from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")  # before importing db

from db import DATABASE_URL, connect  # noqa: E402
from judy.demo import DEMO_PASSWORD, demo_email, get_demo_user  # noqa: E402
from judy.persona import list_profiles  # noqa: E402


def main():
    target = "the SHARED Supabase database (DATABASE_URL)" if DATABASE_URL else "your local SQLite file"
    print(f"This will create or reset demo users in {target}.")
    if DATABASE_URL and input("Type yes to continue: ").strip().lower() != "yes":
        raise SystemExit("Cancelled.")

    db = connect()
    for name in list_profiles():
        get_demo_user(db, name)
        print(f"  {demo_email(name)}")
    db.close()
    print(f"Done. Log in with any of those emails and the password {DEMO_PASSWORD}")


if __name__ == "__main__":
    main()
