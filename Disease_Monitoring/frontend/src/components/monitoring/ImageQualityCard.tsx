import React from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";
import type { ImageQualityResult, QualityCheckStatus } from "../../api/imageQuality";
import { palette, severityColors } from "../../theme/colors";

type Props = {
  result: ImageQualityResult | null;
  loading?: boolean;
  skipped?: boolean;
};

const ROWS: Array<{ key: keyof ImageQualityResult["checks"]; label: string }> = [
  { key: "blur", label: "Sharpness" },
  { key: "brightness", label: "Lighting" },
  { key: "distance", label: "Distance" },
];

function statusMeta(status: QualityCheckStatus) {
  switch (status) {
    case "pass":
      return { icon: "✓", color: palette.accent, label: "Good" };
    case "warn":
      return { icon: "!", color: severityColors.medium.main, label: "Check" };
    case "fail":
      return { icon: "✕", color: severityColors.high.main, label: "Retake" };
  }
}

export function ImageQualityCard({ result, loading, skipped }: Props) {
  if (loading) {
    return (
      <View style={styles.card}>
        <Text style={styles.title}>Checking photo quality…</Text>
        <ActivityIndicator color={palette.accent} style={styles.spinner} />
      </View>
    );
  }

  if (skipped) {
    return (
      <View style={styles.card}>
        <Text style={styles.title}>Photo quality check</Text>
        <Text style={styles.skipped}>
          Could not run quality check - you can still upload.
        </Text>
      </View>
    );
  }

  if (!result) return null;

  const overallColor =
    result.overall === "good"
      ? palette.accent
      : result.overall === "fair"
        ? severityColors.medium.main
        : severityColors.high.main;

  return (
    <View style={styles.card}>
      <Text style={styles.kicker}>PHOTO QUALITY CHECK</Text>
      <Text style={[styles.summary, { color: overallColor }]}>{result.farmer_summary}</Text>

      {ROWS.map(({ key, label }) => {
        const check = result.checks[key];
        const meta = statusMeta(check.status);
        return (
          <View key={key} style={styles.row}>
            <View style={[styles.badge, { borderColor: meta.color }]}>
              <Text style={[styles.badgeIcon, { color: meta.color }]}>{meta.icon}</Text>
            </View>
            <View style={styles.rowBody}>
              <Text style={styles.rowLabel}>
                {label} · <Text style={{ color: meta.color }}>{meta.label}</Text>
              </Text>
              <Text style={styles.rowMessage}>{check.message}</Text>
            </View>
          </View>
        );
      })}

      <Text style={styles.footer}>
        Tips only - upload is still allowed. The gate will validate crop type on upload.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    marginTop: 12,
    backgroundColor: palette.card,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: palette.cardBorder,
    padding: 14,
  },
  kicker: {
    color: palette.textMuted,
    fontSize: 10,
    letterSpacing: 1,
    fontWeight: "700",
  },
  title: { color: palette.textPrimary, fontWeight: "700", fontSize: 14 },
  summary: { fontWeight: "700", marginTop: 8, lineHeight: 20 },
  spinner: { marginTop: 12 },
  skipped: { color: palette.textMuted, marginTop: 8, lineHeight: 18 },
  row: {
    flexDirection: "row",
    alignItems: "flex-start",
    marginTop: 12,
    gap: 10,
  },
  badge: {
    width: 28,
    height: 28,
    borderRadius: 14,
    borderWidth: 1.5,
    alignItems: "center",
    justifyContent: "center",
  },
  badgeIcon: { fontWeight: "800", fontSize: 14 },
  rowBody: { flex: 1 },
  rowLabel: { color: palette.textPrimary, fontWeight: "700", fontSize: 13 },
  rowMessage: { color: palette.textMuted, marginTop: 3, lineHeight: 17, fontSize: 12 },
  footer: { color: palette.textMuted, fontSize: 11, marginTop: 12, lineHeight: 16 },
});
