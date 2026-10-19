import React, { useMemo } from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";
import type { FarmerInsight } from "../../api/observations";
import { type MonitoringPalette } from "../../theme/colors";
import { useMonitoringPalette } from "../../theme/MonitoringThemeContext";

type Props = {
  insight: FarmerInsight | null;
  loading?: boolean;
};

export function MonitoringInsightCard({ insight, loading }: Props) {
  const p = useMonitoringPalette();
  const styles = useMemo(() => makeStyles(p), [p]);

  if (loading) {
    return (
      <View style={styles.card}>
        <Text style={styles.kicker}>MONITORING INSIGHT</Text>
        <ActivityIndicator color={p.accent} style={styles.spinner} />
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

function makeStyles(p: MonitoringPalette) {
  return StyleSheet.create({
    card: {
      marginTop: 12,
      marginBottom: 4,
      backgroundColor: p.card,
      borderRadius: 14,
      borderWidth: 1,
      borderColor: p.cardBorder,
      padding: 14,
    },
    kicker: {
      color: p.textMuted,
      fontSize: 10,
      letterSpacing: 1,
      fontWeight: "700",
    },
    title: {
      color: p.textPrimary,
      fontWeight: "800",
      fontSize: 16,
      marginTop: 8,
    },
    body: {
      color: p.textPrimary,
      marginTop: 10,
      lineHeight: 22,
      fontSize: 14,
    },
    disclaimer: {
      color: p.textMuted,
      fontSize: 11,
      marginTop: 12,
      lineHeight: 16,
    },
    spinner: { marginTop: 12 },
  });
}
