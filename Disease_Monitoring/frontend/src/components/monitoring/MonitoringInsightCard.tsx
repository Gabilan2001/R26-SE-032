import React from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";
import type { FarmerInsight } from "../../api/observations";
import { palette } from "../../theme/colors";

type Props = {
  insight: FarmerInsight | null;
  loading?: boolean;
};

export function MonitoringInsightCard({ insight, loading }: Props) {
  if (loading) {
    return (
      <View style={styles.card}>
        <Text style={styles.kicker}>MONITORING INSIGHT</Text>
        <ActivityIndicator color={palette.accent} style={styles.spinner} />
      </View>
    );
  }

  if (!insight?.available || !insight.text) return null;

  return (
    <View style={styles.card}>
      <Text style={styles.kicker}>MONITORING INSIGHT</Text>
      <Text style={styles.title}>{insight.title || "Monitoring insight"}</Text>
      <Text style={styles.body}>{insight.text}</Text>
      {insight.disclaimer ? (
        <Text style={styles.disclaimer}>{insight.disclaimer}</Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    marginTop: 12,
    marginBottom: 4,
    backgroundColor: palette.card,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: palette.cardBorder,
    padding: 14,
  },
  kicker: {
    color: palette.textMuted,
    fontSize: 10,
    letterSpacing: 1,
    fontWeight: "700",
  },
  title: {
    color: palette.textPrimary,
    fontWeight: "800",
    fontSize: 16,
    marginTop: 8,
  },
  body: {
    color: palette.textPrimary,
    marginTop: 10,
    lineHeight: 22,
    fontSize: 14,
  },
  disclaimer: {
    color: palette.textMuted,
    fontSize: 11,
    marginTop: 12,
    lineHeight: 16,
  },
  spinner: { marginTop: 12 },
});
