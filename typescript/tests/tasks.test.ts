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
});

describe("GET /tasks", () => {
  it("lists tasks newest first", async () => {
    const api = app();
    await request(api).post("/tasks").send({ title: "first" });
    await request(api).post("/tasks").send({ title: "second" });
    const res = await request(api).get("/tasks");
    expect(res.status).toBe(200);
    expect(res.body.map((t: { title: string }) => t.title)).toEqual(["second", "first"]);
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
