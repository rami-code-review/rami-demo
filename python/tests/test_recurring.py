"""Tests for recurring transaction rules and generation."""

from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient


def _sample_rule(**overrides: object) -> dict:
    payload = {
        "amount": "50.00",
        "category": "food",
        "description": "Groceries",
        "frequency": "weekly",
        "start_date": "2026-06-01",
    }
    payload.update(overrides)
    return payload


def test_create_recurring_rule(client: TestClient) -> None:
    response = client.post("/recurring-rules", json=_sample_rule())
    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["amount"] == "50.00"
    assert body["category"] == "food"
    assert body["description"] == "Groceries"
    assert body["frequency"] == "weekly"
    assert body["start_date"] == "2026-06-01"
    assert body["end_date"] is None


def test_create_recurring_rule_with_end_date(client: TestClient) -> None:
    response = client.post("/recurring-rules", json=_sample_rule(end_date="2026-12-31"))
    assert response.status_code == 201
    body = response.json()
    assert body["end_date"] == "2026-12-31"


def test_generate_daily_transactions(client: TestClient) -> None:
    client.post("/recurring-rules", json=_sample_rule(
        frequency="daily",
        start_date="2026-06-01",
        amount="10.00",
        description="Daily coffee",
    ))

    response = client.post("/recurring-rules/generate?up_to=2026-06-05")
    assert response.status_code == 201
    transactions = response.json()
    assert len(transactions) == 5

    for i, tx in enumerate(transactions, start=1):
        expected_day = 1 + i - 1
        assert tx["amount"] == "10.00"
        assert tx["category"] == "food"
        assert tx["description"] == "Daily coffee"
        assert tx["date"] == f"2026-06-{expected_day:02d}"


def test_generate_weekly_transactions(client: TestClient) -> None:
    client.post("/recurring-rules", json=_sample_rule(
        frequency="weekly",
        start_date="2026-06-01",
        amount="50.00",
        description="Groceries",
    ))

    response = client.post("/recurring-rules/generate?up_to=2026-06-22")
    assert response.status_code == 201
    transactions = response.json()
    assert len(transactions) == 4

    expected_dates = ["2026-06-01", "2026-06-08", "2026-06-15", "2026-06-22"]
    for tx, expected_date in zip(transactions, expected_dates):
        assert tx["date"] == expected_date
        assert tx["amount"] == "50.00"


def test_generate_monthly_transactions(client: TestClient) -> None:
    client.post("/recurring-rules", json=_sample_rule(
        frequency="monthly",
        start_date="2026-06-15",
        amount="100.00",
        description="Rent",
    ))

    response = client.post("/recurring-rules/generate?up_to=2026-09-15")
    assert response.status_code == 201
    transactions = response.json()
    assert len(transactions) == 4

    expected_dates = ["2026-06-15", "2026-07-15", "2026-08-15", "2026-09-15"]
    for tx, expected_date in zip(transactions, expected_dates):
        assert tx["date"] == expected_date


def test_generate_with_end_date(client: TestClient) -> None:
    client.post("/recurring-rules", json=_sample_rule(
        frequency="weekly",
        start_date="2026-06-01",
        end_date="2026-06-15",
        amount="50.00",
        description="Groceries",
    ))

    response = client.post("/recurring-rules/generate?up_to=2026-06-30")
    assert response.status_code == 201
    transactions = response.json()
    assert len(transactions) == 3

    expected_dates = ["2026-06-01", "2026-06-08", "2026-06-15"]
    for tx, expected_date in zip(transactions, expected_dates):
        assert tx["date"] == expected_date


def test_generate_no_duplicates(client: TestClient) -> None:
    client.post("/recurring-rules", json=_sample_rule(
        frequency="weekly",
        start_date="2026-06-01",
        amount="50.00",
        description="Groceries",
    ))

    response = client.post("/recurring-rules/generate?up_to=2026-06-15")
    assert response.status_code == 201
    assert len(response.json()) == 3

    response = client.post("/recurring-rules/generate?up_to=2026-06-30")
    assert response.status_code == 201
    generated = response.json()
    assert len(generated) == 2

    response = client.post("/recurring-rules/generate?up_to=2026-07-06")
    assert response.status_code == 201
    generated = response.json()
    assert len(generated) == 1
