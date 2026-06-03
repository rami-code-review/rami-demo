export interface Task {
  id: string;
  title: string;
  done: boolean;
  createdAt: string;
}

export type TaskStatus = "all" | "active" | "done";

export function isTaskStatus(value: string): value is TaskStatus {
  return value === "all" || value === "active" || value === "done";
}

export class ValidationError extends Error {}

/** Validate and normalize a task title, or throw ValidationError. */
export function normalizeTitle(raw: unknown): string {
  if (typeof raw !== "string") {
    throw new ValidationError("title must be a string");
  }
  const title = raw.trim();
  if (title.length === 0) {
    throw new ValidationError("title must not be empty");
  }
  if (title.length > 200) {
    throw new ValidationError("title must be at most 200 characters");
  }
  return title;
}
