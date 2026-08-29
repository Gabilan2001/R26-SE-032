/** Farmer-facing copy for observation monitoring (not clinical claims). */

export function formatDiseaseName(name: string): string {
  return name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function formatScore(n: number | null | undefined): string {
  if (n == null || Number.isNaN(n)) return "n/a";
  return n.toFixed(2);
}

export function trendFarmerLabel(trend: string | null | undefined): string {
  switch (trend) {
    case "BASELINE":
      return "Baseline (first observation)";
    case "STABLE":
      return "Stable — similar to last observation";
    case "IMPROVING":
      return "Improving — severity lower than last time";
    case "WORSENING":
      return "Worsening — severity higher than last time";
    case "RECOVERED":
      return "Recovered — low severity after improvement";
    default:
      return trend ? String(trend) : "n/a";
  }
}

export function consistencyFarmerTitle(status: string | null | undefined): string {
  switch (status) {
    case "BASELINE":
      return "First observation (baseline)";
    case "MATCH":
      return "Visual consistency: MATCH";
    case "POSSIBLE_MATCH":
      return "Visual consistency: POSSIBLE MATCH";
    case "MISMATCH":
      return "Visual consistency: MISMATCH";
    default:
      return status ? `Visual consistency: ${status}` : "Visual consistency";
  }
}

export function consistencyFarmerHint(status: string | null | undefined): string {
  switch (status) {
    case "BASELINE":
      return "This photo is the reference for future checks on this monitoring case.";
    case "MATCH":
      return "Looks visually consistent with the previous observation. This does not prove it is the same plant.";
    case "POSSIBLE_MATCH":
      return "Somewhat similar to the previous photo. Confirm only if this is the same monitoring case.";
    case "MISMATCH":
      return "Looks visually different from previous photos. Prefer a new monitoring case, or confirm only if you are sure it belongs here.";
    default:
      return "Visual consistency with previous observation — not plant identity confirmation.";
  }
}

export function recoveryHeadline(trend: string | null | undefined): string {
  switch (trend) {
    case "RECOVERED":
      return "Recovery trend detected";
    case "IMPROVING":
      return "Condition is improving";
    case "STABLE":
      return "Condition remains stable";
    case "WORSENING":
      return "Condition is worsening";
    case "BASELINE":
      return "Baseline established";
    default:
      return "Monitoring in progress";
  }
}

export function recoveryTone(
  trend: string | null | undefined
): "success" | "positive" | "neutral" | "warning" {
  switch (trend) {
    case "RECOVERED":
      return "success";
    case "IMPROVING":
      return "positive";
    case "WORSENING":
      return "warning";
    default:
      return "neutral";
  }
}

export function weatherSummary(
  wx: Record<string, unknown> | null | undefined
): string {
  if (!wx) return "Weather not attached";
  if (wx.available === false) {
    return typeof wx.interpretation === "string"
      ? wx.interpretation
      : "Weather data unavailable";
  }
  const details = wx.details as
    | {
        temperature?: number;
        humidity?: number;
        rainfall?: number;
        rainfall_1h?: number;
      }
    | undefined;
  if (details && (details.temperature != null || details.humidity != null)) {
    const rain = details.rainfall ?? details.rainfall_1h ?? "n/a";
    return `Temp ${details.temperature ?? "n/a"}°C · Humidity ${
      details.humidity ?? "n/a"
    }% · Rain ${rain} mm`;
  }
  if (typeof wx.interpretation === "string" && wx.interpretation) {
    return wx.interpretation;
  }
  return "Weather context recorded";
}
