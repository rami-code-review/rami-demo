"""Shared test fixtures: an isolated database and a TestClient bound to it."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db import closing_connection, init_db
from app.main import app, get_db


@pytest.fixture()
def db_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    """Point LEDGER_DB at a fresh temp database and initialize its schema."""
    path = str(tmp_path / "test_ledger.db")
    monkeypatch.setenv("LEDGER_DB", path)
    init_db(path)
    return path


@pytest.fixture()
def client(db_file: str) -> Iterator[TestClient]:
    """A TestClient whose requests run against the temp database."""

    def override_get_db() -> Iterator:
        with closing_connection(db_file) as conn:
            yield conn

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
