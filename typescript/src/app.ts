import express, { type Express, type Request, type Response } from "express";
import { TaskStore } from "./store.js";
import { isTaskStatus, normalizeTitle, normalizeTags, normalizeRecurrence, normalizeDueDate, ValidationError } from "./task.js";

/** Build the task-manager Express app around a task store. */
export function createApp(store: TaskStore = new TaskStore()): Express {
  const app = express();
  app.use(express.json());

  app.post("/tasks", (req: Request, res: Response) => {
    let title: string;
    let tags: string[] = [];
    let recurrence;
    let dueDate;
    try {
      title = normalizeTitle(req.body?.title);
      tags = normalizeTags(req.body?.tags);
      recurrence = normalizeRecurrence(req.body?.recurrence);
      dueDate = normalizeDueDate(req.body?.dueDate);
    } catch (err) {
      if (err instanceof ValidationError) {
        return res.status(400).json({ error: err.message });
      }
      throw err;
    }
    return res.status(201).json(store.create(title, tags, recurrence, dueDate));
  });

  app.get("/tasks", (req: Request, res: Response) => {
    const statusParam = req.query.status;
    const status = statusParam === undefined ? "all" : String(statusParam);
    if (!isTaskStatus(status)) {
      return res.status(400).json({ error: "status must be one of: all, active, done" });
    }
    const tagParam = req.query.tag;
    const tagValue = Array.isArray(tagParam) ? tagParam[0] : tagParam;
    const tag =
      tagValue === undefined || tagValue === "" ? undefined : String(tagValue);
    const searchParam = req.query.search;
    const searchValue = Array.isArray(searchParam) ? searchParam[0] : searchParam;
    const search =
      searchValue === undefined || searchValue === "" ? undefined : String(searchValue);
    return res.json(store.list(status, tag, search));
  });

  app.get<{ id: string }>("/tasks/:id", (req, res) => {
    const task = store.get(req.params.id);
    if (task === undefined) {
      return res.status(404).json({ error: "task not found" });
    }
    return res.json(task);
  });

  app.patch<{ id: string }>("/tasks/:id", (req, res) => {
    const changes: { title?: string; done?: boolean; tags?: string[] } = {};

    if (req.body?.title !== undefined) {
      try {
        changes.title = normalizeTitle(req.body.title);
      } catch (err) {
        if (err instanceof ValidationError) {
          return res.status(400).json({ error: err.message });
        }
        throw err;
      }
    }

    if (req.body?.done !== undefined) {
      if (typeof req.body.done !== "boolean") {
        return res.status(400).json({ error: "done must be a boolean" });
      }
      changes.done = req.body.done;
    }

    if (req.body?.tags !== undefined) {
      try {
        changes.tags = normalizeTags(req.body.tags);
      } catch (err) {
        if (err instanceof ValidationError) {
          return res.status(400).json({ error: err.message });
        }
        throw err;
      }
    }

    const updated = store.update(req.params.id, changes);
    if (updated === undefined) {
      return res.status(404).json({ error: "task not found" });
    }
    return res.json(updated);
  });

  app.delete<{ id: string }>("/tasks/:id", (req, res) => {
    if (!store.delete(req.params.id)) {
      return res.status(404).json({ error: "task not found" });
    }
    return res.status(204).end();
  });

  app.post("/tasks/bulk/action", (req: Request, res: Response) => {
    const ids = req.body?.ids;
    const action = req.body?.action;

    if (!Array.isArray(ids)) {
      return res.status(400).json({ error: "ids must be an array" });
    }

    if (!ids.every((id): id is string => typeof id === "string")) {
      return res.status(400).json({ error: "each id must be a string" });
    }

    if (action !== "complete" && action !== "delete") {
      return res.status(400).json({ error: "action must be one of: complete, delete" });
    }

    try {
      const result = store.bulkAction(ids, action);
      return res.json(result);
    } catch (err) {
      return res.status(500).json({ error: "internal server error" });
    }
  });

  return app;
}
