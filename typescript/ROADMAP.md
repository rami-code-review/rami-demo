# task-manager — roadmap

A small task-management web app: add tasks, mark them done, filter by
status.

## What's built

The core slice: an Express + TypeScript API over an in-memory store.

- `POST /tasks`, `GET /tasks` (with `?status=all|active|done`),
  `GET /tasks/:id`, `PATCH /tasks/:id`, `DELETE /tasks/:id`
- Titles validated and trimmed (1–200 chars); done-toggle and edit
- Endpoint tests via supertest

See [`README.md`](README.md) to run it.

## What's intentionally not built

Pick one of these and open a PR. (Or invent your own — these are a menu,
not a contract.)

### Tagging
Attach one or more tags to a task, and filter the list by tag.

### Recurring tasks
Tasks that re-create themselves on a daily, weekly, or monthly schedule.

### Search
A search box that filters tasks by title as you type.

### Bulk actions
Select multiple tasks at once and complete or delete them in one go.

### Drag-to-reorder
Reorder tasks by dragging, and persist the new order.

## How to contribute

Fork the repo, pick a feature above (or your own), and open a PR back to
your fork. Rami reviews it within about a minute.

This repo is for trying Rami — PRs here aren't merged.
