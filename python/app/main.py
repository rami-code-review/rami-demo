"""FastAPI application exposing the ledger over HTTP."""

from __future__ import annotations

import re
import sqlite3
from collections.abc import AsyncIterator, Iterator
from datetime import date
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, UploadFile

from . import storage
from .db import closing_connection, init_db
from .models import Summary, TransactionIn, TransactionOut

MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Ensure the database schema exists before the app serves requests."""
    init_db()
    yield


app = FastAPI(
    title="ledger",
    description="Record transactions, categorize them, see monthly summaries.",
    lifespan=lifespan,
)


def get_db() -> Iterator[sqlite3.Connection]:
    """Yield a per-request database connection."""
    with closing_connection() as conn:
        yield conn


@app.post("/transactions", response_model=TransactionOut, status_code=201)
def create_transaction(
    tx: TransactionIn, conn: sqlite3.Connection = Depends(get_db)
) -> TransactionOut:
    """Record a new transaction."""
    return storage.create_transaction(conn, tx)


@app.get("/transactions", response_model=list[TransactionOut])
def list_transactions(conn: sqlite3.Connection = Depends(get_db)) -> list[TransactionOut]:
    """List all transactions, newest first."""
    return storage.list_transactions(conn)


@app.get("/transactions/search", response_model=list[TransactionOut])
def search_transactions(
    q: str | None = None,
    category: str | None = None,
    start: str | None = None,
    end: str | None = None,
    conn: sqlite3.Connection = Depends(get_db),
) -> list[TransactionOut]:
    """Search transactions by free text, category, and date range."""
    for label, value in (("start", start), ("end", end)):
        if value is not None:
            try:
                date.fromisoformat(value)
            except ValueError:
                raise HTTPException(status_code=422, detail=f"{label} must be formatted YYYY-MM-DD")
    return storage.search_transactions(conn, q=q, category=category, start=start, end=end)


@app.get("/transactions/{tx_id}", response_model=TransactionOut)
def get_transaction(
    tx_id: int, conn: sqlite3.Connection = Depends(get_db)
) -> TransactionOut:
    """Fetch a single transaction by id."""
    tx = storage.get_transaction(conn, tx_id)
    if tx is None:
        raise HTTPException(status_code=404, detail="transaction not found")
    return tx


@app.delete("/transactions/{tx_id}", status_code=204)
def delete_transaction(tx_id: int, conn: sqlite3.Connection = Depends(get_db)) -> None:
    """Delete a transaction by id."""
    if not storage.delete_transaction(conn, tx_id):
        raise HTTPException(status_code=404, detail="transaction not found")


@app.get("/summary", response_model=Summary)
def summary(
    month: str = Query(..., description="Month to summarize, formatted YYYY-MM."),
    conn: sqlite3.Connection = Depends(get_db),
) -> Summary:
    """Summarize a month's transactions by category."""
    if not MONTH_PATTERN.match(month):
        raise HTTPException(status_code=422, detail="month must be formatted YYYY-MM")
    return storage.monthly_summary(conn, month)


@app.post("/transactions/import", response_model=list[TransactionOut], status_code=201)
def import_transactions(
    file: UploadFile, conn: sqlite3.Connection = Depends(get_db)
) -> list[TransactionOut]:
    """Import transactions from a CSV file."""
    try:
        content = file.file.read()
        csv_text = content.decode("utf-8")
        return storage.import_transactions(conn, csv_text)
    except (ValueError, KeyError, AttributeError, UnicodeDecodeError) as e:
        raise HTTPException(status_code=422, detail=str(e))
