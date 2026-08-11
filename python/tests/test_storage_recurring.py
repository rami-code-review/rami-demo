"""Unit tests for recurring rule storage and generation logic."""

from __future__ import annotations

from datetime import date

import pytest

from app.db import closing_connection, init_db
from app.models import Category, RecurringRuleIn, RecurrenceFrequency, TransactionIn
from app.storage import (
    _generate_occurrences,
    create_recurring_rule,
    create_transaction,
    generate_due_transactions,
    list_transactions,
)


@pytest.fixture()
def db_file(tmp_path, monkeypatch):
    """Point LEDGER_DB at a fresh temp database and initialize its schema."""
    path = str(tmp_path / "test_ledger.db")
    monkeypatch.setenv("LEDGER_DB", path)
    init_db(path)
    return path


def test_monthly_day_drift_fix(db_file):
    """Test that monthly rules maintain correct day-of-month despite short months."""
    with closing_connection(db_file) as conn:
        rule = RecurringRuleIn(
            amount=100,
            category=Category.other,
            description="Monthly on the 31st",
            frequency=RecurrenceFrequency.monthly,
            start_date=date(2026, 1, 31),
            end_date=date(2026, 4, 30),
        )
        create_recurring_rule(conn, rule)
        generated = generate_due_transactions(conn, date(2026, 4, 30))

    assert len(generated) == 4
    assert generated[0].date == date(2026, 1, 31)
    assert generated[1].date == date(2026, 2, 28)
    assert generated[2].date == date(2026, 3, 31)
    assert generated[3].date == date(2026, 4, 30)


def test_dedup_with_manual_transaction(db_file):
    """Test that a manual transaction with same amount/category/description does not suppress rule generation."""
    with closing_connection(db_file) as conn:
        rule = RecurringRuleIn(
            amount=50,
            category=Category.food,
            description="Weekly groceries",
            frequency=RecurrenceFrequency.weekly,
            start_date=date(2026, 1, 5),
            end_date=date(2026, 1, 19),
        )
        create_recurring_rule(conn, rule)

        manual_tx = TransactionIn(
            amount=50,
            category=Category.food,
            description="Weekly groceries",
            date=date(2026, 1, 5),
        )
        create_transaction(conn, manual_tx)

        generate_due_transactions(conn, date(2026, 1, 19))

    with closing_connection(db_file) as conn:
        all_txs = list_transactions(conn)
        dates = sorted([tx.date for tx in all_txs])
        assert dates == [date(2026, 1, 5), date(2026, 1, 5), date(2026, 1, 12), date(2026, 1, 19)]


def test_generate_is_idempotent_per_rule(db_file):
    """Test that calling generate_due_transactions twice does not duplicate rule-generated transactions."""
    with closing_connection(db_file) as conn:
        rule = RecurringRuleIn(
            amount=25,
            category=Category.transport,
            description="Weekly transit",
            frequency=RecurrenceFrequency.weekly,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 15),
        )
        create_recurring_rule(conn, rule)

        generated1 = generate_due_transactions(conn, date(2026, 1, 15))
        generated2 = generate_due_transactions(conn, date(2026, 1, 15))

    assert len(generated1) == 3
    assert len(generated2) == 0
    with closing_connection(db_file) as conn:
        all_txs = list_transactions(conn)
        assert len(all_txs) == 3


def test_two_rules_do_not_collide(db_file):
    """Test that two different rules with the same amount/category/description on same date both generate transactions."""
    with closing_connection(db_file) as conn:
        rule1 = RecurringRuleIn(
            amount=30,
            category=Category.entertainment,
            description="Event ticket",
            frequency=RecurrenceFrequency.monthly,
            start_date=date(2026, 1, 15),
            end_date=date(2026, 3, 15),
        )
        rule2 = RecurringRuleIn(
            amount=30,
            category=Category.entertainment,
            description="Event ticket",
            frequency=RecurrenceFrequency.monthly,
            start_date=date(2026, 1, 20),
            end_date=date(2026, 3, 20),
        )
        create_recurring_rule(conn, rule1)
        create_recurring_rule(conn, rule2)

        generate_due_transactions(conn, date(2026, 3, 31))

    with closing_connection(db_file) as conn:
        all_txs = list_transactions(conn)
        assert len(all_txs) == 6


def test_generate_occurrences_daily():
    """Test daily recurrence generates correct occurrences."""
    occurrences = _generate_occurrences(
        date(2026, 1, 1),
        date(2026, 1, 5),
        RecurrenceFrequency.daily,
        date(2026, 1, 5),
    )
    assert occurrences == [
        date(2026, 1, 1),
        date(2026, 1, 2),
        date(2026, 1, 3),
        date(2026, 1, 4),
        date(2026, 1, 5),
    ]


def test_generate_occurrences_weekly():
    """Test weekly recurrence generates correct occurrences."""
    occurrences = _generate_occurrences(
        date(2026, 1, 1),
        None,
        RecurrenceFrequency.weekly,
        date(2026, 1, 22),
    )
    assert occurrences == [
        date(2026, 1, 1),
        date(2026, 1, 8),
        date(2026, 1, 15),
        date(2026, 1, 22),
    ]


def test_generate_occurrences_monthly_respects_end_date():
    """Test monthly recurrence respects end_date."""
    occurrences = _generate_occurrences(
        date(2026, 1, 15),
        date(2026, 2, 15),
        RecurrenceFrequency.monthly,
        date(2026, 3, 15),
    )
    assert occurrences == [
        date(2026, 1, 15),
        date(2026, 2, 15),
    ]


def test_malformed_rule_does_not_block_valid_rules(db_file):
    """Test that a rule with malformed date does not prevent other rules from generating."""
    with closing_connection(db_file) as conn:
        rule = RecurringRuleIn(
            amount=50,
            category=Category.food,
            description="Valid weekly groceries",
            frequency=RecurrenceFrequency.weekly,
            start_date=date(2026, 1, 5),
            end_date=date(2026, 1, 19),
        )
        create_recurring_rule(conn, rule)

        conn.execute(
            "INSERT INTO recurring_rules (amount_cents, category, description, frequency, start_date, end_date) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (3000, "food", "Bad rule", "weekly", "2026-13-01", None),
        )
        conn.commit()

        generated = generate_due_transactions(conn, date(2026, 1, 19))

    assert len(generated) == 3
    assert all(tx.description == "Valid weekly groceries" for tx in generated)
    dates = [tx.date for tx in generated]
    assert dates == [date(2026, 1, 5), date(2026, 1, 12), date(2026, 1, 19)]
