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

/** Hub / choose Leaf|Fruit: shared TomatoDoc light theme (see src/theme). */
export const hubPalette: MonitoringPalette = {
  bg: "#FBFAF5",
  bgElevated: "#F3F5EE",
  card: "#FFFFFF",
  cardBorder: "#E3E8DF",
  textPrimary: "#1E3027",
  textMuted: "#5E6E64",
  accent: "#1F6044",
  accentDim: "#EDF6DF",
  accentBorder: "#CFE3B8",
  divider: "#E3E8DF",
  infoBanner: "#EDF6DF",
  infoText: "#12382B",
  trackLine: "#E3E8DF",
  onAccent: "#FFFFFF",
};

/** Leaf flow: same green theme as the hub. */
export const leafPalette: MonitoringPalette = {
  ...hubPalette,
};

/** Fruit flow: tomato-red accent on the same light surfaces. */
export const fruitPalette: MonitoringPalette = {
  ...hubPalette,
  accent: "#E34A3B",
  accentDim: "#FDEDEA",
  accentBorder: "#F5C5BF",
  infoBanner: "#FDEDEA",
  infoText: "#C9362C",
  onAccent: "#FFFFFF",
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
    main: "#D64545",
    muted: "#F8D6D3",
    badgeText: "#B83232",
    badgeBg: "#FDECEA",
  },
  medium: {
    main: "#D98A1B",
    muted: "#F4E2B8",
    badgeText: "#9A6410",
    badgeBg: "#FBF1DA",
  },
  low: {
    main: "#2F8F4E",
    muted: "#CBE8D3",
    badgeText: "#1F6B38",
    badgeBg: "#E4F4E8",
  },
} as const;

export type SeverityBand = keyof typeof severityColors;
