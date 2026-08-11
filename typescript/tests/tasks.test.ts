import { describe, expect, it } from "vitest";
import request from "supertest";
import { createApp } from "../src/app.js";
import { TaskStore } from "../src/store.js";

function app() {
  return createApp();
}

describe("POST /tasks", () => {
  it("creates a task and returns it", async () => {
    const res = await request(app()).post("/tasks").send({ title: "Write tests" });
    expect(res.status).toBe(201);
    expect(res.body.id).toBeTruthy();
    expect(res.body.title).toBe("Write tests");
    expect(res.body.done).toBe(false);
    expect(res.body.createdAt).toBeTruthy();
  });

  it("trims the title", async () => {
    const res = await request(app()).post("/tasks").send({ title: "  spaced  " });
    expect(res.body.title).toBe("spaced");
  });

  it("rejects an empty title", async () => {
    const res = await request(app()).post("/tasks").send({ title: "   " });
    expect(res.status).toBe(400);
  });

  it("rejects a missing title", async () => {
    const res = await request(app()).post("/tasks").send({});
    expect(res.status).toBe(400);
  });

  it("rejects an overlong title", async () => {
    const res = await request(app())
      .post("/tasks")
      .send({ title: "x".repeat(201) });
    expect(res.status).toBe(400);
  });

  it("creates a task with tags", async () => {
    const res = await request(app())
      .post("/tasks")
      .send({ title: "Write tests", tags: ["work", "urgent"] });
    expect(res.status).toBe(201);
    expect(res.body.tags).toEqual(["work", "urgent"]);
  });

  it("rejects tags that are not an array", async () => {
    const res = await request(app())
      .post("/tasks")
      .send({ title: "Task", tags: "work" });
    expect(res.status).toBe(400);
  });

  it("rejects tags with non-string elements", async () => {
    const res = await request(app())
      .post("/tasks")
      .send({ title: "Task", tags: ["work", 123] });
    expect(res.status).toBe(400);
  });
});

