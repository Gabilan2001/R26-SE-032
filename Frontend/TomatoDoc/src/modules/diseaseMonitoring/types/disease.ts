import type { SeverityBand } from "../theme/colors";

export type DayKey = "d1" | "d3" | "d7";

export type DiseaseTrack = {
  id: string;
  name: string;
  /** Mask / U-Net infected area estimate */
  infectedPercent: number;
  /** Discrete severity from model */
  severityBand: SeverityBand;
  /** 0–100 score driving the semicircular gauge */
  severityScore: number;
  /** Monitoring band (legacy demo type; active UI uses observation API) */
  monitoringBand: SeverityBand;
  /** Per-day overrides (optional): same disease, different timepoints */
  daySnapshots?: Partial<
    Record<
      DayKey,
      { infectedPercent: number; severityBand: SeverityBand; severityScore: number }
    >
  >;
};
