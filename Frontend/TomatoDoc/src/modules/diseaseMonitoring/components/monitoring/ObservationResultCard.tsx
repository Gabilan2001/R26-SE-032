import React, { useMemo } from "react";
import { View, Text, StyleSheet, Image } from "react-native";
import type { CropPart, Observation } from "../../api/observations";
import { severityColors, type MonitoringPalette } from "../../theme/colors";
import { useMonitoringPalette } from "../../theme/MonitoringThemeContext";
import {
  formatSeverityPercent,
  imageStatusLabel,
  monitoringDayLabel,
  severityChangePercent,
  trendHeadline,
} from "../../utils/observationDisplay";
import { ConsistencyStatusCard } from "./ConsistencyStatusCard";
import { LocationObservationCard } from "./LocationObservationCard";
import { WeatherObservationCard } from "./WeatherObservationCard";

type Props = {
  observationNumber: number;
  observation: Observation;
  previousObservation?: Observation | null;
  cropPart?: CropPart;
  imageUri?: string | null;
};

export function ObservationResultCard({
  observationNumber,
  observation,
  previousObservation,
  cropPart,
  imageUri,
}: Props) {
  const high = observation.severity_class === "HIGH";
  const p = useMonitoringPalette();
  const styles = useMemo(() => makeStyles(p), [p]);
  const change = severityChangePercent(observation, previousObservation);
  const trend = trendHeadline(observation.trend);
  const isBaseline = observationNumber === 1 || observation.consistency_status === "BASELINE";

  return (
    <View>
      <View style={styles.heroCard}>
        <Text style={styles.kicker}>OBSERVATION {observationNumber}</Text>
        <Text style={styles.dayLabel}>{monitoringDayLabel(observationNumber)}</Text>
        <Text style={styles.dateLabel}>
          {new Date(observation.created_at).toLocaleDateString(undefined, {
            weekday: "short",
            year: "numeric",
            month: "short",
            day: "numeric",
          })}
        </Text>

        {imageUri ? (
          <Image source={{ uri: imageUri }} style={styles.image} resizeMode="cover" />
        ) : (
          <View style={styles.imagePlaceholder}>
            <Text style={styles.placeholderText}>Photo saved</Text>
          </View>
        )}

        <View style={styles.severityBlock}>
          <Text style={styles.sectionLabel}>Severity</Text>
          <Text style={styles.severityValue}>{formatSeverityPercent(observation)}</Text>
          <View
            style={[
              styles.severityBadge,
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
              {observation.severity_class}
            </Text>
          </View>
          {!isBaseline && change ? (
            <View style={styles.changeRow}>
              <Text style={styles.changeLabel}>Change</Text>
              <Text
                style={[
                  styles.changeValue,
                  change.startsWith("+")
                    ? styles.changeUp
                    : change.startsWith("-")
                      ? styles.changeDown
                      : null,
                ]}
              >
                {change}
              </Text>
            </View>
          ) : null}
          {!isBaseline && trend ? (
            <View style={styles.changeRow}>
              <Text style={styles.changeLabel}>Trend</Text>
              <Text style={styles.trendValue}>{trend}</Text>
            </View>
          ) : null}
          {isBaseline ? (
            <Text style={styles.baselineHint}>First observation — baseline for this case.</Text>
          ) : null}
        </View>
      </View>

      <View style={styles.statusCard}>
        <Text style={styles.sectionLabel}>Image status</Text>
        <Text style={styles.statusOk}>✓ {imageStatusLabel(cropPart ?? observation.crop_part)}</Text>
      </View>

      <ConsistencyStatusCard
        status={observation.consistency_status}
        similarity={observation.similarity_score}
        showSimilarity={false}
      />

      <LocationObservationCard location={observation.location} />
      <WeatherObservationCard weather={observation.weather_context} />
    </View>
  );
}

function makeStyles(p: MonitoringPalette) {
  return StyleSheet.create({
    heroCard: {
      backgroundColor: p.card,
      borderRadius: 16,
      borderWidth: 1,
      borderColor: p.cardBorder,
      padding: 16,
    },
    kicker: {
      color: p.textMuted,
      fontSize: 11,
      letterSpacing: 1.2,
      fontWeight: "700",
    },
    dayLabel: {
      color: p.textPrimary,
      fontSize: 22,
      fontWeight: "800",
      marginTop: 4,
    },
    dateLabel: { color: p.textMuted, marginTop: 4 },
    image: {
      width: "100%",
      height: 200,
      borderRadius: 12,
      marginTop: 14,
      backgroundColor: p.bgElevated,
    },
    imagePlaceholder: {
      height: 120,
      marginTop: 14,
      borderRadius: 12,
      alignItems: "center",
      justifyContent: "center",
      backgroundColor: p.bgElevated,
    },
    placeholderText: { color: p.textMuted },
    severityBlock: { marginTop: 16 },
    sectionLabel: {
      color: p.textMuted,
      fontSize: 12,
      fontWeight: "700",
      letterSpacing: 0.6,
      textTransform: "uppercase",
    },
    severityValue: {
      color: p.textPrimary,
      fontSize: 42,
      fontWeight: "800",
      marginTop: 4,
    },
    severityBadge: {
      alignSelf: "flex-start",
      marginTop: 8,
      paddingHorizontal: 12,
      paddingVertical: 6,
      borderRadius: 999,
    },
    changeRow: {
      flexDirection: "row",
      alignItems: "center",
      gap: 10,
      marginTop: 10,
    },
    changeLabel: { color: p.textMuted, fontWeight: "600", width: 64 },
    changeValue: { color: p.textPrimary, fontWeight: "800", fontSize: 18 },
    changeUp: { color: severityColors.high.main },
    changeDown: { color: severityColors.low.main },
    trendValue: { color: p.infoText, fontWeight: "800", fontSize: 16 },
    baselineHint: { color: p.textMuted, marginTop: 10, lineHeight: 18 },
    statusCard: {
      marginTop: 12,
      backgroundColor: p.card,
      borderRadius: 14,
      borderWidth: 1,
      borderColor: p.cardBorder,
      padding: 14,
    },
    statusOk: { color: p.accent, fontWeight: "700", marginTop: 6, fontSize: 15 },
  });
}
