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
    title: "Leaf monitoring",
    shortLabel: "Leaf",
    defaultDisease: "early_blight",
    severityReady: true,
    explanation:
      "Upload leaf photos over time to track relative severity, visual consistency, weather context, and recovery trend.",
  },
  FRUIT: {
    cropPart: "FRUIT",
    title: "Fruit monitoring",
    shortLabel: "Fruit",
    defaultDisease: "anthracnose",
    severityReady: true,
    explanation:
      "Fruit uses the same observation architecture as leaf: gate validation, relative severity, visual consistency, weather context, and trend.",
  },
};

export const TARGET_OBSERVATIONS = 3;

export const MONITORING_DAY_LABELS = [1, 3, 7] as const;

export const NEXT_OBSERVATION_GUIDANCE =
  "Take the next photo after a few days at the same plant to track how severity changes over time.";
