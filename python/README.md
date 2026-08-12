# ledger

A small personal-finance app. Record transactions, categorize them, and
see where your money went each month. The scrappy version of the
budgeting app you keep meaning to use.

It's a small HTTP API (FastAPI + SQLite). You POST transactions, list
them back, and ask for a monthly summary by category. See
[`ROADMAP.md`](ROADMAP.md) for what's built and what's open to build.

## Run

Requires Python 3.10+.

```bash
cd python
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# start the API (writes to ./ledger.db; override with LEDGER_DB)
uvicorn app.main:app --reload
```

Then, in another terminal:

```bash
# record a transaction
curl -X POST localhost:8000/transactions \
  -H 'Content-Type: application/json' \
  -d '{"amount": "12.50", "category": "food", "description": "Lunch", "date": "2026-06-01"}'

# list them (newest first)
curl localhost:8000/transactions

# summarize a month by category
curl "localhost:8000/summary?month=2026-06"
```

Interactive API docs are at `localhost:8000/docs`.

Run the tests with:

```bash
pytest
```

## API

| Method | Path | Description |
|---|---|---|
| `POST` | `/transactions` | Record a transaction |
| `GET` | `/transactions` | List all transactions, newest first |
| `GET` | `/transactions/{id}` | Fetch one transaction (404 if absent) |
| `DELETE` | `/transactions/{id}` | Delete one transaction (404 if absent) |
| `GET` | `/summary?month=YYYY-MM` | Per-category totals for a month |

A transaction has an `amount` (positive, in the major currency unit — e.g.
`12.50`), a `category` (one of a fixed set: `income`, `food`, `housing`,
`transport`, `utilities`, `entertainment`, `health`, `other`), an optional
`description`, and a `date` (`YYYY-MM-DD`).

## Architecture

```
app/
  models.py   # Pydantic request/response schemas + the Category enum
  db.py       # SQLite connection + schema (LEDGER_DB sets the path)
  storage.py  # transaction CRUD and monthly aggregation
  main.py     # FastAPI app: routes, per-request DB dependency, startup
tests/
  conftest.py # temp-DB fixture + a TestClient bound to it
```

Money is stored as **integer cents** to avoid floating-point drift, and
converted to and from a decimal amount at the API boundary. Dates are ISO
`YYYY-MM-DD` strings. All SQL is parameterized.

The layers are deliberately thin so a new feature has an obvious home:
the open [roadmap](ROADMAP.md) items (recurring-rule editing, a monthly
statement, multi-currency, transaction tags) each slot into `storage.py`
plus a route in `main.py`.
