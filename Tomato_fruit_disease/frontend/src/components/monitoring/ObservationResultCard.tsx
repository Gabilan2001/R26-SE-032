import React from "react";
import { View, Text, StyleSheet, Image } from "react-native";
import type { Observation } from "../../api/observations";
import { palette, severityColors } from "../../theme/colors";
import { formatScore } from "../../utils/observationLabels";
import { ConsistencyStatusCard } from "./ConsistencyStatusCard";
import { SeverityResultCard } from "./SeverityResultCard";
import { WeatherObservationCard } from "./WeatherObservationCard";

type Props = {
  caseId: string;
  observationNumber: number;
  observation: Observation;
  imageUri?: string | null;
};

export function ObservationResultCard({
  caseId,
  observationNumber,
  observation,
  imageUri,
}: Props) {
  const high = observation.severity_class === "HIGH";

  return (
    <View>
      <View style={styles.headerCard}>
        <Text style={styles.kicker}>OBSERVATION {observationNumber} RESULT</Text>
        <Text style={styles.caseId}>Case ID: {caseId}</Text>
        <Text style={styles.meta}>
          {new Date(observation.created_at).toLocaleString()}
        </Text>
        {imageUri ? (
          <Image source={{ uri: imageUri }} style={styles.image} resizeMode="cover" />
        ) : (
          <View style={styles.imagePlaceholder}>
            <Text style={styles.placeholderText}>Image preview unavailable</Text>
          </View>
        )}
        <View style={styles.badgeRow}>
          <View
            style={[
              styles.badge,
              {
                backgroundColor: high
                  ? severityColors.high.badgeBg
                  : severityColors.low.badgeBg,
              },
            ]}
          >
            <Text
              style={{
                color: high ? severityColors.high.main : severityColors.low.main,
                fontWeight: "800",
              }}
            >
              {observation.severity_class} · {formatScore(observation.severity_score)}
            </Text>
          </View>
        </View>
      </View>

      <SeverityResultCard
        severityClass={observation.severity_class}
        severityScore={observation.severity_score}
      />

      <ConsistencyStatusCard
        status={observation.consistency_status}
        similarity={observation.similarity_score}
      />

      <WeatherObservationCard weather={observation.weather_context} />
    </View>
  );
}

const styles = StyleSheet.create({
  headerCard: {
    backgroundColor: palette.card,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: palette.cardBorder,
    padding: 16,
  },
  kicker: {
    color: palette.textMuted,
    fontSize: 11,
    letterSpacing: 1.1,
    fontWeight: "700",
  },
  caseId: { color: palette.infoText, fontWeight: "700", marginTop: 6 },
  meta: { color: palette.textMuted, marginTop: 4 },
  image: {
    width: "100%",
    height: 200,
    borderRadius: 12,
    marginTop: 12,
    backgroundColor: palette.bgElevated,
  },
  imagePlaceholder: {
    height: 100,
    marginTop: 12,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: palette.bgElevated,
  },
  placeholderText: { color: palette.textMuted },
  badgeRow: { flexDirection: "row", marginTop: 12 },
  badge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 999,
  },
});
