"""Tests for the transaction CRUD endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _sample(**overrides: object) -> dict:
    payload = {
        "amount": "12.50",
        "category": "food",
        "description": "Lunch",
        "date": "2026-06-01",
    }
    payload.update(overrides)
    return payload


def test_create_returns_stored_transaction(client: TestClient) -> None:
    response = client.post("/transactions", json=_sample())
    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["amount"] == "12.50"
    assert body["category"] == "food"
    assert body["description"] == "Lunch"
    assert body["date"] == "2026-06-01"


def test_amount_is_rounded_to_cents(client: TestClient) -> None:
    response = client.post("/transactions", json=_sample(amount="10.005"))
    assert response.status_code == 201
    assert response.json()["amount"] == "10.01"


def test_non_positive_amount_is_rejected(client: TestClient) -> None:
    assert client.post("/transactions", json=_sample(amount="0")).status_code == 422
    assert client.post("/transactions", json=_sample(amount="-5")).status_code == 422


def test_sub_cent_amount_that_rounds_to_zero_is_rejected(client: TestClient) -> None:
    assert client.post("/transactions", json=_sample(amount="0.003")).status_code == 422


def test_overlong_description_is_rejected(client: TestClient) -> None:
    response = client.post("/transactions", json=_sample(description="x" * 201))
    assert response.status_code == 422


def test_unknown_category_is_rejected(client: TestClient) -> None:
    response = client.post("/transactions", json=_sample(category="vacation"))
    assert response.status_code == 422


def test_list_returns_newest_first(client: TestClient) -> None:
    client.post("/transactions", json=_sample(date="2026-06-01", description="older"))
    client.post("/transactions", json=_sample(date="2026-06-03", description="newer"))
    rows = client.get("/transactions").json()
    assert [r["description"] for r in rows] == ["newer", "older"]


def test_get_missing_returns_404(client: TestClient) -> None:
    assert client.get("/transactions/999").status_code == 404


def test_get_existing_returns_transaction(client: TestClient) -> None:
    created = client.post("/transactions", json=_sample()).json()
    fetched = client.get(f"/transactions/{created['id']}").json()
    assert fetched == created


def test_delete_removes_transaction(client: TestClient) -> None:
    created = client.post("/transactions", json=_sample()).json()
    assert client.delete(f"/transactions/{created['id']}").status_code == 204
    assert client.get(f"/transactions/{created['id']}").status_code == 404


def test_delete_missing_returns_404(client: TestClient) -> None:
    assert client.delete("/transactions/999").status_code == 404
