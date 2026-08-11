export type Recurrence = "daily" | "weekly" | "monthly";

export interface Task {
  id: string;
  title: string;
  done: boolean;
  createdAt: string;
  tags?: string[];
  recurrence?: Recurrence;
  dueDate?: string;
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

/** Validate and normalize tags, or throw ValidationError. */
export function normalizeTags(raw: unknown): string[] {
  if (raw === undefined || raw === null) {
    return [];
  }
  if (!Array.isArray(raw)) {
    throw new ValidationError("tags must be an array");
  }
  const normalized = new Set<string>();
  for (const tag of raw) {
    if (typeof tag !== "string") {
      throw new ValidationError("each tag must be a string");
    }
    const trimmed = tag.trim();
    if (trimmed.length > 0) {
      normalized.add(trimmed);
    }
  }
  return Array.from(normalized);
}

/** Validate and normalize recurrence, or throw ValidationError. */
export function normalizeRecurrence(raw: unknown): Recurrence | undefined {
  if (raw === undefined || raw === null) {
    return undefined;
  }
  if (typeof raw !== "string") {
    throw new ValidationError("recurrence must be a string");
  }
  if (raw !== "daily" && raw !== "weekly" && raw !== "monthly") {
    throw new ValidationError("recurrence must be one of: daily, weekly, monthly");
  }
  return raw;
}

/** Validate and normalize a due date, or throw ValidationError. */
export function normalizeDueDate(raw: unknown): string | undefined {
  if (raw === undefined || raw === null) {
    return undefined;
  }
  if (typeof raw !== "string") {
    throw new ValidationError("dueDate must be a string");
  }
  const date = new Date(raw);
  if (isNaN(date.getTime())) {
    throw new ValidationError("dueDate must be a valid ISO date");
  }
  return date.toISOString().split("T")[0];
}

/** Calculate the next due date by advancing by the recurrence interval. */
export function getNextDueDate(dueDate: string, recurrence: Recurrence): string {
  const date = new Date(dueDate + "T00:00:00Z");

  if (recurrence === "daily") {
    date.setUTCDate(date.getUTCDate() + 1);
  } else if (recurrence === "weekly") {
    date.setUTCDate(date.getUTCDate() + 7);
  } else if (recurrence === "monthly") {
    date.setUTCMonth(date.getUTCMonth() + 1);
  }

  const result = date.toISOString().split("T")[0];
  return result as string;
}
