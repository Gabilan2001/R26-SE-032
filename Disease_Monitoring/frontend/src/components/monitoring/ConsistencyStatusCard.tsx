import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { palette, severityColors } from "../../theme/colors";
import {
  consistencyFarmerHint,
  consistencyFarmerTitle,
  formatScore,
} from "../../utils/observationLabels";

type Props = {
  status: string;
  similarity?: number | null;
  showSimilarity?: boolean;
};

function tone(status: string) {
  if (status === "MATCH" || status === "BASELINE") {
    return { border: palette.accent, bg: palette.accentDim, text: palette.accent };
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
  return { border: palette.cardBorder, bg: palette.bgElevated, text: palette.textMuted };
}

export function ConsistencyStatusCard({
  status,
  similarity,
  showSimilarity = false,
}: Props) {
  const t = tone(status);
  const icon =
    status === "MATCH" || status === "BASELINE"
      ? "✓"
      : status === "POSSIBLE_MATCH"
        ? "!"
        : status === "MISMATCH"
          ? "✕"
          : "·";

  return (
    <View style={[styles.card, { borderColor: t.border, backgroundColor: t.bg }]}>
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

const styles = StyleSheet.create({
  card: {
    borderRadius: 14,
    borderWidth: 1,
    padding: 14,
    marginTop: 12,
  },
  row: { flexDirection: "row", gap: 10, alignItems: "center" },
  icon: {
    width: 32,
    height: 32,
    borderRadius: 16,
    borderWidth: 1.5,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: palette.bg,
  },
  title: { fontWeight: "700", fontSize: 14 },
  meta: { color: palette.textMuted, marginTop: 2, fontSize: 12 },
  hint: { color: palette.textMuted, marginTop: 8, lineHeight: 18, fontSize: 12 },
});