describe("GET /tasks", () => {
  it("lists tasks in creation order", async () => {
    const api = app();
    await request(api).post("/tasks").send({ title: "first" });
    await request(api).post("/tasks").send({ title: "second" });
    const res = await request(api).get("/tasks");
    expect(res.status).toBe(200);
    expect(res.body.map((t: { title: string }) => t.title)).toEqual(["first", "second"]);
  });

  it("filters by status", async () => {
    const api = app();
    const a = await request(api).post("/tasks").send({ title: "active one" });
    await request(api).post("/tasks").send({ title: "done one" });
    const second = (await request(api).get("/tasks")).body.find(
      (t: { title: string }) => t.title === "done one",
    );
    await request(api).patch(`/tasks/${second.id}`).send({ done: true });

    const active = await request(api).get("/tasks?status=active");
    expect(active.body.map((t: { title: string }) => t.title)).toEqual(["active one"]);
    const done = await request(api).get("/tasks?status=done");
    expect(done.body.map((t: { title: string }) => t.title)).toEqual(["done one"]);
    expect(a.status).toBe(201);
  });

  it("rejects an unknown status", async () => {
    const res = await request(app()).get("/tasks?status=archived");
    expect(res.status).toBe(400);
  });

  it("filters by tag", async () => {
    const api = app();
    await request(api).post("/tasks").send({ title: "work task", tags: ["work"] });
    await request(api).post("/tasks").send({ title: "personal task", tags: ["personal"] });
    await request(api).post("/tasks").send({ title: "both", tags: ["work", "personal"] });

    const workTasks = await request(api).get("/tasks?tag=work");
    expect(workTasks.body.length).toBe(2);
    expect(workTasks.body.map((t: { title: string }) => t.title).sort()).toEqual(["both", "work task"]);

    const personalTasks = await request(api).get("/tasks?tag=personal");
    expect(personalTasks.body.length).toBe(2);
    expect(personalTasks.body.map((t: { title: string }) => t.title).sort()).toEqual(["both", "personal task"]);
  });

  it("composes tag and status filters", async () => {
    const api = app();
    const t1 = await request(api).post("/tasks").send({ title: "active work", tags: ["work"] });
    const t2 = await request(api).post("/tasks").send({ title: "done work", tags: ["work"] });
    const t3 = await request(api).post("/tasks").send({ title: "active personal", tags: ["personal"] });

    await request(api).patch(`/tasks/${t2.body.id}`).send({ done: true });

    const result = await request(api).get("/tasks?tag=work&status=active");
    expect(result.body.map((t: { title: string }) => t.title)).toEqual(["active work"]);
  });

  it("filters by search query", async () => {
    const api = app();
    await request(api).post("/tasks").send({ title: "buy milk" });
    await request(api).post("/tasks").send({ title: "drink milk" });
    await request(api).post("/tasks").send({ title: "feed the cat" });

    const result = await request(api).get("/tasks?search=milk");
    expect(result.body.length).toBe(2);
    expect(result.body.map((t: { title: string }) => t.title).sort()).toEqual(["buy milk", "drink milk"]);
  });

  it("searches case-insensitively", async () => {
    const api = app();
    await request(api).post("/tasks").send({ title: "Buy Milk" });
    await request(api).post("/tasks").send({ title: "DRINK COFFEE" });

    const result = await request(api).get("/tasks?search=milk");
    expect(result.body.length).toBe(1);
    expect(result.body[0].title).toBe("Buy Milk");
  });

  it("composes search with status and tag filters", async () => {
    const api = app();
    const t1 = await request(api).post("/tasks").send({ title: "buy milk", tags: ["shopping"] });
    const t2 = await request(api).post("/tasks").send({ title: "drink milk", tags: ["shopping"] });
    const t3 = await request(api).post("/tasks").send({ title: "buy coffee", tags: ["shopping"] });

    await request(api).patch(`/tasks/${t2.body.id}`).send({ done: true });

    const result = await request(api).get("/tasks?search=milk&status=active&tag=shopping");
    expect(result.body.length).toBe(1);
    expect(result.body[0].title).toBe("buy milk");
  });
});

describe("GET /tasks/:id", () => {
  it("returns an existing task", async () => {
    const api = app();
    const created = await request(api).post("/tasks").send({ title: "find me" });
    const res = await request(api).get(`/tasks/${created.body.id}`);
    expect(res.status).toBe(200);
    expect(res.body).toEqual(created.body);
  });

  it("returns 404 for a missing task", async () => {
    const res = await request(app()).get("/tasks/nope");
    expect(res.status).toBe(404);
  });
});

