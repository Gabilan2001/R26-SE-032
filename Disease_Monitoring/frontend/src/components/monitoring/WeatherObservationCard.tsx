import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { palette } from "../../theme/colors";
import {
  parseWeatherContext,
  weatherMetrics,
} from "../../utils/weatherDisplay";

type Props = {
  title?: string;
  weather: Record<string, unknown> | null | undefined;
};

export function WeatherObservationCard({ title = "Current weather", weather }: Props) {
  const parsed = parseWeatherContext(weather);
  const unavailable = !parsed || parsed.available === false;
  const metrics = unavailable ? [] : weatherMetrics(weather);

  return (
    <View style={styles.card}>
      <Text style={styles.title}>{title}</Text>
      {unavailable ? (
        <Text style={styles.body}>
          {parsed?.interpretation || "Weather data unavailable"}
        </Text>
      ) : (
        <>
          <View style={styles.grid}>
            {metrics.map((m) => (
              <View key={m.label} style={styles.metric}>
                <Text style={styles.metricLabel}>{m.label}</Text>
                <Text style={styles.metricValue}>{m.value}</Text>
              </View>
            ))}
          </View>
          {parsed?.environmental_conditions ? (
            <View style={styles.envBox}>
              <Text style={styles.envLabel}>Environmental conditions</Text>
              <Text style={styles.envValue}>{parsed.environmental_conditions}</Text>
            </View>
          ) : null}
          {parsed?.interpretation ? (
            <Text style={styles.body}>{parsed.interpretation}</Text>
          ) : null}
        </>
      )}
      <Text style={styles.hint}>
        {parsed?.disclaimer ||
          "Weather is environmental context only and does not determine disease severity."}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    marginTop: 12,
    backgroundColor: palette.infoBanner,
    borderRadius: 14,
    padding: 14,
  },
  title: { color: palette.infoText, fontWeight: "700", marginBottom: 8 },
  body: { color: palette.textPrimary, lineHeight: 20 },
  grid: { flexDirection: "row", flexWrap: "wrap", gap: 10 },
  metric: { width: "30%", minWidth: 90, marginBottom: 6 },
  metricLabel: { color: palette.textMuted, fontSize: 11, fontWeight: "600" },
  metricValue: { color: palette.textPrimary, fontSize: 16, fontWeight: "800", marginTop: 2 },
  envBox: { marginTop: 10, marginBottom: 6 },
  envLabel: { color: palette.textMuted, fontSize: 11, fontWeight: "700" },
  envValue: { color: palette.infoText, fontWeight: "800", marginTop: 2, fontSize: 15 },
  hint: { color: palette.textMuted, fontSize: 11, marginTop: 8, lineHeight: 16 },
});
