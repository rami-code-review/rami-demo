import { randomUUID } from "node:crypto";
import type { Task, TaskStatus, Recurrence } from "./task.js";
import { getNextDueDate } from "./task.js";

/** An in-memory store of tasks. Swap this out for a database to add persistence. */
export class TaskStore {
  private tasks = new Map<string, Task>();

  create(title: string, tags?: string[], recurrence?: Recurrence, dueDate?: string): Task {
    const task: Task = {
      id: randomUUID(),
      title,
      done: false,
      createdAt: new Date().toISOString(),
      tags: tags && tags.length > 0 ? tags : undefined,
      recurrence,
      dueDate,
    };
    this.tasks.set(task.id, task);
    return task;
  }

  get(id: string): Task | undefined {
    return this.tasks.get(id);
  }

  list(status: TaskStatus = "all", tag?: string, search?: string): Task[] {
    const all = [...this.tasks.values()].sort((a, b) =>
      a.createdAt < b.createdAt ? 1 : a.createdAt > b.createdAt ? -1 : 0,
    );
    let filtered = all;
    if (status === "active") filtered = all.filter((t) => !t.done);
    if (status === "done") filtered = all.filter((t) => t.done);
    if (tag !== undefined) {
      filtered = filtered.filter((t) => t.tags && t.tags.includes(tag));
    }
    if (search !== undefined) {
      const lowerSearch = search.toLowerCase();
      filtered = filtered.filter((t) => t.title.toLowerCase().includes(lowerSearch));
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

    if (existing.done === false && changes.done === true && existing.recurrence && existing.dueDate) {
      const nextDueDate = getNextDueDate(existing.dueDate, existing.recurrence);
      const nextTask: Task = {
        id: randomUUID(),
        title: existing.title,
        done: false,
        createdAt: new Date().toISOString(),
        tags: existing.tags,
        recurrence: existing.recurrence,
        dueDate: nextDueDate,
      };
      this.tasks.set(nextTask.id, nextTask);
    }

    return updated;
  }

  delete(id: string): boolean {
    return this.tasks.delete(id);
  }

  bulkAction(
    ids: string[],
    action: "complete" | "delete",
  ): { succeeded: number; failed: number; failedIds: string[] } {
    let succeeded = 0;
    let failed = 0;
    const failedIds: string[] = [];

    const uniqueIds = [...new Set(ids)];
    for (const id of uniqueIds) {
      if (action === "complete") {
        const existing = this.tasks.get(id);
        if (existing === undefined) {
          failed++;
          failedIds.push(id);
        } else {
          const updated: Task = { ...existing, done: true };
          this.tasks.set(id, updated);

          if (existing.done === false && existing.recurrence && existing.dueDate) {
            const nextDueDate = getNextDueDate(existing.dueDate, existing.recurrence);
            const nextTask: Task = {
              id: randomUUID(),
              title: existing.title,
              done: false,
              createdAt: new Date().toISOString(),
              tags: existing.tags,
              recurrence: existing.recurrence,
              dueDate: nextDueDate,
            };
            this.tasks.set(nextTask.id, nextTask);
          }

          succeeded++;
        }
      } else if (action === "delete") {
        if (!this.tasks.delete(id)) {
          failed++;
          failedIds.push(id);
        } else {
          succeeded++;
        }
      }
    }

    return { succeeded, failed, failedIds };
  }
}