describe("PATCH /tasks/:id", () => {
  it("toggles done", async () => {
    const api = app();
    const created = await request(api).post("/tasks").send({ title: "toggle me" });
    const res = await request(api).patch(`/tasks/${created.body.id}`).send({ done: true });
    expect(res.status).toBe(200);
    expect(res.body.done).toBe(true);
  });

  it("edits the title", async () => {
    const api = app();
    const created = await request(api).post("/tasks").send({ title: "old" });
    const res = await request(api).patch(`/tasks/${created.body.id}`).send({ title: "new" });
    expect(res.body.title).toBe("new");
  });

  it("rejects a non-boolean done", async () => {
    const api = app();
    const created = await request(api).post("/tasks").send({ title: "t" });
    const res = await request(api).patch(`/tasks/${created.body.id}`).send({ done: "yes" });
    expect(res.status).toBe(400);
  });

  it("leaves the task unchanged for an empty body", async () => {
    const api = app();
    const created = await request(api).post("/tasks").send({ title: "unchanged" });
    const res = await request(api).patch(`/tasks/${created.body.id}`).send({});
    expect(res.status).toBe(200);
    expect(res.body).toEqual(created.body);
  });

  it("can reset done back to false", async () => {
    const api = app();
    const created = await request(api).post("/tasks").send({ title: "flip" });
    await request(api).patch(`/tasks/${created.body.id}`).send({ done: true });
    const res = await request(api).patch(`/tasks/${created.body.id}`).send({ done: false });
    expect(res.body.done).toBe(false);
  });

  it("returns 404 for a missing task", async () => {
    const res = await request(app()).patch("/tasks/nope").send({ done: true });
    expect(res.status).toBe(404);
  });

  it("updates tags", async () => {
    const api = app();
    const created = await request(api)
      .post("/tasks")
      .send({ title: "task", tags: ["old"] });
    const res = await request(api)
      .patch(`/tasks/${created.body.id}`)
      .send({ tags: ["new", "tags"] });
    expect(res.status).toBe(200);
    expect(res.body.tags).toEqual(["new", "tags"]);
  });

  it("clears tags when set to empty array", async () => {
    const api = app();
    const created = await request(api)
      .post("/tasks")
      .send({ title: "task", tags: ["work"] });
    const res = await request(api)
      .patch(`/tasks/${created.body.id}`)
      .send({ tags: [] });
    expect(res.body.tags).toBeUndefined();
  });

  it("rejects non-array tags in PATCH", async () => {
    const api = app();
    const created = await request(api).post("/tasks").send({ title: "t" });
    const res = await request(api)
      .patch(`/tasks/${created.body.id}`)
      .send({ tags: "work" });
    expect(res.status).toBe(400);
  });
});

describe("DELETE /tasks/:id", () => {
  it("deletes a task", async () => {
    const api = app();
    const created = await request(api).post("/tasks").send({ title: "delete me" });
    const del = await request(api).delete(`/tasks/${created.body.id}`);
    expect(del.status).toBe(204);
    expect((await request(api).get(`/tasks/${created.body.id}`)).status).toBe(404);
  });

  it("returns 404 for a missing task", async () => {
    const res = await request(app()).delete("/tasks/nope");
    expect(res.status).toBe(404);
  });
});

describe("POST /tasks/bulk/action", () => {
  it("completes multiple tasks", async () => {
    const api = app();
    const t1 = await request(api).post("/tasks").send({ title: "first" });
    const t2 = await request(api).post("/tasks").send({ title: "second" });
    const t3 = await request(api).post("/tasks").send({ title: "third" });

    const res = await request(api).post("/tasks/bulk/action").send({
      ids: [t1.body.id, t2.body.id, t3.body.id],
      action: "complete",
    });

    expect(res.status).toBe(200);
    expect(res.body.succeeded).toBe(3);
    expect(res.body.failed).toBe(0);
    expect(res.body.failedIds).toEqual([]);

    const done = await request(api).get("/tasks?status=done");
    expect(done.body.length).toBe(3);
  });

  it("deletes multiple tasks", async () => {
    const api = app();
    const t1 = await request(api).post("/tasks").send({ title: "delete 1" });
    const t2 = await request(api).post("/tasks").send({ title: "delete 2" });
    const t3 = await request(api).post("/tasks").send({ title: "keep me" });

    const res = await request(api).post("/tasks/bulk/action").send({
      ids: [t1.body.id, t2.body.id],
      action: "delete",
    });

    expect(res.status).toBe(200);
    expect(res.body.succeeded).toBe(2);
    expect(res.body.failed).toBe(0);

    const all = await request(api).get("/tasks");
    expect(all.body.length).toBe(1);
    expect(all.body[0].title).toBe("keep me");
  });

  it("handles mix of existing and missing ids", async () => {
    const api = app();
    const t1 = await request(api).post("/tasks").send({ title: "exists" });

    const res = await request(api).post("/tasks/bulk/action").send({
      ids: [t1.body.id, "nonexistent1", "nonexistent2"],
      action: "complete",
    });

    expect(res.status).toBe(200);
    expect(res.body.succeeded).toBe(1);
    expect(res.body.failed).toBe(2);
    expect(res.body.failedIds).toContain("nonexistent1");
    expect(res.body.failedIds).toContain("nonexistent2");

    const done = await request(api).get("/tasks?status=done");
    expect(done.body[0].id).toBe(t1.body.id);
  });

  it("rejects non-array ids", async () => {
    const res = await request(app()).post("/tasks/bulk/action").send({
      ids: "not-an-array",
      action: "complete",
    });

    expect(res.status).toBe(400);
    expect(res.body.error).toContain("ids must be an array");
  });

  it("rejects invalid action", async () => {
    const res = await request(app()).post("/tasks/bulk/action").send({
      ids: ["some-id"],
      action: "invalid",
    });

    expect(res.status).toBe(400);
    expect(res.body.error).toContain("action must be one of");
  });

  it("deduplicates ids and counts each task once", async () => {
    const api = app();
    const t1 = await request(api).post("/tasks").send({ title: "dedupe test" });

    const res = await request(api).post("/tasks/bulk/action").send({
      ids: [t1.body.id, t1.body.id],
      action: "complete",
    });

    expect(res.status).toBe(200);
    expect(res.body.succeeded).toBe(1);
    expect(res.body.failed).toBe(0);
    expect(res.body.failedIds).toEqual([]);

    const done = await request(api).get("/tasks?status=done");
    expect(done.body.length).toBe(1);
  });

  it("rejects non-string ids", async () => {
    const res = await request(app()).post("/tasks/bulk/action").send({
      ids: ["valid-id", 123, null],
      action: "complete",
    });

    expect(res.status).toBe(400);
    expect(res.body.error).toContain("each id must be a string");
  });
});

