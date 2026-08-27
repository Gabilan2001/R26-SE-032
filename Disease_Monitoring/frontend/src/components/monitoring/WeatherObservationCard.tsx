import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { palette } from "../../theme/colors";
import { weatherSummary } from "../../utils/observationLabels";

type Props = {
  title?: string;
  weather: Record<string, unknown> | null | undefined;
};

export function WeatherObservationCard({ title = "Weather context", weather }: Props) {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.body}>{weatherSummary(weather)}</Text>
      <Text style={styles.hint}>Contextual only — not treatment advice.</Text>
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
  title: { color: palette.infoText, fontWeight: "700", marginBottom: 4 },
  body: { color: palette.textPrimary, lineHeight: 20 },
  hint: { color: palette.textMuted, fontSize: 11, marginTop: 6 },
});
