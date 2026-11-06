import os
import sqlite3

from flask import g

# The database file lives next to this file; *.db is gitignored.
DB_PATH = os.getenv("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "judy.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def get_db():
    """One connection per request, closed automatically by close_db."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    app.teardown_appcontext(close_db)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(SCHEMA)
