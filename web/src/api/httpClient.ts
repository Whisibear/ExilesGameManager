export const UNAUTHORIZED_EVENT = "auth:unauthorized";

function formatApiDetail(detail: unknown): string | null {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const messages = detail
      .map((entry) => {
        if (typeof entry === "string") return entry;
        if (entry && typeof entry === "object") {
          const item = entry as { msg?: unknown; loc?: unknown[] };
          const location = Array.isArray(item.loc) ? item.loc.filter((part) => part !== "body").join(".") : "";
          const message = typeof item.msg === "string" ? item.msg : JSON.stringify(entry);
          return location ? `${location}: ${message}` : message;
        }
        return String(entry);
      })
      .filter(Boolean);
    return messages.length ? messages.join("; ") : null;
  }
  if (detail && typeof detail === "object") {
    try {
      return JSON.stringify(detail);
    } catch {
      return null;
    }
  }
  return detail == null ? null : String(detail);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    credentials: "include",
    ...init,
  });

  // Auth endpoints legitimately return 401 for "wrong password" - only
  // treat 401s from the rest of the app as "your session died, log in again".
  if (res.status === 401 && !path.startsWith("/api/auth/")) {
    window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
  }

  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      const detail = formatApiDetail(body?.detail);
      if (detail) message = detail;
    } catch {
      // response had no JSON body - keep the generic message
    }
    throw new Error(message);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

async function requestForm<T>(path: string, formData: FormData): Promise<T> {
  // No Content-Type header here on purpose - the browser sets the correct
  // multipart boundary itself when given a FormData body.
  const res = await fetch(path, { method: "POST", credentials: "include", body: formData });

  if (res.status === 401) {
    window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
  }

  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      const detail = formatApiDetail(body?.detail);
      if (detail) message = detail;
    } catch {
      // response had no JSON body - keep the generic message
    }
    throw new Error(message);
  }

  return (await res.json()) as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PATCH", body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
  postForm: <T>(path: string, formData: FormData) => requestForm<T>(path, formData),
};
