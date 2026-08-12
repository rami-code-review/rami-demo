# ledger — roadmap

A small personal-finance app: record transactions, categorize them, see
monthly summaries.

## What's built

The core slice: a FastAPI + SQLite app that records transactions and
summarizes a month.

- `POST /transactions`, `GET /transactions`, `GET /transactions/{id}`,
  `DELETE /transactions/{id}`
- `GET /summary?month=YYYY-MM` — per-category totals for a month
- Eight fixed categories, amounts validated and stored as integer cents
- **Search** — filter transactions by free text, category, and date range
- **CSV import / export** — bulk-load and download transactions as CSV
- **Recurring transactions** — rules that materialize on a daily/weekly/
  monthly schedule
- **Budgets** — a per-category monthly cap with spent/remaining status
- Tests covering the endpoints and the summary

See [`README.md`](README.md) to run it.

## What's intentionally not built

Pick one of these and open a PR. (Or invent your own — these are a menu,
not a contract.)

### Recurring-rule editing
Edit or cancel a recurring rule after it's created (change the amount,
schedule, or end date).

### Monthly statement
Generate a downloadable month-end statement (opening/closing balance,
per-category breakdown, budget vs. actual).

### Multi-currency
Record a transaction in a non-default currency and convert to the base
currency for summaries.

### Transaction tags
Attach free-form tags to a transaction and filter/summarize by tag.

## How to contribute

Fork the repo, pick a feature above (or your own), and open a PR back to
your fork. Rami reviews it within about a minute.

This repo is for trying Rami — PRs here aren't merged.
