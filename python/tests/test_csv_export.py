"""Tests for CSV export endpoint."""

from __future__ import annotations

import csv
from io import StringIO

from fastapi.testclient import TestClient


def test_export_csv_returns_csv_content(client: TestClient) -> None:
    client.post(
        "/transactions",
        json={
            "amount": "12.50",
            "category": "food",
            "description": "Lunch",
            "date": "2026-06-01",
        },
    )
    response = client.get("/transactions/export")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]
    assert "transactions.csv" in response.headers["content-disposition"]


def test_export_csv_contains_transaction_data(client: TestClient) -> None:
    client.post(
        "/transactions",
        json={
            "amount": "12.50",
            "category": "food",
            "description": "Lunch",
            "date": "2026-06-01",
        },
    )
    client.post(
        "/transactions",
        json={
            "amount": "25.00",
            "category": "transport",
            "description": "Gas",
            "date": "2026-06-02",
        },
    )
    response = client.get("/transactions/export")
    assert response.status_code == 200

    reader = csv.DictReader(StringIO(response.text))
    rows = list(reader)
    assert len(rows) == 2
    assert rows[0]["amount"] == "25.00"
    assert rows[0]["category"] == "transport"
    assert rows[0]["description"] == "Gas"
    assert rows[0]["date"] == "2026-06-02"
    assert rows[1]["amount"] == "12.50"
    assert rows[1]["category"] == "food"
    assert rows[1]["description"] == "Lunch"
    assert rows[1]["date"] == "2026-06-01"


def test_export_csv_round_trip(client: TestClient) -> None:
    client.post(
        "/transactions",
        json={
            "amount": "12.50",
            "category": "food",
            "description": "Lunch",
            "date": "2026-06-01",
        },
    )
    client.post(
        "/transactions",
        json={
            "amount": "100.00",
            "category": "entertainment",
            "description": "Concert",
            "date": "2026-06-03",
        },
    )

    export_response = client.get("/transactions/export")
    assert export_response.status_code == 200

    from io import BytesIO
    import_response = client.post(
        "/transactions/import",
        files={"file": ("export.csv", BytesIO(export_response.content), "text/csv")},
    )
    assert import_response.status_code == 201
    imported = import_response.json()
    assert len(imported) == 2


def test_export_empty_csv(client: TestClient) -> None:
    response = client.get("/transactions/export")
    assert response.status_code == 200
    assert "amount,category,description,date" in response.text


def test_export_csv_formula_injection_protection(client: TestClient) -> None:
    client.post(
        "/transactions",
        json={
            "amount": "10.00",
            "category": "food",
            "description": "=1+1",
            "date": "2026-06-01",
        },
    )
    client.post(
        "/transactions",
        json={
            "amount": "20.00",
            "category": "food",
            "description": "@SUM(A1)",
            "date": "2026-06-02",
        },
    )
    response = client.get("/transactions/export")
    assert response.status_code == 200

    reader = csv.DictReader(StringIO(response.text))
    rows = list(reader)
    assert len(rows) == 2
    assert rows[0]["description"] == "'@SUM(A1)"
    assert rows[1]["description"] == "'=1+1"