describe("TaskStore.list", () => {
  it("returns tasks with the more recent createdAt first", () => {
    const store = new TaskStore();
    store.create("earlier");
    store.create("later");
    const [first, second] = store.list();
    expect(first && second && first.createdAt >= second.createdAt).toBe(true);
  });

  it("filters by status independently of insertion order", () => {
    const store = new TaskStore();
    const keep = store.create("active");
    const done = store.create("done");
    store.update(done.id, { done: true });
    expect(store.list("active").map((t) => t.id)).toEqual([keep.id]);
    expect(store.list("done").map((t) => t.id)).toEqual([done.id]);
  });
});

describe("POST /tasks/reorder", () => {
  it("reorders tasks and returns them in the new order", async () => {
    const api = app();
    const t1 = await request(api).post("/tasks").send({ title: "first" });
    const t2 = await request(api).post("/tasks").send({ title: "second" });
    const t3 = await request(api).post("/tasks").send({ title: "third" });

    const res = await request(api).post("/tasks/reorder").send({
      ids: [t3.body.id, t1.body.id, t2.body.id],
    });

    expect(res.status).toBe(200);
    expect(res.body.success).toBe(true);

    const list = await request(api).get("/tasks");
    expect(list.body.map((t: { title: string }) => t.title)).toEqual(["third", "first", "second"]);
  });

  it("rejects non-array ids", async () => {
    const res = await request(app()).post("/tasks/reorder").send({
      ids: "not-an-array",
    });

    expect(res.status).toBe(400);
    expect(res.body.error).toContain("ids must be an array");
  });

  it("rejects non-string ids", async () => {
    const res = await request(app()).post("/tasks/reorder").send({
      ids: ["valid-id", 123],
    });

    expect(res.status).toBe(400);
    expect(res.body.error).toContain("each id must be a string");
  });

  it("rejects if any id does not exist", async () => {
    const api = app();
    const t1 = await request(api).post("/tasks").send({ title: "exists" });

    const res = await request(api).post("/tasks/reorder").send({
      ids: [t1.body.id, "nonexistent"],
    });

    expect(res.status).toBe(400);
    expect(res.body.error).toContain("one or more task ids not found");
  });
});

