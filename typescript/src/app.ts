import express, { type Express, type Request, type Response } from "express";
import { TaskStore } from "./store.js";
import { isTaskStatus, normalizeTitle, normalizeTags, ValidationError } from "./task.js";

/** Build the task-manager Express app around a task store. */
export function createApp(store: TaskStore = new TaskStore()): Express {
  const app = express();
  app.use(express.json());

  app.post("/tasks", (req: Request, res: Response) => {
    let title: string;
    let tags: string[] = [];
    try {
      title = normalizeTitle(req.body?.title);
      tags = normalizeTags(req.body?.tags);
    } catch (err) {
      if (err instanceof ValidationError) {
        return res.status(400).json({ error: err.message });
      }
      throw err;
    }
    return res.status(201).json(store.create(title, tags));
  });

  app.get("/tasks", (req: Request, res: Response) => {
    const statusParam = req.query.status;
    const status = statusParam === undefined ? "all" : String(statusParam);
    if (!isTaskStatus(status)) {
      return res.status(400).json({ error: "status must be one of: all, active, done" });
    }
    const tagParam = req.query.tag;
    const tag = tagParam === undefined ? undefined : String(tagParam);
    return res.json(store.list(status, tag));
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

  return app;
}
