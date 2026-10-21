import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { SemicircularSeverityGauge } from "../SemicircularSeverityGauge";
import { palette, severityColors } from "../../theme/colors";
import { formatScore } from "../../utils/observationLabels";

type Props = {
  severityClass: string;
  severityScore: number;
};

export function SeverityResultCard({ severityClass, severityScore }: Props) {
  const high = severityClass === "HIGH";
  const band = high ? "high" : "low";
  const color = high ? severityColors.high.main : severityColors.low.main;

  return (
    <View style={styles.card}>
      <Text style={styles.label}>Severity</Text>
      <Text style={[styles.band, { color }]}>{severityClass}</Text>
      <SemicircularSeverityGauge
        score={Math.round(severityScore * 100)}
        band={band}
        size={180}
      />
      <Text style={styles.score}>
        Estimated affected area: {formatScore(severityScore)}
      </Text>
      <Text style={styles.hint}>
        Visual estimate from the image (≤30% LOW, &gt;30% HIGH) - not expert-validated severity.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: palette.card,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: palette.cardBorder,
    padding: 16,
    alignItems: "center",
    marginTop: 12,
  },
  label: { color: palette.textMuted, fontSize: 12, fontWeight: "600", alignSelf: "flex-start" },
  band: { fontSize: 28, fontWeight: "800", marginTop: 4, alignSelf: "flex-start" },
  score: { color: palette.textPrimary, fontWeight: "600", marginTop: 4 },
  hint: { color: palette.textMuted, fontSize: 11, marginTop: 6, textAlign: "center" },
});