describe("Recurring tasks", () => {
  it("creates a task with recurrence and dueDate", async () => {
    const res = await request(app())
      .post("/tasks")
      .send({ title: "Daily standup", recurrence: "daily", dueDate: "2025-01-15" });
    expect(res.status).toBe(201);
    expect(res.body.recurrence).toBe("daily");
    expect(res.body.dueDate).toBe("2025-01-15");
  });

  it("spawns next occurrence when completing a recurring task", async () => {
    const api = app();
    const created = await request(api)
      .post("/tasks")
      .send({ title: "Daily standup", recurrence: "daily", dueDate: "2025-01-15" });
    const taskId = created.body.id;

    await request(api).patch(`/tasks/${taskId}`).send({ done: true });

    const allTasks = await request(api).get("/tasks");
    expect(allTasks.body.length).toBe(2);

    const completedTask = allTasks.body.find((t: { id: string }) => t.id === taskId);
    expect(completedTask.done).toBe(true);

    const nextTask = allTasks.body.find((t: { id: string }) => t.id !== taskId);
    expect(nextTask.title).toBe("Daily standup");
    expect(nextTask.done).toBe(false);
    expect(nextTask.recurrence).toBe("daily");
    expect(nextTask.dueDate).toBe("2025-01-16");
  });

  it("advances weekly recurrence correctly", async () => {
    const api = app();
    const created = await request(api)
      .post("/tasks")
      .send({ title: "Weekly review", recurrence: "weekly", dueDate: "2025-01-15" });
    const taskId = created.body.id;

    await request(api).patch(`/tasks/${taskId}`).send({ done: true });

    const allTasks = await request(api).get("/tasks");
    const nextTask = allTasks.body.find((t: { id: string }) => t.id !== taskId);
    expect(nextTask.dueDate).toBe("2025-01-22");
  });

  it("advances monthly recurrence correctly", async () => {
    const api = app();
    const created = await request(api)
      .post("/tasks")
      .send({ title: "Monthly review", recurrence: "monthly", dueDate: "2025-01-15" });
    const taskId = created.body.id;

    await request(api).patch(`/tasks/${taskId}`).send({ done: true });

    const allTasks = await request(api).get("/tasks");
    const nextTask = allTasks.body.find((t: { id: string }) => t.id !== taskId);
    expect(nextTask.dueDate).toBe("2025-02-15");
  });

  it("does not spawn next occurrence for non-recurring tasks", async () => {
    const api = app();
    const created = await request(api)
      .post("/tasks")
      .send({ title: "One-time task" });
    const taskId = created.body.id;

    await request(api).patch(`/tasks/${taskId}`).send({ done: true });

    const allTasks = await request(api).get("/tasks");
    expect(allTasks.body.length).toBe(1);
    expect(allTasks.body[0].done).toBe(true);
  });

  it("does not spawn next occurrence if task has recurrence but no dueDate", async () => {
    const api = app();
    const created = await request(api)
      .post("/tasks")
      .send({ title: "Incomplete recurring", recurrence: "daily" });
    const taskId = created.body.id;

    await request(api).patch(`/tasks/${taskId}`).send({ done: true });

    const allTasks = await request(api).get("/tasks");
    expect(allTasks.body.length).toBe(1);
    expect(allTasks.body[0].done).toBe(true);
  });

  it("rejects invalid recurrence value", async () => {
    const res = await request(app())
      .post("/tasks")
      .send({ title: "Task", recurrence: "invalid" });
    expect(res.status).toBe(400);
    expect(res.body.error).toContain("recurrence must be one of");
  });

  it("rejects invalid dueDate", async () => {
    const res = await request(app())
      .post("/tasks")
      .send({ title: "Task", dueDate: "not-a-date" });
    expect(res.status).toBe(400);
    expect(res.body.error).toContain("dueDate must be a valid ISO date");
  });

  it("spawns next occurrence in bulk complete action", async () => {
    const api = app();
    const t1 = await request(api)
      .post("/tasks")
      .send({ title: "Recurring task", recurrence: "daily", dueDate: "2025-01-15" });

    const res = await request(api).post("/tasks/bulk/action").send({
      ids: [t1.body.id],
      action: "complete",
    });

    expect(res.status).toBe(200);
    expect(res.body.succeeded).toBe(1);

    const allTasks = await request(api).get("/tasks");
    expect(allTasks.body.length).toBe(2);

    const nextTask = allTasks.body.find((t: { id: string }) => t.id !== t1.body.id);
    expect(nextTask.recurrence).toBe("daily");
    expect(nextTask.dueDate).toBe("2025-01-16");
  });

  it("handles monthly overflow: Jan 31 -> Feb 28", async () => {
    const api = app();
    const created = await request(api)
      .post("/tasks")
      .send({ title: "Monthly task", recurrence: "monthly", dueDate: "2025-01-31" });
    const taskId = created.body.id;

    await request(api).patch(`/tasks/${taskId}`).send({ done: true });

    const allTasks = await request(api).get("/tasks");
    const nextTask = allTasks.body.find((t: { id: string }) => t.id !== taskId);
    expect(nextTask.dueDate).toBe("2025-02-28");
  });

  it("handles monthly overflow in leap year: Jan 31 -> Feb 29", async () => {
    const api = app();
    const created = await request(api)
      .post("/tasks")
      .send({ title: "Monthly task", recurrence: "monthly", dueDate: "2024-01-31" });
    const taskId = created.body.id;

    await request(api).patch(`/tasks/${taskId}`).send({ done: true });

    const allTasks = await request(api).get("/tasks");
    const nextTask = allTasks.body.find((t: { id: string }) => t.id !== taskId);
    expect(nextTask.dueDate).toBe("2024-02-29");
  });

  it("does not spawn on re-completion of already-done recurring task", async () => {
    const api = app();
    const created = await request(api)
      .post("/tasks")
      .send({ title: "Recurring task", recurrence: "daily", dueDate: "2025-01-15" });
    const taskId = created.body.id;

    await request(api).patch(`/tasks/${taskId}`).send({ done: true });
    const countAfterFirst = (await request(api).get("/tasks")).body.length;

    await request(api).patch(`/tasks/${taskId}`).send({ done: true });
    const countAfterSecond = (await request(api).get("/tasks")).body.length;

    expect(countAfterSecond).toBe(countAfterFirst);
  });

  it("does not spawn when PATCH done:true on already-done task with title change", async () => {
    const api = app();
    const created = await request(api)
      .post("/tasks")
      .send({ title: "Recurring task", recurrence: "daily", dueDate: "2025-01-15" });
    const taskId = created.body.id;

    await request(api).patch(`/tasks/${taskId}`).send({ done: true });
    const countAfterFirst = (await request(api).get("/tasks")).body.length;

    await request(api).patch(`/tasks/${taskId}`).send({ title: "Updated title", done: true });
    const countAfterSecond = (await request(api).get("/tasks")).body.length;

    expect(countAfterSecond).toBe(countAfterFirst);
  });

  it("does not spawn on bulk re-complete of already-done recurring task", async () => {
    const api = app();
    const created = await request(api)
      .post("/tasks")
      .send({ title: "Recurring task", recurrence: "daily", dueDate: "2025-01-15" });
    const taskId = created.body.id;

    await request(api).post("/tasks/bulk/action").send({
      ids: [taskId],
      action: "complete",
    });
    const countAfterFirst = (await request(api).get("/tasks")).body.length;

    await request(api).post("/tasks/bulk/action").send({
      ids: [taskId],
      action: "complete",
    });
    const countAfterSecond = (await request(api).get("/tasks")).body.length;

    expect(countAfterSecond).toBe(countAfterFirst);
  });
});
