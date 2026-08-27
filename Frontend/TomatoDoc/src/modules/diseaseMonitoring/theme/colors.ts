/** TomatoDoc-aligned palettes for Disease Monitoring (theme only). */

export type MonitoringPalette = {
  bg: string;
  bgElevated: string;
  card: string;
  cardBorder: string;
  textPrimary: string;
  textMuted: string;
  accent: string;
  accentDim: string;
  accentBorder: string;
  divider: string;
  infoBanner: string;
  infoText: string;
  trackLine: string;
  /** Dark text on lime primary buttons (TomatoDoc style). */
  onAccent: string;
};

/** Hub / choose Leaf|Fruit — matches TomatoDoc Home (#5). */
export const hubPalette: MonitoringPalette = {
  bg: "#0f0f0f",
  bgElevated: "#1a1a1a",
  card: "#1a1a1a",
  cardBorder: "rgba(255,255,255,0.07)",
  textPrimary: "#f0f0f0",
  textMuted: "#666666",
  accent: "#c8f135",
  accentDim: "rgba(200,241,53,0.10)",
  accentBorder: "rgba(200,241,53,0.22)",
  divider: "rgba(255,255,255,0.07)",
  infoBanner: "#0f1a2e",
  infoText: "#7ec8ff",
  trackLine: "#2a2a2a",
  onAccent: "#0f0f0f",
};

/** Leaf flow — matches Leaf Scanner / Nutrient lime theme. */
export const leafPalette: MonitoringPalette = {
  bg: "#0f0f0f",
  bgElevated: "#1a1a1a",
  card: "#1a1a1a",
  cardBorder: "rgba(255,255,255,0.07)",
  textPrimary: "#f0f0f0",
  textMuted: "#666666",
  accent: "#c8f135",
  accentDim: "rgba(200,241,53,0.10)",
  accentBorder: "rgba(200,241,53,0.22)",
  divider: "rgba(255,255,255,0.07)",
  infoBanner: "#0f1a00",
  infoText: "#c8f135",
  trackLine: "#2a2a2a",
  onAccent: "#0f0f0f",
};

/** Fruit flow — matches Tomato Fruit Disease Scan coral/red theme. */
export const fruitPalette: MonitoringPalette = {
  bg: "#0f0f0f",
  bgElevated: "#1a1a1a",
  card: "#1a1a1a",
  cardBorder: "rgba(255,255,255,0.07)",
  textPrimary: "#f0f0f0",
  textMuted: "#666666",
  accent: "#ff5c5c",
  accentDim: "rgba(255,92,92,0.08)",
  accentBorder: "rgba(255,92,92,0.20)",
  divider: "rgba(255,255,255,0.07)",
  infoBanner: "#2a1012",
  infoText: "#ff5c5c",
  trackLine: "#2a2a2a",
  onAccent: "#ffffff",
};

/** Default export used by unused/legacy screens — TomatoDoc hub. */
export const palette = hubPalette;

export function paletteFor(
  cropPart?: "LEAF" | "FRUIT" | null
): MonitoringPalette {
  if (cropPart === "LEAF") return leafPalette;
  if (cropPart === "FRUIT") return fruitPalette;
  return hubPalette;
}

export const severityColors = {
  high: {
    main: "#FF6B6B",
    muted: "#3d1518",
    badgeText: "#FF6B6B",
    badgeBg: "#2a1012",
  },
  medium: {
    main: "#FFB347",
    muted: "#3d2e10",
    badgeText: "#FFB347",
    badgeBg: "#2a2210",
  },
  low: {
    main: "#4ADE80",
    muted: "#103d22",
    badgeText: "#4ADE80",
    badgeBg: "#0f2418",
  },
} as const;

export type SeverityBand = keyof typeof severityColors;
