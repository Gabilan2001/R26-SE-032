import type { SeverityBand } from "../theme/colors";

/** Map a 0–100 U-Net / fusion score to discrete severity for UI colors. */
export function severityBandFromScore(score: number): SeverityBand {
  if (score >= 66) return "high";
  if (score >= 33) return "medium";
  return "low";
}
