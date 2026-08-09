"""Tests for the transaction search endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _post(client: TestClient, amount: str, category: str, description: str, date: str) -> None:
    response = client.post(
        "/transactions",
        json={"amount": amount, "category": category, "description": description, "date": date},
    )
    assert response.status_code == 201


def test_search_by_category(client: TestClient) -> None:
    _post(client, "10.00", "food", "Lunch", "2026-06-01")
    _post(client, "50.00", "housing", "Rent", "2026-06-01")
    _post(client, "5.50", "food", "Breakfast", "2026-06-02")

    rows = client.get("/transactions/search", params={"category": "food"}).json()
    assert len(rows) == 2
    assert all(row["category"] == "food" for row in rows)
    assert [row["description"] for row in rows] == ["Breakfast", "Lunch"]


def test_search_by_text(client: TestClient) -> None:
    _post(client, "10.00", "food", "Coffee at Cafe", "2026-06-01")
    _post(client, "50.00", "housing", "Coffee table", "2026-06-01")
    _post(client, "5.50", "food", "Donut", "2026-06-02")

    rows = client.get("/transactions/search", params={"q": "coffee"}).json()
    assert len(rows) == 2
    assert [row["description"] for row in rows] == ["Coffee table", "Coffee at Cafe"]


def test_search_by_date_range(client: TestClient) -> None:
    _post(client, "10.00", "food", "Lunch", "2026-06-01")
    _post(client, "5.00", "food", "Snack", "2026-06-15")
    _post(client, "20.00", "food", "Dinner", "2026-07-01")

    rows = client.get("/transactions/search", params={"start": "2026-06-10", "end": "2026-06-30"}).json()
    assert len(rows) == 1
    assert rows[0]["description"] == "Snack"


def test_search_combines_filters(client: TestClient) -> None:
    _post(client, "10.00", "food", "Pizza", "2026-06-01")
    _post(client, "50.00", "housing", "Rent payment", "2026-06-05")
    _post(client, "5.50", "food", "Pizza slice", "2026-06-10")
    _post(client, "3.00", "food", "Burger", "2026-07-01")

    rows = client.get(
        "/transactions/search",
        params={"q": "pizza", "category": "food", "start": "2026-06-01", "end": "2026-06-30"},
    ).json()
    assert len(rows) == 2
    assert all(row["category"] == "food" for row in rows)
    assert all("pizza" in row["description"].lower() for row in rows)


def test_search_empty_result(client: TestClient) -> None:
    _post(client, "10.00", "food", "Lunch", "2026-06-01")

    rows = client.get("/transactions/search", params={"q": "nonexistent"}).json()
    assert rows == []


def test_search_no_filters_returns_all(client: TestClient) -> None:
    _post(client, "10.00", "food", "Lunch", "2026-06-01")
    _post(client, "50.00", "housing", "Rent", "2026-06-01")
    _post(client, "5.50", "food", "Breakfast", "2026-06-02")

    rows = client.get("/transactions/search").json()
    assert len(rows) == 3


def test_search_text_treats_wildcards_literally(client: TestClient) -> None:
    _post(client, "10.00", "food", "50% off lunch", "2026-06-01")
    _post(client, "50.00", "housing", "Rent", "2026-06-02")

    rows = client.get("/transactions/search", params={"q": "%"}).json()
    assert [row["description"] for row in rows] == ["50% off lunch"]


def test_search_rejects_malformed_date(client: TestClient) -> None:
    response = client.get("/transactions/search", params={"start": "June 2026"})
    assert response.status_code == 422


def test_search_date_range_boundaries_are_inclusive(client: TestClient) -> None:
    _post(client, "10.00", "food", "On start", "2026-06-10")
    _post(client, "20.00", "food", "In range", "2026-06-20")
    _post(client, "30.00", "food", "On end", "2026-06-30")
    _post(client, "40.00", "food", "Before", "2026-06-09")
    _post(client, "50.00", "food", "After", "2026-07-01")

    rows = client.get("/transactions/search", params={"start": "2026-06-10", "end": "2026-06-30"}).json()
    assert sorted(row["description"] for row in rows) == ["In range", "On end", "On start"]
