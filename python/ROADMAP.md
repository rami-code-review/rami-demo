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
- Tests covering the endpoints and the summary

See [`README.md`](README.md) to run it.

## What's intentionally not built

Pick one of these and open a PR. (Or invent your own — these are a menu,
not a contract.)

### CSV import
Upload a CSV of transactions and import them into the ledger.

### Recurring transactions
Entries that auto-create on a daily, weekly, or monthly schedule.

### Budgets
A per-category monthly cap, with an indicator showing how much is left.

### Search
Filter transactions by date range, category, and free text.

### Export to CSV
Download the current set of transactions as a CSV file.

## How to contribute

Fork the repo, pick a feature above (or your own), and open a PR back to
your fork. Rami reviews it within about a minute.

This repo is for trying Rami — PRs here aren't merged.
