"""Tools Judy can call to look things up beyond this month's DATA block: other months,
full purchase lists, and repeat purchases. Every tool reads only the logged-in user's rows.
"""

import json
from collections import defaultdict

from budget import CATEGORIES, month_expenses, month_range, month_summary
from judy.persona import CATEGORY_LABELS, clean, money

MONTH_PROPERTY = {"type": "string", "description": "Month as YYYY-MM, e.g. 2026-10"}

TOOLS = [
    {
        "name": "get_month_summary",
        "description": "Income, necessities, discretionary budget, total spent, amount left, and spending per category for any month. Use it for months other than the one in the DATA block, like last month.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {"month": MONTH_PROPERTY},
            "required": ["month"],
            "additionalProperties": False,
        },
    },
    {
        "name": "list_expenses",
        "description": "Every purchase in one month (date, category, note, amount), newest first, plus the total. Use category 'all' for every category.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "month": MONTH_PROPERTY,
                "category": {"type": "string", "enum": ["all", *CATEGORIES]},
            },
            "required": ["month", "category"],
            "additionalProperties": False,
        },
    },
    {
        "name": "find_repeat_purchases",
        "description": "Purchases with the same note bought 2+ times in one month, with how many times and the combined total.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {"month": MONTH_PROPERTY},
            "required": ["month"],
            "additionalProperties": False,
        },
    },
]


def repeat_purchases(expenses):
    groups = defaultdict(list)
    for e in expenses:
        key = e["note"].strip().lower()
        if key:
            groups[key].append(e)
    repeats = sorted((g for g in groups.values() if len(g) >= 2), key=lambda g: -sum(e["amount_cents"] for e in g))
    return [
        {"note": clean(g[0]["note"]), "times": len(g), "total": money(sum(e["amount_cents"] for e in g))}
        for g in repeats
    ]


def run_tool(db, user_id, name, args):
    """Run one tool for this user and return JSON text for the tool_result.
    Raises ValueError for bad input, which goes back to Claude as an error result."""
    months = month_range(args.get("month"))
    if months is None:
        raise ValueError("month must look like 2026-11")

    if name == "get_month_summary":
        s = month_summary(db, user_id, months)
        result = {
            "month": s["month"],
            "income": money(s["income_cents"]),
            "necessities": money(s["necessities_cents"]),
            "discretionary_budget": money(s["discretionary_cents"]),
            "spent": money(s["spent_cents"]),
            "left": money(s["left_cents"]),
            "by_category": {CATEGORY_LABELS.get(r["category"], r["category"]): money(r["total_cents"]) for r in s["by_category"]},
        }
    elif name == "list_expenses":
        category = None if args.get("category") == "all" else args.get("category")
        expenses = month_expenses(db, user_id, months, category)
        result = {
            "count": len(expenses),
            "total": money(sum(e["amount_cents"] for e in expenses)),
            "expenses": [
                {"date": e["spent_on"], "category": e["category"], "note": clean(e["note"]), "amount": money(e["amount_cents"])}
                for e in expenses
            ],
        }
    elif name == "find_repeat_purchases":
        result = {"repeats": repeat_purchases(month_expenses(db, user_id, months))}
    else:
        raise ValueError(f"unknown tool {name}")
    return json.dumps(result)
