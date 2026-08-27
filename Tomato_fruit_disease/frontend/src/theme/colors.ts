export const palette = {
  bg: "#06120c",
  bgElevated: "#0c1f14",
  card: "#102818",
  cardBorder: "#1a3d2a",
  textPrimary: "#f4fdf7",
  textMuted: "#7a9a86",
  accent: "#3dff7a",
  accentDim: "#1a5c32",
  divider: "#1e3d2a",
  infoBanner: "#0f1a2e",
  infoText: "#7ec8ff",
  trackLine: "#2a4a38",
} as const;

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
