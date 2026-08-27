import type { SeverityBand } from "../theme/colors";

export function bandLabel(b: SeverityBand): string {
  if (b === "high") return "HIGH RISK";
  if (b === "medium") return "MODERATE";
  return "LOW RISK";
}

export function monitoringLabel(b: SeverityBand): string {
  if (b === "high") return "Monitoring: High";
  if (b === "medium") return "Monitoring: Medium";
  return "Monitoring: Low";
}
