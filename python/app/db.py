"""SQLite connection management and schema for the ledger."""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

DEFAULT_DB_PATH = "ledger.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS transactions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    amount_cents INTEGER NOT NULL,
    category    TEXT    NOT NULL,
    description TEXT    NOT NULL DEFAULT '',
    date        TEXT    NOT NULL,
    rule_id     INTEGER
);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
CREATE TABLE IF NOT EXISTS recurring_rules (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    amount_cents INTEGER NOT NULL,
    category     TEXT    NOT NULL,
    description  TEXT    NOT NULL DEFAULT '',
    frequency    TEXT    NOT NULL,
    start_date   TEXT    NOT NULL,
    end_date     TEXT
);
"""


def db_path() -> str:
    """Return the configured SQLite database path, from LEDGER_DB or the default."""
    return os.environ.get("LEDGER_DB", DEFAULT_DB_PATH)


def connect(path: str | None = None) -> sqlite3.Connection:
    """Open a SQLite connection with row access by column name and foreign keys enabled."""
    conn = sqlite3.connect(path or db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(path: str | None = None) -> None:
    """Create the schema if it does not yet exist."""
    with closing_connection(path) as conn:
        conn.executescript(SCHEMA)


@contextmanager
def closing_connection(path: str | None = None) -> Iterator[sqlite3.Connection]:
    """Yield a connection that is closed when the block exits."""
    conn = connect(path)
    try:
        yield conn
    finally:
        conn.close()
