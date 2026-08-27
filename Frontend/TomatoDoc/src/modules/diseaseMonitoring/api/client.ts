import { API_BASE_URL } from "../config/env";

/** Absolute URL for a backend path (leading slash optional). */
export function apiUrl(path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE_URL}${p}`;
}
