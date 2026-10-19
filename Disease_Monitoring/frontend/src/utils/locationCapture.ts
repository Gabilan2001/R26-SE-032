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

export type GpsFailureReason =
  | "unavailable"
  | "permission_denied"
  | "insecure_context"
  | "timeout"
  | "position_unavailable";

export type GpsRequestResult =
  | { success: true; location: ObservationLocationSelection }
  | { success: false; reason: GpsFailureReason };

const GPS_OPTIONS: PositionOptions = {
  enableHighAccuracy: false,
  timeout: 12000,
  maximumAge: 60000,
};

export function isGeolocationUsable(): boolean {
  if (Platform.OS !== "web") {
    return true;
  }
  if (typeof window === "undefined") {
    return false;
  }
  if (!window.isSecureContext) {
    return false;
  }
  return typeof navigator !== "undefined" && !!navigator.geolocation;
}

function mapGeolocationError(error: GeolocationPositionError): GpsFailureReason {
  switch (error.code) {
    case error.PERMISSION_DENIED:
      return "permission_denied";
    case error.TIMEOUT:
      return "timeout";
    case error.POSITION_UNAVAILABLE:
      return "position_unavailable";
    default:
      return "unavailable";
  }
}

function requestWebGps(): Promise<GpsRequestResult> {
  if (!isGeolocationUsable()) {
    return Promise.resolve({ success: false, reason: "insecure_context" });
  }
  return new Promise((resolve) => {
    navigator.geolocation.getCurrentPosition(
      (pos) =>
        resolve({
          success: true,
          location: {
            latitude: pos.coords.latitude,
            longitude: pos.coords.longitude,
            source: "gps",
          },
        }),
      (err) => resolve({ success: false, reason: mapGeolocationError(err) }),
      GPS_OPTIONS
    );
  });
}

export async function requestGpsLocation(): Promise<GpsRequestResult> {
  if (Platform.OS === "web") {
    return requestWebGps();
  }

  try {
    const Location = await import("expo-location");
    const { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== "granted") {
      return { success: false, reason: "permission_denied" };
    }
    const position = await Location.getCurrentPositionAsync({
      accuracy: Location.Accuracy.Balanced,
    });
    return {
      success: true,
      location: {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        source: "gps",
      },
    };
  } catch {
    return { success: false, reason: "unavailable" };
  }
}

export function gpsFailureMessage(
  reason: GpsFailureReason,
  attachWeather: boolean
): string {
  switch (reason) {
    case "insecure_context":
      return "GPS needs https or localhost. Pick an area manually or use Colombo default.";
    case "permission_denied":
      return "Location permission blocked. Allow it in browser settings, or pick an area manually.";
    case "timeout":
      return "GPS timed out. Try again, pick an area manually, or use Colombo default.";
    case "position_unavailable":
      return "GPS signal not found. Pick an area manually or use Colombo default.";
    default:
      return attachWeather
        ? "GPS not available. Pick an area manually or use Colombo default for weather."
        : "GPS not available. Pick an area manually.";
  }
}

export function hasUserSelectedLocation(
  location: ObservationLocationSelection | null | undefined
): boolean {
  return !!(
    location &&
    location.source !== "none" &&
    (location.latitude != null || location.label || location.area)
  );
}

function dedupeParts(parts: string[]): string[] {
  return parts.filter((part, index) => index === 0 || part !== parts[index - 1]);
}

export function formatLocationSummary(
  location: ObservationLocationSelection | null | undefined
): string | null {
  if (!hasUserSelectedLocation(location)) {
    return null;
  }
  const parts = dedupeParts(
    [location!.area, location!.district, location!.province].filter(Boolean) as string[]
  );
  if (parts.length > 0) {
    return parts.join(" · ");
  }
  if (location!.label) {
    return location!.label;
  }
  if (location!.latitude != null && location!.longitude != null) {
    return `${location!.latitude.toFixed(4)}, ${location!.longitude.toFixed(4)}`;
  }
  return null;
}

export function formatLocationNotice(
  location: ObservationLocationSelection | null | undefined
): string | null {
  const summary = formatLocationSummary(location);
  if (!summary) {
    return null;
  }
  return `Location on - ${summary}`;
}

export function formatLocationContextLine(
  location: ObservationLocationSelection | null | undefined
): { available: boolean; text: string } {
  const summary = formatLocationSummary(location);
  if (!summary) {
    return {
      available: false,
      text: "Location is not available. Enable location or select an area manually.",
    };
  }
  const sourceLabel =
    location!.source === "gps"
      ? "From device GPS"
      : location!.source === "manual"
        ? "Selected manually"
        : "Selected";
  return {
    available: true,
    text: `${summary} (${sourceLabel})`,
  };
}

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
