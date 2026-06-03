import { randomUUID } from "node:crypto";
import type { Task, TaskStatus } from "./task.js";

/** An in-memory store of tasks. Swap this out for a database to add persistence. */
export class TaskStore {
  private tasks = new Map<string, Task>();

  create(title: string): Task {
    const task: Task = {
      id: randomUUID(),
      title,
      done: false,
      createdAt: new Date().toISOString(),
    };
    this.tasks.set(task.id, task);
    return task;
  }

  get(id: string): Task | undefined {
    return this.tasks.get(id);
  }

  list(status: TaskStatus = "all"): Task[] {
    const all = [...this.tasks.values()].sort((a, b) =>
      a.createdAt < b.createdAt ? 1 : a.createdAt > b.createdAt ? -1 : 0,
    );
    if (status === "active") return all.filter((t) => !t.done);
    if (status === "done") return all.filter((t) => t.done);
    return all;
  }

  update(id: string, changes: { title?: string; done?: boolean }): Task | undefined {
    const existing = this.tasks.get(id);
    if (existing === undefined) return undefined;
    const updated: Task = {
      ...existing,
      title: changes.title ?? existing.title,
      done: changes.done ?? existing.done,
    };
    this.tasks.set(id, updated);
    return updated;
  }

  delete(id: string): boolean {
    return this.tasks.delete(id);
  }
}
