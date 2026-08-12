# task-manager — roadmap

A small task-management web app: add tasks, mark them done, filter by
status.

## What's built

The core slice: an Express + TypeScript API over an in-memory store.

- `POST /tasks`, `GET /tasks` (with `?status=all|active|done`),
  `GET /tasks/:id`, `PATCH /tasks/:id`, `DELETE /tasks/:id`
- Titles validated and trimmed (1–200 chars); done-toggle and edit
- **Tagging** — attach tags to a task and filter the list by tag
- **Bulk actions** — complete or delete many tasks in one request
- **Search** — filter tasks by title with `?search=`
- **Recurring tasks** — completing one spawns its next occurrence
- **Drag-to-reorder** — set and persist a manual task order
- Endpoint tests via supertest

See [`README.md`](README.md) to run it.

## What's intentionally not built

Pick one of these and open a PR. (Or invent your own — these are a menu,
not a contract.)

### Due dates
Give a task a due date and filter for what's due or overdue.

### Subtasks
Nest checklist items under a task and roll their completion up.

### Priority + sort
Assign a priority and sort the list by priority (composing with the
existing filters).

### CSV import
Bulk-create tasks from an uploaded CSV.

## How to contribute

Fork the repo, pick a feature above (or your own), and open a PR back to
your fork. Rami reviews it within about a minute.

This repo is for trying Rami — PRs here aren't merged.
