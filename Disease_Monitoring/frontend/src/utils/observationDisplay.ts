import type { CropPart, Observation } from "../api/observations";
import { MONITORING_DAY_LABELS } from "../config/modality";

export function severityPercent(obs: Observation): number {
  if (obs.estimated_affected_area_percentage != null) {
    return Number(obs.estimated_affected_area_percentage);
  }
  return Math.round(obs.severity_score * 1000) / 10;
}

export function formatSeverityPercent(obs: Observation): string {
  return `${severityPercent(obs).toFixed(0)}%`;
}

export function monitoringDayLabel(observationNumber: number): string {
  const day = MONITORING_DAY_LABELS[observationNumber - 1];
  return day != null ? `Day ${day}` : `Day ${observationNumber}`;
}

export function severityChangePercent(
  current: Observation,
  previous?: Observation | null
): string | null {
  if (!previous) return null;
  const delta = severityPercent(current) - severityPercent(previous);
  if (Math.abs(delta) < 0.5) return "0%";
  const sign = delta > 0 ? "+" : "";
  return `${sign}${Math.round(delta)}%`;
}

export function imageStatusLabel(cropPart?: CropPart): string {
  return cropPart === "FRUIT" ? "Valid tomato fruit" : "Valid tomato leaf";
}

export function trendHeadline(trend?: string | null): string | null {
  if (!trend || trend === "BASELINE") return null;
  switch (trend) {
    case "IMPROVING":
      return "Improving";
    case "WORSENING":
      return "Worsening";
    case "STABLE":
      return "Stable";
    case "RECOVERED":
      return "Recovered";
    default:
      return String(trend);
  }
}

export function consistencyHeadline(status?: string | null): string {
  switch (status) {
    case "BASELINE":
      return "Baseline observation";
    case "MATCH":
      return "Matches previous photo";
    case "POSSIBLE_MATCH":
      return "Possible match — confirm same plant";
    case "MISMATCH":
      return "Looks different from previous photo";
    default:
      return status ? String(status) : "Not checked";
  }
}

export type MonitoringSummaryView = {
  initial_severity_pct: number;
  peak_severity_pct: number;
  final_severity_pct: number;
  overall_change_pct: number;
  overall_trend: string;
  peak_observation_number: number;
  severity_timeline: string;
  peak_note?: string | null;
  observation_count: number;
};

/** Client fallback when API summary is missing (same rules as backend). */
export function computeOverallSummary(
  observations: Observation[]
): MonitoringSummaryView | null {
  if (observations.length === 0) return null;

  const scores = observations.map((o) => severityPercent(o) / 100);
  const initial = scores[0];
  const final = scores[scores.length - 1];
  const peak = Math.max(...scores);
  const peakIndex = scores.indexOf(peak) + 1;
  const initialPct = Math.round(initial * 1000) / 10;
  const finalPct = Math.round(final * 1000) / 10;
  const peakPct = Math.round(peak * 1000) / 10;
  const overallChange = Math.round((finalPct - initialPct) * 10) / 10;

  let overallTrend = "BASELINE";
  if (scores.length > 1) {
    const delta = final - initial;
    if (final <= 0.25 && final < initial) overallTrend = "RECOVERED";
    else if (delta <= -0.05) overallTrend = "IMPROVING";
    else if (delta >= 0.05) overallTrend = "WORSENING";
    else overallTrend = "STABLE";
  }

  const timeline = observations.map((o) => formatSeverityPercent(o)).join(" → ");
  const peakDay = MONITORING_DAY_LABELS[peakIndex - 1];
  const peakNote =
    peakDay != null
      ? `Highest severity was on Observation ${peakIndex} (Day ${peakDay}): ${Math.round(peakPct)}%.`
      : `Highest severity was on Observation ${peakIndex}: ${Math.round(peakPct)}%.`;

  return {
    initial_severity_pct: initialPct,
    peak_severity_pct: peakPct,
    final_severity_pct: finalPct,
    overall_change_pct: overallChange,
    overall_trend: overallTrend,
    peak_observation_number: peakIndex,
    severity_timeline: timeline,
    peak_note: peakNote,
    observation_count: observations.length,
  };
}

export function formatSignedPercent(value: number): string {
  if (Math.abs(value) < 0.5) return "0%";
  const sign = value > 0 ? "+" : "";
  return `${sign}${Math.round(value)}%`;
}

export type SeverityTrendPoint = {
  observationNumber: number;
  dayLabel: string;
  severityPct: number;
  severityClass: "LOW" | "HIGH";
  isPeak: boolean;
};

export function buildSeverityTrendPoints(
  observations: Observation[],
  peakObservationNumber?: number
): SeverityTrendPoint[] {
  return observations.map((o, i) => {
    const observationNumber = i + 1;
    return {
      observationNumber,
      dayLabel: monitoringDayLabel(observationNumber),
      severityPct: severityPercent(o),
      severityClass: o.severity_class,
      isPeak:
        peakObservationNumber != null && observationNumber === peakObservationNumber,
    };
  });
}
