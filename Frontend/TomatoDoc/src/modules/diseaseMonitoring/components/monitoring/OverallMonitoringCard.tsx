import React from "react";
import { View, Text, StyleSheet, Image } from "react-native";
import type { Observation } from "../../api/observations";
import { palette, severityColors } from "../../theme/colors";
import { weatherSummary } from "../../utils/observationLabels";
import {
  consistencyHeadline,
  formatSeverityPercent,
  monitoringDayLabel,
  trendHeadline,
} from "../../utils/observationDisplay";

type Props = {
  index: number;
  observation: Observation;
  imageUri?: string | null;
};

export function OverallMonitoringCard({
  index,
  observation,
  imageUri,
}: Props) {
  const high = observation.severity_class === "HIGH";
  const isBaseline = index === 0 || observation.consistency_status === "BASELINE";
  const trend = trendHeadline(observation.trend);

  return (
    <View style={styles.card}>
      <Text style={styles.title}>OBSERVATION {index + 1}</Text>
      <Text style={styles.day}>{monitoringDayLabel(index + 1)}</Text>
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
        {formatSeverityPercent(observation)} · {observation.severity_class}
      </Text>
      {!isBaseline && trend ? (
        <Text style={styles.trend}>Trend: {trend}</Text>
      ) : null}
      <Text style={styles.meta}>Weather: {weatherSummary(observation.weather_context)}</Text>
      <Text style={styles.consistency}>
        {consistencyHeadline(observation.consistency_status)}
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
  day: { color: palette.textMuted, marginTop: 2, fontWeight: "600" },
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
  severity: { marginTop: 6, fontWeight: "700", fontSize: 16 },
  trend: { color: palette.infoText, marginTop: 4, fontWeight: "700" },
  consistency: { color: palette.infoText, marginTop: 6, fontWeight: "600" },
});
