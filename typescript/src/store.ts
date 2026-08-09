import { randomUUID } from "node:crypto";
import type { Task, TaskStatus } from "./task.js";

/** An in-memory store of tasks. Swap this out for a database to add persistence. */
export class TaskStore {
  private tasks = new Map<string, Task>();

  create(title: string, tags?: string[]): Task {
    const task: Task = {
      id: randomUUID(),
      title,
      done: false,
      createdAt: new Date().toISOString(),
      tags: tags && tags.length > 0 ? tags : undefined,
    };
    this.tasks.set(task.id, task);
    return task;
  }

  get(id: string): Task | undefined {
    return this.tasks.get(id);
  }

  list(status: TaskStatus = "all", tag?: string): Task[] {
    const all = [...this.tasks.values()].sort((a, b) =>
      a.createdAt < b.createdAt ? 1 : a.createdAt > b.createdAt ? -1 : 0,
    );
    let filtered = all;
    if (status === "active") filtered = all.filter((t) => !t.done);
    if (status === "done") filtered = all.filter((t) => t.done);
    if (tag !== undefined) {
      filtered = filtered.filter((t) => t.tags && t.tags.includes(tag));
    }
    return filtered;
  }

  update(id: string, changes: { title?: string; done?: boolean; tags?: string[] }): Task | undefined {
    const existing = this.tasks.get(id);
    if (existing === undefined) return undefined;
    const updated: Task = {
      ...existing,
      title: changes.title ?? existing.title,
      done: changes.done ?? existing.done,
      tags: changes.tags !== undefined ? (changes.tags.length > 0 ? changes.tags : undefined) : existing.tags,
    };
    this.tasks.set(id, updated);
    return updated;
  }

  delete(id: string): boolean {
    return this.tasks.delete(id);
  }
}
