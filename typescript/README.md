# task-manager

A small task-management web app. Add tasks, mark them done, filter by
status. The kind of to-do app you'd throw together for yourself in an
afternoon.

It's a small HTTP API (Express + TypeScript) over an in-memory store. See
[`ROADMAP.md`](ROADMAP.md) for what's built and what's open to build.

## Run

Requires Node 20+.

```bash
cd typescript
npm install
npm run dev      # starts on http://localhost:3000 (set PORT to change)
```

Then, in another terminal:

```bash
# add a task
curl -X POST localhost:3000/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title": "Buy milk"}'

# list tasks (newest first); filter with ?status=active|done|all
curl localhost:3000/tasks
curl "localhost:3000/tasks?status=active"

# mark one done (or edit its title)
curl -X PATCH localhost:3000/tasks/<id> \
  -H 'Content-Type: application/json' \
  -d '{"done": true}'
```

Type-check and test with:

```bash
npm run typecheck
npm test
```

## API

| Method | Path | Description |
|---|---|---|
| `POST` | `/tasks` | Add a task (`{ "title": "..." }`) |
| `GET` | `/tasks?status=all\|active\|done` | List tasks, newest first |
| `GET` | `/tasks/:id` | Fetch one task (404 if absent) |
| `PATCH` | `/tasks/:id` | Update `title` and/or `done` |
| `DELETE` | `/tasks/:id` | Delete one task (404 if absent) |

A task has an `id`, a `title` (1–200 characters, trimmed), a `done` flag,
and a `createdAt` timestamp.

## Architecture

```
src/
  task.ts    # the Task type, status values, and title validation
  store.ts   # in-memory CRUD + status filter (swap for a DB to persist)
  app.ts     # createApp(store): Express routes
  server.ts  # starts the server
tests/
  tasks.test.ts  # endpoint tests via supertest
```

`createApp` takes a `TaskStore`, so tests build an app around a fresh
store with no shared state. The layers are thin so a new feature has an
obvious home: the [roadmap](ROADMAP.md) items (tagging, search, bulk
actions, drag-to-reorder, recurring tasks) each slot into `store.ts` plus
a route in `app.ts`.
