import { Platform } from "react-native";

export type ObservationLocationSelection = {
  latitude?: number;
  longitude?: number;
  area?: string;
  district?: string;
  province?: string;
  source: "gps" | "manual" | "none";
  label?: string;
};

/** Request device GPS coordinates (web geolocation first, then Expo Location). */
export async function requestGpsLocation(): Promise<ObservationLocationSelection | null> {
  if (
    Platform.OS === "web" &&
    typeof navigator !== "undefined" &&
    navigator.geolocation
  ) {
    return new Promise((resolve) => {
      navigator.geolocation.getCurrentPosition(
        (pos) =>
          resolve({
            latitude: pos.coords.latitude,
            longitude: pos.coords.longitude,
            source: "gps",
          }),
        () => resolve(null),
        { enableHighAccuracy: false, timeout: 8000, maximumAge: 60000 }
      );
    });
  }

  try {
    const Location = await import("expo-location");
    const { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== "granted") {
      return null;
    }
    const position = await Location.getCurrentPositionAsync({
      accuracy: Location.Accuracy.Balanced,
    });
    return {
      latitude: position.coords.latitude,
      longitude: position.coords.longitude,
      source: "gps",
    };
  } catch {
    return null;
  }
}

export function formatLocationSummary(
  location: ObservationLocationSelection | null | undefined
): string | null {
  if (!location || location.source === "none") {
    return null;
  }
  const parts = [location.area, location.district, location.province].filter(Boolean);
  if (parts.length > 0) {
    return parts.join(" - ");
  }
  if (location.label) {
    return location.label;
  }
  if (location.latitude != null && location.longitude != null) {
    return `${location.latitude.toFixed(4)}, ${location.longitude.toFixed(4)}`;
  }
  return null;
}

/** Client-side labels for manual pick — mirrors backend /meta/locations. */
export const MANUAL_LOCATION_HINTS: Record<
  string,
  { latitude: number; longitude: number; district: string; province: string }
> = {
  Colombo: { latitude: 6.9271, longitude: 79.8612, district: "Colombo", province: "Western Province" },
  Dambulla: { latitude: 7.86, longitude: 80.65, district: "Matale", province: "Central Province" },
  Kandy: { latitude: 7.2906, longitude: 80.6337, district: "Kandy", province: "Central Province" },
  "Nuwara Eliya": {
    latitude: 6.9708,
    longitude: 80.7736,
    district: "Nuwara Eliya",
    province: "Central Province",
  },
  Galle: { latitude: 6.0329, longitude: 80.216, district: "Galle", province: "Southern Province" },
  Jaffna: { latitude: 9.6615, longitude: 80.0255, district: "Jaffna", province: "Northern Province" },
  Kurunegala: {
    latitude: 7.4806,
    longitude: 80.3621,
    district: "Kurunegala",
    province: "North Western Province",
  },
  Matara: { latitude: 5.9483, longitude: 80.5353, district: "Matara", province: "Southern Province" },
  Badulla: { latitude: 6.9934, longitude: 81.055, district: "Badulla", province: "Uva Province" },
  Anuradhapura: {
    latitude: 8.3114,
    longitude: 80.4037,
    district: "Anuradhapura",
    province: "North Central Province",
  },
  Batticaloa: {
    latitude: 7.7102,
    longitude: 81.6924,
    district: "Batticaloa",
    province: "Eastern Province",
  },
  Ratnapura: {
    latitude: 6.6828,
    longitude: 80.3992,
    district: "Ratnapura",
    province: "Sabaragamuwa Province",
  },
};

export function manualLocationSelection(label: string): ObservationLocationSelection {
  const meta = MANUAL_LOCATION_HINTS[label];
  if (!meta) {
    return { label, area: label, source: "manual" };
  }
  return {
    label,
    area: label,
    district: meta.district,
    province: meta.province,
    latitude: meta.latitude,
    longitude: meta.longitude,
    source: "manual",
  };
}
