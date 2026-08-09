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


def test_import_csv_rejects_non_numeric_amount(client: TestClient) -> None:
    csv_content = """\
amount,category,description,date
not-a-number,food,Lunch,2026-06-01
"""
    response = client.post(
        "/transactions/import",
        files={"file": ("test.csv", BytesIO(csv_content.encode()), "text/csv")},
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "amount" in detail.lower()


def test_import_csv_rejects_missing_required_column(client: TestClient) -> None:
    csv_content = """\
amount,category,description
12.50,food,Lunch
"""
    response = client.post(
        "/transactions/import",
        files={"file": ("test.csv", BytesIO(csv_content.encode()), "text/csv")},
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "date" in detail.lower()


def test_import_csv_rejects_malformed_row(client: TestClient) -> None:
    csv_content = """\
amount,category,description,date
12.50,food
"""
    response = client.post(
        "/transactions/import",
        files={"file": ("test.csv", BytesIO(csv_content.encode()), "text/csv")},
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "row" in detail.lower()


def test_import_csv_partial_failure_does_not_commit(client: TestClient) -> None:
    initial_response = client.get("/transactions")
    initial_count = len(initial_response.json())

    csv_content = """\
amount,category,description,date
12.50,food,Lunch,2026-06-01
not-a-number,food,Dinner,2026-06-02
"""
    response = client.post(
        "/transactions/import",
        files={"file": ("test.csv", BytesIO(csv_content.encode()), "text/csv")},
    )
    assert response.status_code == 422

    final_response = client.get("/transactions")
    final_count = len(final_response.json())
    assert final_count == initial_count


def test_import_csv_rejects_oversized_file(client: TestClient) -> None:
    large_content = b"amount,category,description,date\n" + b"1.00,food,test,2026-06-01\n" * (1024 * 1024)
    response = client.post(
        "/transactions/import",
        files={"file": ("test.csv", BytesIO(large_content), "text/csv")},
    )
    assert response.status_code == 413
    detail = response.json()["detail"]
    assert "large" in detail.lower()
