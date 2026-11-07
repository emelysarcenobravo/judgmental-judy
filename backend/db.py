import os
import sqlite3

from flask import g

# With DATABASE_URL (Supabase Postgres) the app uses Postgres; without it, a local
# SQLite file next to this file (*.db is gitignored).
DATABASE_URL = os.getenv("DATABASE_URL")
DB_PATH = os.getenv("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "judy.db"))

SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS budgets (
    user_id       INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    income_cents  INTEGER NOT NULL CHECK (income_cents >= 0),
    updated_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS necessities (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name          TEXT NOT NULL,
    amount_cents  INTEGER NOT NULL CHECK (amount_cents >= 0)
);
CREATE TABLE IF NOT EXISTS expenses (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount_cents  INTEGER NOT NULL CHECK (amount_cents > 0),
    category      TEXT NOT NULL,
    note          TEXT NOT NULL DEFAULT '',
    spent_on      TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS expenses_user_date ON expenses (user_id, spent_on);

"""

POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS budgets (
    user_id       BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    income_cents  INTEGER NOT NULL CHECK (income_cents >= 0),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS necessities (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id       BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name          TEXT NOT NULL,
    amount_cents  INTEGER NOT NULL CHECK (amount_cents >= 0)
);
CREATE TABLE IF NOT EXISTS expenses (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id       BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount_cents  INTEGER NOT NULL CHECK (amount_cents > 0),
    category      TEXT NOT NULL,
    note          TEXT NOT NULL DEFAULT '',
    spent_on      DATE NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS expenses_user_date ON expenses (user_id, spent_on);
"""

if DATABASE_URL:
    import psycopg
    from psycopg.rows import dict_row

    IntegrityError = psycopg.errors.UniqueViolation
else:
    IntegrityError = sqlite3.IntegrityError


class Database:
    """Same small API for SQLite and Postgres. Write SQL with ? placeholders."""

    def __init__(self, conn, postgres):
        self.conn = conn
        self.postgres = postgres

    def execute(self, sql, params=()):
        if self.postgres:
            sql = sql.replace("?", "%s")
        return self.conn.execute(sql, params)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()


def connect():
    if DATABASE_URL:
        # prepare_threshold=None keeps this working through Supabase's connection pooler.
        conn = psycopg.connect(DATABASE_URL, row_factory=dict_row, prepare_threshold=None)
        return Database(conn, postgres=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Cheap no-op once the tables exist; recreates them if judy.db is deleted while running.
    conn.executescript(SQLITE_SCHEMA)
    return Database(conn, postgres=False)


def get_db():
    """One connection per request, closed automatically by close_db."""
    if "db" not in g:
        g.db = connect()
    return g.db


def close_db(_exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    app.teardown_appcontext(close_db)
    if DATABASE_URL:
        with psycopg.connect(DATABASE_URL, prepare_threshold=None) as conn:
            conn.execute(POSTGRES_SCHEMA)
