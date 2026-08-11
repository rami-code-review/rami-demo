"""Tests for the budget endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _post_transaction(client: TestClient, amount: str, category: str, date: str) -> None:
    response = client.post(
        "/transactions",
        json={"amount": amount, "category": category, "description": "", "date": date},
    )
    assert response.status_code == 201


def _post_budget(client: TestClient, category: str, month: str, amount: str) -> dict:
    response = client.post(
        "/budgets",
        json={"category": category, "month": month, "amount": amount},
    )
    assert response.status_code == 201
    return response.json()


def _get_budget_status(client: TestClient, category: str, month: str) -> dict:
    response = client.get(f"/budgets/{category}/{month}")
    assert response.status_code == 200
    return response.json()


def test_set_budget_and_get_status(client: TestClient) -> None:
    _post_transaction(client, "50.00", "food", "2026-06-01")
    _post_transaction(client, "30.00", "food", "2026-06-15")

    budget = _post_budget(client, "food", "2026-06", "150.00")
    assert budget["category"] == "food"
    assert budget["month"] == "2026-06"
    assert budget["amount"] == "150.00"

    status = _get_budget_status(client, "food", "2026-06")
    assert status["category"] == "food"
    assert status["month"] == "2026-06"
    assert status["cap"] == "150.00"
    assert status["spent"] == "80.00"
    assert status["remaining"] == "70.00"
    assert status["percentage"] == "53.33"


def test_budget_status_calculates_percentage(client: TestClient) -> None:
    _post_transaction(client, "75.00", "housing", "2026-07-10")

    _post_budget(client, "housing", "2026-07", "100.00")
    status = _get_budget_status(client, "housing", "2026-07")

    assert status["spent"] == "75.00"
    assert status["cap"] == "100.00"
    assert status["percentage"] == "75.00"


def test_budget_status_with_no_spending(client: TestClient) -> None:
    _post_budget(client, "entertainment", "2026-08", "200.00")
    status = _get_budget_status(client, "entertainment", "2026-08")

    assert status["spent"] == "0.00"
    assert status["cap"] == "200.00"
    assert status["remaining"] == "200.00"
    assert status["percentage"] == "0.00"


def test_budget_over_cap(client: TestClient) -> None:
    _post_transaction(client, "100.00", "utilities", "2026-09-05")
    _post_transaction(client, "50.00", "utilities", "2026-09-20")

    _post_budget(client, "utilities", "2026-09", "120.00")
    status = _get_budget_status(client, "utilities", "2026-09")

    assert status["spent"] == "150.00"
    assert status["cap"] == "120.00"
    assert status["remaining"] == "-30.00"
    assert status["percentage"] == "125.00"


def test_budget_not_found_returns_404(client: TestClient) -> None:
    response = client.get("/budgets/food/2026-10")
    assert response.status_code == 404


def test_malformed_month_in_budget_status_returns_422(client: TestClient) -> None:
    assert client.get("/budgets/food/2026-13").status_code == 422
    assert client.get("/budgets/food/2026-6").status_code == 422


def test_update_existing_budget(client: TestClient) -> None:
    _post_budget(client, "health", "2026-11", "100.00")
    status1 = _get_budget_status(client, "health", "2026-11")
    assert status1["cap"] == "100.00"

    _post_budget(client, "health", "2026-11", "250.00")
    status2 = _get_budget_status(client, "health", "2026-11")
    assert status2["cap"] == "250.00"


def test_budget_excludes_other_months(client: TestClient) -> None:
    _post_transaction(client, "50.00", "other", "2026-05-15")
    _post_transaction(client, "75.00", "other", "2026-06-15")

    _post_budget(client, "other", "2026-06", "100.00")
    status = _get_budget_status(client, "other", "2026-06")

    assert status["spent"] == "75.00"
    assert status["remaining"] == "25.00"
