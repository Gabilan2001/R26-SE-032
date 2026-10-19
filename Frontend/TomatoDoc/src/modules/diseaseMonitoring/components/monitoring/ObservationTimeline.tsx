import React, { useMemo } from "react";
import { View, Text, StyleSheet } from "react-native";
import type { Observation } from "../../api/observations";
import { severityColors, type MonitoringPalette } from "../../theme/colors";
import { useMonitoringPalette } from "../../theme/MonitoringThemeContext";
import {
  consistencyHeadline,
  formatSeverityPercent,
  monitoringDayLabel,
} from "../../utils/observationDisplay";
import { weatherSummary } from "../../utils/weatherDisplay";

type Props = {
  observations: Observation[];
  peakObservationNumber?: number;
};

export function ObservationTimeline({ observations, peakObservationNumber }: Props) {
  const p = useMonitoringPalette();
  const styles = useMemo(() => makeStyles(p), [p]);

  if (observations.length === 0) {
    return (
      <View style={styles.card}>
        <Text style={styles.empty}>No observations yet</Text>
      </View>
    );
  }

  return (
    <View style={styles.card}>
      <Text style={styles.title}>Severity progression</Text>
      <View style={styles.row}>
        {observations.map((o, i) => {
          const high = o.severity_class === "HIGH";
          const obsNum = i + 1;
          const isPeak =
            peakObservationNumber != null && obsNum === peakObservationNumber;
          return (
            <React.Fragment key={o.observation_id}>
              {i > 0 ? <Text style={styles.arrow}>→</Text> : null}
              <View
                style={[
                  styles.node,
                  isPeak && { borderColor: p.accent, backgroundColor: p.accentDim },
                ]}
              >
                <Text style={styles.nodeLabel}>Obs {obsNum}</Text>
                <Text style={styles.nodeDay}>{monitoringDayLabel(obsNum)}</Text>
                <Text
                  style={[
                    styles.nodeScore,
                    { color: high ? severityColors.high.main : severityColors.low.main },
                  ]}
                >
                  {formatSeverityPercent(o)}
                </Text>
                {isPeak ? <Text style={styles.peakBadge}>Peak</Text> : null}
              </View>
            </React.Fragment>
          );
        })}
      </View>
    </View>
  );
}

export function ConsistencySummary({ observations }: Props) {
  const p = useMonitoringPalette();
  const styles = useMemo(() => makeStyles(p), [p]);

  return (
    <View style={styles.card}>
      <Text style={styles.title}>Consistency summary</Text>
      {observations.map((o, i) => (
        <Text key={o.observation_id} style={styles.line}>
          Observation {i + 1}: {consistencyHeadline(o.consistency_status)}
        </Text>
      ))}
    </View>
  );
}

export function WeatherTimeline({ observations }: Props) {
  const p = useMonitoringPalette();
  const styles = useMemo(() => makeStyles(p), [p]);

  return (
    <View style={styles.card}>
      <Text style={styles.title}>Weather across observations</Text>
      {observations.map((o, i) => (
        <Text key={o.observation_id} style={styles.line}>
          Observation {i + 1}: {weatherSummary(o.weather_context)}
        </Text>
      ))}
      <Text style={styles.hint}>
        Weather is environmental context only and does not determine disease severity.
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
    title: { color: p.textPrimary, fontWeight: "700", marginBottom: 10 },
    empty: { color: p.textMuted },
    row: { flexDirection: "row", alignItems: "center", flexWrap: "wrap" },
    node: {
      alignItems: "center",
      minWidth: 76,
      borderRadius: 10,
      borderWidth: 1,
      borderColor: p.cardBorder,
      paddingVertical: 8,
      paddingHorizontal: 6,
    },
    nodeLabel: { color: p.textMuted, fontSize: 11, fontWeight: "600" },
    nodeDay: { color: p.textMuted, fontSize: 10, marginTop: 2 },
    nodeScore: { fontSize: 18, fontWeight: "800", marginTop: 4 },
    peakBadge: {
      color: p.accent,
      fontSize: 10,
      fontWeight: "800",
      marginTop: 4,
      textTransform: "uppercase",
    },
    arrow: { color: p.textMuted, marginHorizontal: 6, fontWeight: "700" },
    line: { color: p.textMuted, marginTop: 4, lineHeight: 18 },
    hint: { color: p.textMuted, fontSize: 11, marginTop: 10, lineHeight: 16 },
  });
}
