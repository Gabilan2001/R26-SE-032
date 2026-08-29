import { apiUrl } from "./client";

export async function fetchKnownLocations(): Promise<string[]> {
  const res = await fetch(apiUrl("/meta/locations"));
  if (!res.ok) {
    throw new Error("Could not load location list.");
  }
  const body = (await res.json()) as { locations?: string[] };
  return body.locations ?? [];
}
