import React from "react";
import { View, Text, StyleSheet, Image } from "react-native";
import type { Observation } from "../../api/observations";
import { palette, severityColors } from "../../theme/colors";
import { formatScore, weatherSummary } from "../../utils/observationLabels";

type Props = {
  index: number;
  observation: Observation;
  imageUri?: string | null;
};

export function OverallMonitoringCard({ index, observation, imageUri }: Props) {
  const high = observation.severity_class === "HIGH";
  const isBaseline = index === 0 || observation.consistency_status === "BASELINE";

  return (
    <View style={styles.card}>
      <Text style={styles.title}>
        OBSERVATION {index + 1}
        {isBaseline ? " · BASELINE" : ""}
      </Text>
      {imageUri ? (
        <Image source={{ uri: imageUri }} style={styles.image} resizeMode="cover" />
      ) : (
        <View style={styles.ph}>
          <Text style={styles.phText}>No local preview</Text>
        </View>
      )}
      <Text style={styles.meta}>{new Date(observation.created_at).toLocaleString()}</Text>
      <Text
        style={[
          styles.severity,
          { color: high ? severityColors.high.main : severityColors.low.main },
        ]}
      >
        Severity {observation.severity_class} · {formatScore(observation.severity_score)}
      </Text>
      <Text style={styles.meta}>Weather: {weatherSummary(observation.weather_context)}</Text>
      <Text style={styles.consistency}>
        {isBaseline ? "BASELINE" : observation.consistency_status}
        {observation.similarity_score != null
          ? ` · similarity ${formatScore(observation.similarity_score)}`
          : ""}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: palette.card,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: palette.cardBorder,
    padding: 14,
    marginTop: 12,
  },
  title: { color: palette.textPrimary, fontWeight: "800", letterSpacing: 0.4 },
  image: {
    width: "100%",
    height: 140,
    borderRadius: 10,
    marginTop: 10,
    backgroundColor: palette.bgElevated,
  },
  ph: {
    height: 80,
    marginTop: 10,
    borderRadius: 10,
    backgroundColor: palette.bgElevated,
    alignItems: "center",
    justifyContent: "center",
  },
  phText: { color: palette.textMuted },
  meta: { color: palette.textMuted, marginTop: 6, lineHeight: 18 },
  severity: { marginTop: 6, fontWeight: "700" },
  consistency: { color: palette.infoText, marginTop: 6, fontWeight: "600" },
});
