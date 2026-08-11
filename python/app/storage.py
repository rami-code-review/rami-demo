"""Transaction persistence and monthly aggregation."""

from __future__ import annotations

import csv
import io
import sqlite3
from collections.abc import Iterator
from datetime import date
from decimal import Decimal, InvalidOperation

from .models import (
    CategoryTotal,
    RecurringRuleIn,
    RecurringRuleOut,
    RecurrenceFrequency,
    Summary,
    TransactionIn,
    TransactionOut,
    from_cents,
    to_cents,
)


class RowError(ValueError):
    """Exception raised when a CSV row cannot be processed. Carries row number."""

    def __init__(self, row_num: int, message: str) -> None:
        self.row_num = row_num
        super().__init__(f"Row {row_num}: {message}")


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


def _neutralize_formula_injection(value: str) -> str:
    """Prefix cells that start with formula indicators to prevent injection attacks."""
    if value and value[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + value
    return value


def export_transactions(conn: sqlite3.Connection) -> str:
    """Export all transactions as CSV content with columns: amount, category, description, date."""
    transactions = list_transactions(conn)
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["amount", "category", "description", "date"])
    writer.writeheader()
    for tx in transactions:
        writer.writerow({
            "amount": _neutralize_formula_injection(str(tx.amount)),
            "category": _neutralize_formula_injection(tx.category.value),
            "description": _neutralize_formula_injection(tx.description),
            "date": _neutralize_formula_injection(tx.date.isoformat()),
        })
    return output.getvalue()


def export_transactions_stream(conn: sqlite3.Connection) -> Iterator[str]:
    """Stream all transactions as CSV with formula injection protection, yielding one line at a time."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["amount", "category", "description", "date"])
    writer.writeheader()
    yield output.getvalue()
    output.truncate(0)
    output.seek(0)

    for tx in list_transactions(conn):
        output.truncate(0)
        output.seek(0)
        writer.writerow({
            "amount": _neutralize_formula_injection(str(tx.amount)),
            "category": _neutralize_formula_injection(tx.category.value),
            "description": _neutralize_formula_injection(tx.description),
            "date": _neutralize_formula_injection(tx.date.isoformat()),
        })
        yield output.getvalue()


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
    with conn:
        for row_num, row in enumerate(reader, start=2):
            try:
                amount_str = row.get("amount", "").strip()
                if not amount_str:
                    raise RowError(row_num, "amount field is empty")
                try:
                    amount = Decimal(amount_str)
                except InvalidOperation as e:
                    raise RowError(row_num, f"amount '{amount_str}' is not a valid number") from e

                category_str = row.get("category", "").strip()
                if not category_str:
                    raise RowError(row_num, "category field is empty")

                date_str = row.get("date", "").strip()
                if not date_str:
                    raise RowError(row_num, "date field is empty")
                try:
                    date_val = date.fromisoformat(date_str)
                except ValueError as e:
                    raise RowError(row_num, f"date '{date_str}' is invalid") from e

                tx_in = TransactionIn(
                    amount=amount,
                    category=category_str,
                    description=row.get("description", "").strip(),
                    date=date_val,
                )
            except (KeyError, AttributeError) as e:
                raise RowError(row_num, f"malformed CSV row - {e}") from e

            inserted.append(create_transaction(conn, tx_in, autocommit=False))

    return inserted


def _row_to_recurring_rule(row: sqlite3.Row) -> RecurringRuleOut:
    """Map a database row to a RecurringRuleOut."""
    return RecurringRuleOut(
        id=row["id"],
        amount=from_cents(row["amount_cents"]),
        category=row["category"],
        description=row["description"],
        frequency=row["frequency"],
        start_date=row["start_date"],
        end_date=row["end_date"],
    )


def create_recurring_rule(conn: sqlite3.Connection, rule: RecurringRuleIn) -> RecurringRuleOut:
    """Insert a recurring rule and return the stored row."""
    row = conn.execute(
        "INSERT INTO recurring_rules (amount_cents, category, description, frequency, start_date, end_date) "
        "VALUES (?, ?, ?, ?, ?, ?) "
        "RETURNING id, amount_cents, category, description, frequency, start_date, end_date",
        (to_cents(rule.amount), rule.category.value, rule.description, rule.frequency.value,
         rule.start_date.isoformat(), rule.end_date.isoformat() if rule.end_date else None),
    ).fetchone()
    if row is None:
        raise RuntimeError("INSERT did not return a row")
    conn.commit()
    return _row_to_recurring_rule(row)


def _generate_occurrences(start_date: date, end_date: date | None, frequency: RecurrenceFrequency, up_to: date) -> list[date]:
    """Generate occurrence dates for a recurring rule up to a given date."""
    from datetime import timedelta

    occurrences = []
    current = start_date
    anchor_day = start_date.day

    if frequency == RecurrenceFrequency.daily:
        while current <= up_to:
            if end_date is None or current <= end_date:
                occurrences.append(current)
            current += timedelta(days=1)
    elif frequency == RecurrenceFrequency.weekly:
        while current <= up_to:
            if end_date is None or current <= end_date:
                occurrences.append(current)
            current += timedelta(days=7)
    elif frequency == RecurrenceFrequency.monthly:
        while current <= up_to:
            if end_date is None or current <= end_date:
                occurrences.append(current)
            if current.month == 12:
                next_month = date(current.year + 1, 1, 1)
            else:
                next_month = date(current.year, current.month + 1, 1)
            last_day_of_next = (next_month.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            target_day = min(anchor_day, last_day_of_next.day)
            current = next_month.replace(day=target_day)
    else:
        raise ValueError(f"unrecognized frequency: {frequency}")

    return occurrences


def generate_due_transactions(conn: sqlite3.Connection, up_to: date) -> list[TransactionOut]:
    """Generate and insert transactions from recurring rules up to a given date."""
    rows = conn.execute(
        "SELECT id, amount_cents, category, description, frequency, start_date, end_date "
        "FROM recurring_rules"
    ).fetchall()

    generated = []
    with conn:
        for row in rows:
            rule_id = row["id"]
            try:
                start_date = date.fromisoformat(row["start_date"])
                end_date = date.fromisoformat(row["end_date"]) if row["end_date"] else None
                frequency = RecurrenceFrequency(row["frequency"])
            except (ValueError, KeyError) as e:
                print(f"Skipping recurring rule {rule_id}: {e}", file=__import__("sys").stderr)
                continue

            occurrences = _generate_occurrences(start_date, end_date, frequency, up_to)

            for occurrence in occurrences:
                occurrence_iso = occurrence.isoformat()
                tx_row = conn.execute(
                    "INSERT OR IGNORE INTO transactions (amount_cents, category, description, date, rule_id) "
                    "VALUES (?, ?, ?, ?, ?) "
                    "RETURNING id, amount_cents, category, description, date",
                    (row["amount_cents"], row["category"], row["description"], occurrence_iso, rule_id),
                ).fetchone()
                if tx_row is not None:
                    generated.append(_row_to_transaction(tx_row))

    return generated
