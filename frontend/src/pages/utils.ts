import { ApiError } from "../api/client";

export function formatMetric(value: number | null | undefined, digits = 3) {
  return value === null || value === undefined ? "—" : value.toFixed(digits);
}

export function formatLatencySeconds(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "—";
  }
  const seconds = value / 1000;
  return `${seconds.toFixed(2)} с`;
}

export function formatInteger(value: number | null | undefined) {
  return value === null || value === undefined ? "—" : value.toLocaleString("ru-RU");
}

export function formatBytes(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "—";
  }
  if (value < 1024) {
    return `${value} Б`;
  }
  const units = ["КБ", "МБ", "ГБ"];
  let current = value / 1024;
  let index = 0;
  while (current >= 1024 && index < units.length - 1) {
    current /= 1024;
    index += 1;
  }
  return `${current.toFixed(current >= 10 ? 1 : 2)} ${units[index]}`;
}

export function formatDate(value: string | null | undefined) {
  if (!value) {
    return "—";
  }
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function errorMessage(error: unknown) {
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Неизвестная ошибка";
}

export function toQuery(params: object) {
  const search = new URLSearchParams();
  Object.entries(params as Record<string, string | number | null | undefined>).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== "") {
      search.set(key, String(value));
    }
  });
  const query = search.toString();
  return query ? `?${query}` : "";
}

export function safeJsonParse(value: string) {
  if (!value.trim()) {
    return {};
  }
  return JSON.parse(value) as Record<string, unknown>;
}
