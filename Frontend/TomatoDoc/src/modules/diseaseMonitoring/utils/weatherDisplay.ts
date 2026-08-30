export type WeatherDetails = {
  temperature?: number;
  humidity?: number;
  rainfall?: number;
  rainfall_1h?: number;
  wind_speed_kmh?: number;
  wind_speed?: number;
  dew_point?: number;
  cloud_cover?: number;
  visibility_km?: number;
  vpd_kpa?: number;
  description?: string;
};

export type WeatherContext = {
  available?: boolean;
  reason?: string;
  interpretation?: string;
  disclaimer?: string;
  environmental_conditions?: string;
  details?: WeatherDetails;
  city?: string;
  used_default_location?: boolean;
};

function rainMm(details?: WeatherDetails): number | undefined {
  if (!details) return undefined;
  if (details.rainfall != null) return Number(details.rainfall);
  if (details.rainfall_1h != null) return Number(details.rainfall_1h);
  return undefined;
}

function windKmh(details?: WeatherDetails): number | undefined {
  if (!details) return undefined;
  if (details.wind_speed_kmh != null) return Number(details.wind_speed_kmh);
  if (details.wind_speed != null) return Number(details.wind_speed) * 3.6;
  return undefined;
}

function fmt(n: number | undefined, digits = 0): string {
  if (n == null || Number.isNaN(n)) return "n/a";
  return n.toFixed(digits);
}

export function parseWeatherContext(
  wx: Record<string, unknown> | null | undefined
): WeatherContext | null {
  if (!wx) return null;
  return wx as WeatherContext;
}

export function weatherSummary(
  wx: Record<string, unknown> | null | undefined
): string {
  const parsed = parseWeatherContext(wx);
  if (!parsed) return "Weather not attached";
  if (parsed.available === false) {
    const reason = String(parsed.reason ?? "").toLowerCase();
    if (reason.includes("location") || reason.includes("coordinate")) {
      return "No location — weather not retrieved.";
    }
    if (reason.includes("api") || reason.includes("key") || reason.includes("fail")) {
      return "Weather temporarily unavailable.";
    }
    return parsed.interpretation || "Weather temporarily unavailable.";
  }
  const d = parsed.details;
  const defaultNote = parsed.used_default_location ? " (Colombo default)" : "";
  if (d && (d.temperature != null || d.humidity != null)) {
    return `Temp ${fmt(d.temperature, 0)}°C · Humidity ${fmt(d.humidity, 0)}% · Rain ${fmt(
      rainMm(d),
      1
    )} mm${defaultNote}`;
  }
  if (typeof parsed.interpretation === "string" && parsed.interpretation) {
    return parsed.interpretation;
  }
  return "Weather context recorded";
}

export function weatherMetrics(wx: Record<string, unknown> | null | undefined) {
  const parsed = parseWeatherContext(wx);
  const d = parsed?.details;
  return [
    { label: "Temperature", value: d?.temperature != null ? `${fmt(d.temperature, 0)}°C` : "n/a" },
    { label: "Humidity", value: d?.humidity != null ? `${fmt(d.humidity, 0)}%` : "n/a" },
    { label: "Rain", value: rainMm(d) != null ? `${fmt(rainMm(d), 1)} mm` : "n/a" },
    { label: "Wind", value: windKmh(d) != null ? `${fmt(windKmh(d), 0)} km/h` : "n/a" },
    { label: "Dew point", value: d?.dew_point != null ? `${fmt(d.dew_point, 0)}°C` : "n/a" },
    { label: "Clouds", value: d?.cloud_cover != null ? `${fmt(d.cloud_cover, 0)}%` : "n/a" },
  ];
}
