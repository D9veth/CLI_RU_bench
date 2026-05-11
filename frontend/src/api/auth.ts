import { apiGet, apiPost } from "./client";
import type { TokenPair, User } from "./types";

export const ACCESS_TOKEN_KEY = "llm_bench_access";
export const REFRESH_TOKEN_KEY = "llm_bench_refresh";

export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function saveTokens(tokens: TokenPair) {
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh);
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

export async function loginRequest(username: string, password: string) {
  const tokens = await apiPost<TokenPair>("/api/auth/token/", { username, password });
  saveTokens(tokens);
  return tokens;
}

export async function refreshAccessToken() {
  const refresh = localStorage.getItem(REFRESH_TOKEN_KEY);
  if (!refresh) {
    throw new Error("Refresh token is missing");
  }
  const token = await apiPost<{ access: string }>("/api/auth/token/refresh/", { refresh });
  localStorage.setItem(ACCESS_TOKEN_KEY, token.access);
  return token.access;
}

export function getCurrentUser() {
  return apiGet<User>("/api/auth/me/");
}
