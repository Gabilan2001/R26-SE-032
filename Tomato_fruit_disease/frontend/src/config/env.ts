import { Platform } from "react-native";

function stripTrailingSlashes(url: string): string {
  return url.replace(/\/+$/, "");
}

/**
 * Backend base URL from `.env`:
 * - Prefer `EXPO_PUBLIC_API_BASE_URL` if set.
 * - On web, prefer localhost so browser can reach uvicorn bound to this PC.
 * - Else `http://EXPO_PUBLIC_API_HOST:EXPO_PUBLIC_API_PORT` (phone / Expo Go).
 * Restart Expo after editing `.env`.
 */
export const API_BASE_URL: string = (() => {
  const explicit = process.env.EXPO_PUBLIC_API_BASE_URL?.trim();
  if (explicit) {
    return stripTrailingSlashes(explicit);
  }

  const port = (process.env.EXPO_PUBLIC_API_PORT ?? "8000").trim();

  // Browser on this PC cannot use a LAN IP if uvicorn is localhost-only,
  // and localhost is the reliable target when running `npm run web`.
  if (Platform.OS === "web") {
    const webHost = (
      process.env.EXPO_PUBLIC_API_HOST_WEB ?? "127.0.0.1"
    ).trim();
    return stripTrailingSlashes(`http://${webHost}:${port}`);
  }

  const host = (process.env.EXPO_PUBLIC_API_HOST ?? "192.168.0.1").trim();
  return stripTrailingSlashes(`http://${host}:${port}`);
})();
