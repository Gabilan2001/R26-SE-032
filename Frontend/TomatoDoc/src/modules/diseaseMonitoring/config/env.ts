import { Platform } from "react-native";

function stripTrailingSlashes(url: string): string {
  return url.replace(/\/+$/, "");
}

/**
 * Disease Monitoring API (FastAPI :8000).
 * Uses MONITORING-specific env keys so TomatoDoc nutrient :5000 is not overridden.
 *
 * Prefer EXPO_PUBLIC_MONITORING_API_BASE_URL, else host/port below.
 */
export const API_BASE_URL: string = (() => {
  const explicit = process.env.EXPO_PUBLIC_MONITORING_API_BASE_URL?.trim();
  if (explicit) {
    return stripTrailingSlashes(explicit);
  }

  const port = (process.env.EXPO_PUBLIC_MONITORING_API_PORT ?? "8000").trim();

  if (Platform.OS === "web") {
    const webHost = (
      process.env.EXPO_PUBLIC_MONITORING_API_HOST_WEB ?? "127.0.0.1"
    ).trim();
    return stripTrailingSlashes(`http://${webHost}:${port}`);
  }

  const host = (
    process.env.EXPO_PUBLIC_MONITORING_API_HOST ??
    process.env.EXPO_PUBLIC_FRUIT_API_HOST ??
    "192.168.243.127"
  ).trim();
  return stripTrailingSlashes(`http://${host}:${port}`);
})();
