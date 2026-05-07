/**
 * Minimal HTTP client for Quorum ``/api/v1`` — mirrors FastAPI error payloads.
 */

const baseURL = () =>
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "/api/v1";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly body?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function parseDetail(payload: unknown): string {
  if (payload && typeof payload === "object" && "detail" in payload) {
    const d = (payload as { detail: unknown }).detail;
    if (typeof d === "string") return d;
    if (Array.isArray(d) && d[0] && typeof d[0] === "object" && "msg" in d[0]) {
      return String((d[0] as { msg: string }).msg);
    }
  }
  return "Request failed";
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit & { skipAuth?: boolean } = {},
): Promise<T> {
  const { skipAuth, headers: hdr, ...rest } = options;
  const headers = new Headers(hdr);
  if (!headers.has("Content-Type") && rest.body && !(rest.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  if (!skipAuth) {
    const access = localStorage.getItem("quorum_access_token");
    if (access) headers.set("Authorization", `Bearer ${access}`);
  }

  const res = await fetch(`${baseURL()}${path.startsWith("/") ? path : `/${path}`}`, {
    ...rest,
    headers,
  });

  const text = await res.text();
  let json: unknown = undefined;
  if (text) {
    try {
      json = JSON.parse(text);
    } catch {
      json = text;
    }
  }

  if (!res.ok) {
    throw new ApiError(parseDetail(json), res.status, json);
  }

  return json as T;
}
