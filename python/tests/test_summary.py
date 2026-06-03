"""Tests for the monthly summary endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _post(client: TestClient, amount: str, category: str, date: str) -> None:
    response = client.post(
        "/transactions",
        json={"amount": amount, "category": category, "description": "", "date": date},
    )
    assert response.status_code == 201


def test_summary_groups_by_category(client: TestClient) -> None:
    _post(client, "10.00", "food", "2026-06-01")
    _post(client, "5.50", "food", "2026-06-15")
    _post(client, "100.00", "housing", "2026-06-02")
    body = client.get("/summary", params={"month": "2026-06"}).json()

    totals = {row["category"]: row["total"] for row in body["totals"]}
    assert totals == {"food": "15.50", "housing": "100.00"}
    assert body["total"] == "115.50"
    assert body["month"] == "2026-06"


def test_summary_excludes_other_months(client: TestClient) -> None:
    _post(client, "10.00", "food", "2026-06-01")
    _post(client, "99.00", "food", "2026-07-01")
    body = client.get("/summary", params={"month": "2026-06"}).json()
    assert body["total"] == "10.00"


def test_summary_december_spans_year_boundary(client: TestClient) -> None:
    _post(client, "10.00", "food", "2026-12-01")
    _post(client, "20.00", "food", "2026-12-31")
    _post(client, "99.00", "food", "2027-01-01")
    body = client.get("/summary", params={"month": "2026-12"}).json()
    assert body["total"] == "30.00"


def test_summary_empty_month_is_zero(client: TestClient) -> None:
    body = client.get("/summary", params={"month": "2026-06"}).json()
    assert body["totals"] == []
    assert body["total"] == "0.00"


def test_summary_rejects_malformed_month(client: TestClient) -> None:
    assert client.get("/summary", params={"month": "2026-6"}).status_code == 422
    assert client.get("/summary", params={"month": "2026-13"}).status_code == 422
    assert client.get("/summary", params={"month": "June"}).status_code == 422
