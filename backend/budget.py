from datetime import date

from flask import Blueprint, request, session

from auth import login_required
from db import get_db

budget = Blueprint("budget", __name__, url_prefix="/api")

CATEGORIES = ["food", "shopping", "entertainment", "subscriptions", "transportation", "other"]
MAX_CENTS = 100_000_000  # $1,000,000: anything bigger is a typo


def valid_cents(value, allow_zero=True):
    """Money is stored as whole cents (an int), so $12.50 is 1250."""
    if isinstance(value, bool) or not isinstance(value, int):
        return False
    return (0 if allow_zero else 1) <= value <= MAX_CENTS


def month_range(value):
    """'2026-11' -> ('2026-11-01', '2026-12-01'); this month when value is empty. None if invalid."""
    try:
        start = date.fromisoformat(f"{value}-01") if value else date.today().replace(day=1)
    except ValueError:
        return None
    end = date(start.year + start.month // 12, start.month % 12 + 1, 1)
    return start.isoformat(), end.isoformat()


def public_expense(row):
    return {
        "id": row["id"],
        "amount_cents": row["amount_cents"],
        "category": row["category"],
        "note": row["note"],
        # Postgres returns a date object, SQLite a string; str() gives "2026-11-06" for both.
        "spent_on": str(row["spent_on"]),
    }


@budget.get("/budget")
@login_required
def get_budget():
    user_id = session["user_id"]
    db = get_db()
    row = db.execute("SELECT income_cents FROM budgets WHERE user_id = ?", (user_id,)).fetchone()
    if row is None:
        return {"budget": None}
    items = db.execute(
        "SELECT id, name, amount_cents FROM necessities WHERE user_id = ? ORDER BY id", (user_id,)
    ).fetchall()
    return {
        "budget": {
            "income_cents": row["income_cents"],
            "necessities": [
                {"id": i["id"], "name": i["name"], "amount_cents": i["amount_cents"]} for i in items
            ],
        }
    }


@budget.put("/budget")
@login_required
def save_budget():
    data = request.get_json(silent=True) or {}
    income = data.get("income_cents")
    necessities = data.get("necessities") or []

    if not valid_cents(income):
        return {"error": "Enter your monthly income"}, 400
    if not isinstance(necessities, list) or len(necessities) > 30:
        return {"error": "Too many necessities"}, 400
    for item in necessities:
        name = (item.get("name") or "").strip() if isinstance(item, dict) else ""
        if not name or len(name) > 60 or not valid_cents(item.get("amount_cents")):
            return {"error": "Each necessity needs a name and an amount"}, 400

    user_id = session["user_id"]
    db = get_db()
    # Insert the budget, or update it if this user already has one.
    db.execute(
        "INSERT INTO budgets (user_id, income_cents) VALUES (?, ?) "
        "ON CONFLICT (user_id) DO UPDATE SET income_cents = excluded.income_cents",
        (user_id, income),
    )
    # Replace the whole necessities list with the new one.
    db.execute("DELETE FROM necessities WHERE user_id = ?", (user_id,))
    for item in necessities:
        db.execute(
            "INSERT INTO necessities (user_id, name, amount_cents) VALUES (?, ?, ?)",
            (user_id, item["name"].strip(), item["amount_cents"]),
        )
    db.commit()
    return get_budget()


@budget.get("/expenses")
@login_required
def list_expenses():
    months = month_range(request.args.get("month"))
    if months is None:
        return {"error": "Month must look like 2026-11"}, 400
    rows = get_db().execute(
        "SELECT id, amount_cents, category, note, spent_on FROM expenses "
        "WHERE user_id = ? AND spent_on >= ? AND spent_on < ? "
        "ORDER BY spent_on DESC, id DESC",
        (session["user_id"], *months),
    ).fetchall()
    return {"expenses": [public_expense(r) for r in rows]}


@budget.post("/expenses")
@login_required
def add_expense():
    data = request.get_json(silent=True) or {}
    amount = data.get("amount_cents")
    category = data.get("category")
    note = (data.get("note") or "").strip()
    spent_on = data.get("spent_on") or date.today().isoformat()

    if not valid_cents(amount, allow_zero=False):
        return {"error": "Enter an amount greater than $0"}, 400
    if category not in CATEGORIES:
        return {"error": "Pick a category"}, 400
    if len(note) > 120:
        return {"error": "Keep the note under 120 characters"}, 400
    try:
        date.fromisoformat(spent_on)
    except (TypeError, ValueError):
        return {"error": "Pick a valid date"}, 400

    db = get_db()
    row = db.execute(
        "INSERT INTO expenses (user_id, amount_cents, category, note, spent_on) "
        "VALUES (?, ?, ?, ?, ?) RETURNING id, amount_cents, category, note, spent_on",
        (session["user_id"], amount, category, note, spent_on),
    ).fetchone()
    db.commit()
    return {"expense": public_expense(row)}, 201


@budget.delete("/expenses/<int:expense_id>")
@login_required
def delete_expense(expense_id):
    db = get_db()
    # user_id in the WHERE means nobody can delete someone else's expense.
    cursor = db.execute(
        "DELETE FROM expenses WHERE id = ? AND user_id = ?", (expense_id, session["user_id"])
    )
    db.commit()
    if cursor.rowcount == 0:
        return {"error": "Expense not found"}, 404
    return {"ok": True}


@budget.get("/summary")
@login_required
def get_summary():
    months = month_range(request.args.get("month"))
    if months is None:
        return {"error": "Month must look like 2026-11"}, 400
    user_id = session["user_id"]
    db = get_db()

    row = db.execute("SELECT income_cents FROM budgets WHERE user_id = ?", (user_id,)).fetchone()
    income = row["income_cents"] if row else 0
    necessities = db.execute(
        "SELECT COALESCE(SUM(amount_cents), 0) AS total FROM necessities WHERE user_id = ?",
        (user_id,),
    ).fetchone()["total"]
    by_category = db.execute(
        "SELECT category, SUM(amount_cents) AS total FROM expenses "
        "WHERE user_id = ? AND spent_on >= ? AND spent_on < ? "
        "GROUP BY category ORDER BY total DESC",
        (user_id, *months),
    ).fetchall()

    discretionary = income - necessities  # fun money after the bills
    spent = sum(r["total"] for r in by_category)
    left = discretionary - spent  # negative means overspent
    percent_left = max(0, min(100, round(left / discretionary * 100))) if discretionary > 0 else 0

    return {
        "month": months[0][:7],
        "income_cents": income,
        "necessities_cents": necessities,
        "discretionary_cents": discretionary,
        "spent_cents": spent,
        "left_cents": left,
        "percent_left": percent_left,
        "by_category": [{"category": r["category"], "total_cents": r["total"]} for r in by_category],
    }