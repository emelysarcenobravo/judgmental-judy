"""Turns a real user's rows in the database into the input Judy needs.

load_profile() returns the SAME dict shape as judy/profiles/*.json, so
compute_summary() and build_system_prompt() in persona.py work unchanged on
real users and on sample profiles.

Privacy note: only budget numbers and expense notes go to Claude. The user's
name and email never leave your database.
"""

import calendar
from datetime import date

from budget import month_range
from judy.persona import compute_summary


def load_profile(db, user_id, month=None):
    """Read one user's budget and expenses for a month ('2026-11'; default: this month).

    Returns None if the user hasn't set up a budget yet.
    Raises ValueError if `month` isn't formatted like 2026-11.
    """
    months = month_range(month)
    if months is None:
        raise ValueError("Month must look like 2026-11")
    start, end = months

    budget = db.execute("SELECT income_cents FROM budgets WHERE user_id = ?", (user_id,)).fetchone()
    if budget is None:
        return None

    necessities = db.execute(
        "SELECT name, amount_cents FROM necessities WHERE user_id = ? ORDER BY id", (user_id,)
    ).fetchall()
    expenses = db.execute(
        "SELECT amount_cents, category, note, spent_on FROM expenses "
        "WHERE user_id = ? AND spent_on >= ? AND spent_on < ? ORDER BY spent_on, id",
        (user_id, start, end),
    ).fetchall()

    return {
        "month": start[:7],
        "income_cents": budget["income_cents"],
        "necessities": [
            {"name": r["name"], "amount_cents": r["amount_cents"]} for r in necessities
        ],
        "expenses": [
            {
                "amount_cents": r["amount_cents"],
                "category": r["category"],
                "note": r["note"],
                # Postgres returns a date object, SQLite a string; str() handles both.
                "spent_on": str(r["spent_on"]),
            }
            for r in expenses
        ],
    }


def build_judy_inputs(db, user_id, month=None, today=None):
    """(profile, summary) ready for build_system_prompt(), or (None, None) if no budget yet.

    "Today" is this month's current date, or the last day for a past month, so Judy's
    days-left count is right either way. Note: the server's date is UTC on Render, so
    around midnight it can be a day ahead of the user. Fine for a class project.
    """
    profile = load_profile(db, user_id, month)
    if profile is None:
        return None, None

    today = today or date.today()
    year, mon = (int(p) for p in profile["month"].split("-"))
    if (today.year, today.month) == (year, mon):
        as_of = today
    else:
        as_of = date(year, mon, calendar.monthrange(year, mon)[1])
    return profile, compute_summary(profile, as_of=as_of)