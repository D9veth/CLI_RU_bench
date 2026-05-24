import type { CompareResponse } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const ACCESS_TOKEN_KEY = "llm_bench_access";
const REFRESH_TOKEN_KEY = "llm_bench_refresh";

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
  return requestWithAuth<T>(method, path, body, true);
}

async function requestWithAuth<T>(method: string, path: string, body: Body | undefined, allowRefresh: boolean): Promise<T> {
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
    if (response.status === 401 && allowRefresh && !path.includes("/api/auth/token/")) {
      try {
        await refreshAccessTokenInternal();
        return requestWithAuth<T>(method, path, body, false);
      } catch {
        localStorage.removeItem(ACCESS_TOKEN_KEY);
        localStorage.removeItem(REFRESH_TOKEN_KEY);
      }
    }
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
    if (response.status === 401) {
      await refreshAccessTokenInternal();
      return requestBlob(path);
    }
    throw new ApiError(response.status, await response.text(), "Ошибка запроса к API");
  }
  return response.blob();
}

async function refreshAccessTokenInternal() {
  const refresh = localStorage.getItem(REFRESH_TOKEN_KEY);
  if (!refresh) {
    throw new Error("Refresh token is missing");
  }
  const response = await fetch(`${API_BASE_URL}/api/auth/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });
  if (!response.ok) {
    throw new Error("Refresh token failed");
  }
  const data = (await response.json()) as { access: string };
  localStorage.setItem(ACCESS_TOKEN_KEY, data.access);
  return data.access;
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

export function getCompareRuns(runA: number, runB: number) {
  return apiGet<CompareResponse>(`/api/compare/runs/?run_a=${runA}&run_b=${runB}`);
}

export function getCompareExportUrl(runA: number, runB: number) {
  return `${API_BASE_URL}/api/compare/runs/export.csv?run_a=${runA}&run_b=${runB}`;
}
