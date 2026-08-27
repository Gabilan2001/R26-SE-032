import React from "react";
import { View, Text, StyleSheet } from "react-native";
import type { Observation } from "../../api/observations";
import { palette, severityColors } from "../../theme/colors";
import { formatScore } from "../../utils/observationLabels";

type Props = {
  observations: Observation[];
};

export function ObservationTimeline({ observations }: Props) {
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
          return (
            <React.Fragment key={o.observation_id}>
              {i > 0 ? <Text style={styles.arrow}>→</Text> : null}
              <View style={styles.node}>
                <Text style={styles.nodeLabel}>Obs {i + 1}</Text>
                <Text
                  style={[
                    styles.nodeScore,
                    { color: high ? severityColors.high.main : severityColors.low.main },
                  ]}
                >
                  {formatScore(o.severity_score)}
                </Text>
                <Text style={styles.nodeClass}>{o.severity_class}</Text>
              </View>
            </React.Fragment>
          );
        })}
      </View>
    </View>
  );
}

export function ConsistencySummary({ observations }: Props) {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>Consistency summary</Text>
      {observations.map((o, i) => (
        <Text key={o.observation_id} style={styles.line}>
          Observation {i + 1}:{" "}
          {i === 0 || o.consistency_status === "BASELINE"
            ? "BASELINE"
            : o.consistency_status}
        </Text>
      ))}
    </View>
  );
}

export function WeatherTimeline({ observations }: Props) {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>Weather across observations</Text>
      {observations.map((o, i) => {
        const wx = o.weather_context as
          | { interpretation?: string; details?: Record<string, unknown> }
          | null
          | undefined;
        const line =
          wx?.interpretation ||
          (wx?.details
            ? `T ${String(wx.details.temperature ?? "n/a")}°C · H ${String(
                wx.details.humidity ?? "n/a"
              )}%`
            : "Not attached");
        return (
          <Text key={o.observation_id} style={styles.line}>
            Observation {i + 1}: {line}
          </Text>
        );
      })}
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
  title: { color: palette.textPrimary, fontWeight: "700", marginBottom: 10 },
  empty: { color: palette.textMuted },
  row: { flexDirection: "row", alignItems: "center", flexWrap: "wrap" },
  node: { alignItems: "center", minWidth: 72 },
  nodeLabel: { color: palette.textMuted, fontSize: 11, fontWeight: "600" },
  nodeScore: { fontSize: 16, fontWeight: "800", marginTop: 4 },
  nodeClass: { color: palette.textMuted, fontSize: 11, marginTop: 2 },
  arrow: { color: palette.textMuted, marginHorizontal: 6, fontWeight: "700" },
  line: { color: palette.textMuted, marginTop: 4, lineHeight: 18 },
});
