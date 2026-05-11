const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const ACCESS_TOKEN_KEY = "llm_bench_access";

export class ApiError extends Error {
  status: number;
  data: unknown;
  isAuthError: boolean;

  constructor(status: number, data: unknown, message: string) {
    super(message);
    this.status = status;
    this.data = data;
    this.isAuthError = status === 401;
  }
}

type Body = Record<string, unknown> | unknown[] | FormData | undefined;

export function getApiBaseUrl() {
  return API_BASE_URL;
}

async function request<T>(method: string, path: string, body?: Body): Promise<T> {
  const headers = new Headers();
  const token = localStorage.getItem(ACCESS_TOKEN_KEY);
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  const init: RequestInit = { method, headers };
  if (body !== undefined) {
    if (body instanceof FormData) {
      init.body = body;
    } else {
      headers.set("Content-Type", "application/json");
      init.body = JSON.stringify(body);
    }
  }

  const response = await fetch(`${API_BASE_URL}${path}`, init);
  const contentType = response.headers.get("content-type") ?? "";
  const data = contentType.includes("application/json") ? await response.json() : await response.text();

  if (!response.ok) {
    const message =
      typeof data === "object" && data !== null && "detail" in data
        ? String((data as { detail: unknown }).detail)
        : "Ошибка запроса к API";
    throw new ApiError(response.status, data, message);
  }

  return data as T;
}

async function requestBlob(path: string): Promise<Blob> {
  const headers = new Headers();
  const token = localStorage.getItem(ACCESS_TOKEN_KEY);
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, { method: "GET", headers });
  if (!response.ok) {
    throw new ApiError(response.status, await response.text(), "Ошибка запроса к API");
  }
  return response.blob();
}

export function apiGet<T>(path: string) {
  return request<T>("GET", path);
}

export function apiPost<T>(path: string, body?: Body) {
  return request<T>("POST", path, body);
}

export function apiPatch<T>(path: string, body?: Body) {
  return request<T>("PATCH", path, body);
}

export function apiDelete<T>(path: string) {
  return request<T>("DELETE", path);
}

export function apiGetBlob(path: string) {
  return requestBlob(path);
}
