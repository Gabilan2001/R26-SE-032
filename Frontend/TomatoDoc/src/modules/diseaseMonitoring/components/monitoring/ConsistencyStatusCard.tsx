import React, { useMemo } from "react";
import { View, Text, StyleSheet } from "react-native";
import { severityColors, type MonitoringPalette } from "../../theme/colors";
import { useMonitoringPalette } from "../../theme/MonitoringThemeContext";
import {
  consistencyFarmerHint,
  consistencyFarmerTitle,
  formatScore,
} from "../../utils/observationLabels";

type Props = {
  status: string;
  similarity?: number | null;
  showSimilarity?: boolean;
  compact?: boolean;
};

function tone(status: string, p: MonitoringPalette) {
  if (status === "MATCH" || status === "BASELINE") {
    return { border: p.accent, bg: p.accentDim, text: p.accent };
  }
  if (status === "POSSIBLE_MATCH") {
    return {
      border: severityColors.medium.main,
      bg: severityColors.medium.badgeBg,
      text: severityColors.medium.main,
    };
  }
  if (status === "MISMATCH") {
    return {
      border: severityColors.high.main,
      bg: severityColors.high.badgeBg,
      text: severityColors.high.main,
    };
  }
  return { border: p.cardBorder, bg: p.bgElevated, text: p.textMuted };
}

export function ConsistencyStatusCard({
  status,
  similarity,
  showSimilarity = false,
  compact = false,
}: Props) {
  const p = useMonitoringPalette();
  const t = tone(status, p);
  const styles = useMemo(() => makeStyles(p, compact), [p, compact]);
  const icon =
    status === "MATCH" || status === "BASELINE"
      ? "✓"
      : status === "POSSIBLE_MATCH"
        ? "!"
        : status === "MISMATCH"
          ? "✕"
          : "·";

  return (
    <View
      style={[
        styles.card,
        compact
          ? styles.cardCompact
          : { borderColor: t.border, backgroundColor: t.bg },
      ]}
    >
      <View style={styles.row}>
        <View style={[styles.icon, { borderColor: t.border }]}>
          <Text style={{ color: t.text, fontWeight: "800" }}>{icon}</Text>
        </View>
        <View style={{ flex: 1 }}>
          <Text style={[styles.title, { color: t.text }]}>
            {consistencyFarmerTitle(status)}
          </Text>
          {showSimilarity && similarity != null ? (
            <Text style={styles.meta}>Similarity score: {formatScore(similarity)}</Text>
          ) : null}
        </View>
      </View>
      <Text style={styles.hint}>{consistencyFarmerHint(status)}</Text>
    </View>
  );
}

function makeStyles(p: MonitoringPalette, compact: boolean) {
  return StyleSheet.create({
    card: {
      borderRadius: 14,
      borderWidth: 1,
      padding: 14,
      marginTop: 12,
    },
    cardCompact: {
      borderWidth: 0,
      padding: 0,
      marginTop: 8,
      backgroundColor: "transparent",
    },
    row: { flexDirection: "row", gap: 10, alignItems: "center" },
    icon: {
      width: 32,
      height: 32,
      borderRadius: 16,
      borderWidth: 1.5,
      alignItems: "center",
      justifyContent: "center",
      backgroundColor: p.bg,
    },
    title: { fontWeight: "700", fontSize: 14 },
    meta: { color: p.textMuted, marginTop: 2, fontSize: 12 },
    hint: { color: p.textMuted, marginTop: 8, lineHeight: 18, fontSize: 12 },
  });
}
