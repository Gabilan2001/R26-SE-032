import React, { useMemo } from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";
import type { ImageQualityResult, QualityCheckStatus } from "../../api/imageQuality";
import { severityColors, type MonitoringPalette } from "../../theme/colors";
import { useMonitoringPalette } from "../../theme/MonitoringThemeContext";

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

function statusMeta(status: QualityCheckStatus, p: MonitoringPalette) {
  switch (status) {
    case "pass":
      return { icon: "✓", color: p.accent, label: "Good" };
    case "warn":
      return { icon: "!", color: severityColors.medium.main, label: "Check" };
    case "fail":
      return { icon: "✕", color: severityColors.high.main, label: "Retake" };
  }
}

export function ImageQualityCard({ result, loading, skipped }: Props) {
  const p = useMonitoringPalette();
  const styles = useMemo(() => makeStyles(p), [p]);

  if (loading) {
    return (
      <View style={styles.card}>
        <Text style={styles.title}>Checking photo quality…</Text>
        <ActivityIndicator color={p.accent} style={styles.spinner} />
      </View>
    );
  }

  if (skipped) {
    return (
      <View style={styles.card}>
        <Text style={styles.title}>Photo quality check</Text>
        <Text style={styles.skipped}>
          Could not run quality check — you can still upload.
        </Text>
      </View>
    );
  }

  if (!result) return null;

  const overallColor =
    result.overall === "good"
      ? p.accent
      : result.overall === "fair"
        ? severityColors.medium.main
        : severityColors.high.main;

  return (
    <View style={styles.card}>
      <Text style={styles.kicker}>PHOTO QUALITY CHECK</Text>
      <Text style={[styles.summary, { color: overallColor }]}>{result.farmer_summary}</Text>

      {ROWS.map(({ key, label }) => {
        const check = result.checks[key];
        const meta = statusMeta(check.status, p);
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
        Tips only — upload is still allowed. The gate will validate crop type on upload.
      </Text>
    </View>
  );
}

function makeStyles(p: MonitoringPalette) {
  return StyleSheet.create({
    card: {
      marginTop: 12,
      backgroundColor: p.card,
      borderRadius: 14,
      borderWidth: 1,
      borderColor: p.cardBorder,
      padding: 14,
    },
    kicker: {
      color: p.textMuted,
      fontSize: 10,
      letterSpacing: 1,
      fontWeight: "700",
    },
    title: { color: p.textPrimary, fontWeight: "700", fontSize: 14 },
    summary: { fontWeight: "700", marginTop: 8, lineHeight: 20 },
    spinner: { marginTop: 12 },
    skipped: { color: p.textMuted, marginTop: 8, lineHeight: 18 },
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
    rowLabel: { color: p.textPrimary, fontWeight: "700", fontSize: 13 },
    rowMessage: { color: p.textMuted, marginTop: 3, lineHeight: 17, fontSize: 12 },
    footer: { color: p.textMuted, fontSize: 11, marginTop: 12, lineHeight: 16 },
  });
}
