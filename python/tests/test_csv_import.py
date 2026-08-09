"""Tests for CSV import endpoint."""

from __future__ import annotations

from io import BytesIO

from fastapi.testclient import TestClient


def test_import_csv_creates_transactions(client: TestClient) -> None:
    csv_content = """\
amount,category,description,date
12.50,food,Lunch,2026-06-01
25.00,transport,Gas,2026-06-02
100.00,entertainment,Concert,2026-06-03
"""
    response = client.post(
        "/transactions/import",
        files={"file": ("test.csv", BytesIO(csv_content.encode()), "text/csv")},
    )
    assert response.status_code == 201
    body = response.json()
    assert len(body) == 3
    assert body[0]["amount"] == "12.50"
    assert body[0]["category"] == "food"
    assert body[0]["description"] == "Lunch"
    assert body[0]["date"] == "2026-06-01"


def test_imported_transactions_appear_in_list(client: TestClient) -> None:
    csv_content = """\
amount,category,description,date
12.50,food,Lunch,2026-06-01
25.00,housing,Rent,2026-06-05
"""
    client.post(
        "/transactions/import",
        files={"file": ("test.csv", BytesIO(csv_content.encode()), "text/csv")},
    )
    response = client.get("/transactions")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    descriptions = [tx["description"] for tx in body]
    assert "Lunch" in descriptions
    assert "Rent" in descriptions
