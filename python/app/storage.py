"""Transaction persistence and monthly aggregation."""

from __future__ import annotations

import csv
import io
import sqlite3
from datetime import date
from decimal import Decimal, InvalidOperation

from .models import (
    CategoryTotal,
    Summary,
    TransactionIn,
    TransactionOut,
    from_cents,
    to_cents,
)


def _row_to_transaction(row: sqlite3.Row) -> TransactionOut:
    """Map a database row to a TransactionOut."""
    return TransactionOut(
        id=row["id"],
        amount=from_cents(row["amount_cents"]),
        category=row["category"],
        description=row["description"],
        date=row["date"],
    )


def create_transaction(conn: sqlite3.Connection, tx: TransactionIn, autocommit: bool = True) -> TransactionOut:
    """Insert a transaction and return the stored row."""
    row = conn.execute(
        "INSERT INTO transactions (amount_cents, category, description, date) "
        "VALUES (?, ?, ?, ?) "
        "RETURNING id, amount_cents, category, description, date",
        (to_cents(tx.amount), tx.category.value, tx.description, tx.date.isoformat()),
    ).fetchone()
    if row is None:
        raise RuntimeError("INSERT did not return a row")
    if autocommit:
        conn.commit()
    return _row_to_transaction(row)


def get_transaction(conn: sqlite3.Connection, tx_id: int) -> TransactionOut | None:
    """Return a single transaction by id, or None if it does not exist."""
    row = conn.execute(
        "SELECT id, amount_cents, category, description, date "
        "FROM transactions WHERE id = ?",
        (tx_id,),
    ).fetchone()
    return _row_to_transaction(row) if row is not None else None


def list_transactions(conn: sqlite3.Connection) -> list[TransactionOut]:
    """Return all transactions, newest first."""
    rows = conn.execute(
        "SELECT id, amount_cents, category, description, date "
        "FROM transactions ORDER BY date DESC, id DESC"
    ).fetchall()
    return [_row_to_transaction(row) for row in rows]


def delete_transaction(conn: sqlite3.Connection, tx_id: int) -> bool:
    """Delete a transaction by id. Return True if a row was removed."""
    cursor = conn.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
    conn.commit()
    return cursor.rowcount > 0


def _month_bounds(month: str) -> tuple[str, str]:
    """Return the inclusive start and exclusive end ISO dates spanning a YYYY-MM month."""
    year, mon = (int(part) for part in month.split("-"))
    start = date(year, mon, 1)
    end = date(year + 1, 1, 1) if mon == 12 else date(year, mon + 1, 1)
    return start.isoformat(), end.isoformat()


def search_transactions(
    conn: sqlite3.Connection,
    q: str | None = None,
    category: str | None = None,
    start: str | None = None,
    end: str | None = None,
) -> list[TransactionOut]:
    """Return transactions matching the provided filters, newest first."""
    query = "SELECT id, amount_cents, category, description, date FROM transactions WHERE 1=1"
    params: list = []

    if q:
        escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        query += " AND description LIKE ? ESCAPE '\\'"
        params.append(f"%{escaped}%")

    if category:
        query += " AND category = ?"
        params.append(category)

    if start:
        query += " AND date >= ?"
        params.append(start)

    if end:
        query += " AND date <= ?"
        params.append(end)

    query += " ORDER BY date DESC, id DESC"

    rows = conn.execute(query, params).fetchall()
    return [_row_to_transaction(row) for row in rows]


def monthly_summary(conn: sqlite3.Connection, month: str) -> Summary:
    """Return per-category totals and the overall total for the given YYYY-MM month."""
    start, end = _month_bounds(month)
    rows = conn.execute(
        "SELECT category, SUM(amount_cents) AS total_cents "
        "FROM transactions WHERE date >= ? AND date < ? "
        "GROUP BY category ORDER BY category",
        (start, end),
    ).fetchall()
    totals = [
        CategoryTotal(category=row["category"], total=from_cents(row["total_cents"]))
        for row in rows
    ]
    overall = sum((row["total_cents"] for row in rows), 0)
    return Summary(month=month, totals=totals, total=from_cents(overall))


def import_transactions(
    conn: sqlite3.Connection, csv_content: str
) -> list[TransactionOut]:
    """Parse and insert transactions from CSV content. Expected columns: amount, category, description, date."""
    reader = csv.DictReader(io.StringIO(csv_content))
    if reader.fieldnames is None:
        raise ValueError("CSV is empty")

    required_fields = {"amount", "category", "date"}
    if not required_fields.issubset(set(reader.fieldnames)):
        missing = required_fields - set(reader.fieldnames)
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    inserted = []
    try:
        for row_num, row in enumerate(reader, start=2):
            try:
                amount_str = row.get("amount", "").strip()
                if not amount_str:
                    raise ValueError("amount field is empty")
                try:
                    amount = Decimal(amount_str)
                except InvalidOperation as e:
                    raise ValueError(f"amount '{amount_str}' is not a valid number") from e

                category_str = row.get("category", "").strip()
                if not category_str:
                    raise ValueError("category field is empty")

                date_str = row.get("date", "").strip()
                if not date_str:
                    raise ValueError("date field is empty")
                date_val = date.fromisoformat(date_str)

                tx_in = TransactionIn(
                    amount=amount,
                    category=category_str,
                    description=row.get("description", "").strip(),
                    date=date_val,
                )
            except (KeyError, AttributeError) as e:
                raise ValueError(f"Row {row_num}: malformed CSV row - {e}") from e
            except ValueError as e:
                if "Row" in str(e):
                    raise
                raise ValueError(f"Row {row_num}: {e}") from e

            inserted.append(create_transaction(conn, tx_in, autocommit=False))

        conn.commit()
    except (ValueError, KeyError, AttributeError):
        conn.rollback()
        raise

    return inserted
