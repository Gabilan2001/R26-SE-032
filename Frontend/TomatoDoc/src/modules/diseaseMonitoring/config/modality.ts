import type { CropPart } from "../api/observations";

/** Demo weather coords (Colombo) — contextual only. */
export const DEMO_WEATHER_COORDS = {
  latitude: 6.9271,
  longitude: 79.8612,
  label: "Colombo (demo)",
} as const;

export type ModalityConfig = {
  cropPart: CropPart;
  title: string;
  shortLabel: string;
  /** Required by API; disease ID is external — default only, not detection. */
  defaultDisease: string;
  severityReady: boolean;
  pendingMessage?: string;
  explanation: string;
};

export const MODALITY: Record<CropPart, ModalityConfig> = {
  LEAF: {
    cropPart: "LEAF",
    title: "Disease in Tomato Leaf",
    shortLabel: "Tomato Leaf",
    defaultDisease: "early_blight",
    severityReady: true,
    explanation:
      "Upload tomato leaf photos over time to track relative severity, visual consistency, weather context, and recovery trend.",
  },
  FRUIT: {
    cropPart: "FRUIT",
    title: "Disease in Tomato Fruit",
    shortLabel: "Tomato Fruit",
    defaultDisease: "anthracnose",
    severityReady: true,
    explanation:
      "Upload tomato fruit photos over time: gate validation, relative severity, visual consistency, weather context, and trend.",
  },
};

export const TARGET_OBSERVATIONS = 3;

/** Illustrative monitoring-day labels for Obs 1 → 3 (not computed from calendar dates). */
export const MONITORING_DAY_LABELS = [1, 3, 7] as const;

export const NEXT_OBSERVATION_GUIDANCE =
  "Take the next photo after a few days at the same plant to track how severity changes over time.";
