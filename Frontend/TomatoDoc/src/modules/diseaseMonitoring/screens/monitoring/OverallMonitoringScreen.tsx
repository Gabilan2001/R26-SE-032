import React, { useMemo } from "react";
import {
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { StatusBar } from "expo-status-bar";
import type { CaseStatus, CropPart, Observation } from "../../api/observations";
import { LeafScanAppHeader } from "../../components/LeafScanAppHeader";
import {
  ConsistencySummary,
  ObservationProgress,
  ObservationTimeline,
  OverallMonitoringCard,
  RecoveryStatusCard,
  WeatherTimeline,
} from "../../components/monitoring";
import { MODALITY } from "../../config/modality";
import { useMonitoringPalette } from "../../theme/MonitoringThemeContext";
import type { MonitoringPalette } from "../../theme/colors";

type Props = {
  cropPart: CropPart;
  caseId: string;
  status: CaseStatus | null;
  observations: Observation[];
  imageUris: Record<string, string>;
  onRestart: () => void;
  onExit?: () => void;
};

export function OverallMonitoringScreen({
  cropPart,
  caseId,
  status,
  observations,
  imageUris,
  onRestart,
  onExit,
}: Props) {
  const cfg = MODALITY[cropPart];
  const first = observations[0];
  const last = observations[observations.length - 1];
  const period =
    first && last
      ? `${new Date(first.created_at).toLocaleDateString()} → ${new Date(
          last.created_at
        ).toLocaleDateString()}`
      : "n/a";

  const trend = status?.overall_status ?? last?.trend ?? null;
  const p = useMonitoringPalette();
  const styles = useMemo(() => makeStyles(p), [p]);

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar style="light" />
      <LeafScanAppHeader
        title="Overall Monitoring"
        badge={cfg.shortLabel.toUpperCase()}
        onBack={onExit}
      />
      <ScrollView contentContainerStyle={styles.content}>
        <ObservationProgress current={3} overview />
        <Text style={styles.title}>Overall Monitoring</Text>

        <View style={styles.summary}>
          <Text style={styles.meta}>Case ID: {caseId}</Text>
          <Text style={styles.meta}>Type: {cfg.shortLabel}</Text>
          <Text style={styles.meta}>Monitoring period: {period}</Text>
          <Text style={styles.meta}>Observations: {observations.length}</Text>
        </View>

        {observations.map((o, i) => (
          <OverallMonitoringCard
            key={o.observation_id}
            index={i}
            observation={o}
            imageUri={imageUris[o.observation_id]}
          />
        ))}

        <ObservationTimeline observations={observations} />
        <RecoveryStatusCard trend={trend} />
        <WeatherTimeline observations={observations} />
        <ConsistencySummary observations={observations} />

        {status?.latest_recommendation ? (
          <View style={styles.guide}>
            <Text style={styles.guideTitle}>
              {String(status.latest_recommendation.title ?? "Monitoring guidance")}
            </Text>
            <Text style={styles.guideHint}>
              Monitoring guidance only — not a treatment prescription.
            </Text>
            {Array.isArray(status.latest_recommendation.actions)
              ? status.latest_recommendation.actions.map((a, i) => (
                  <Text key={i} style={styles.guideItem}>
                    • {String(a)}
                  </Text>
                ))
              : null}
          </View>
        ) : null}

        <Pressable style={styles.primary} onPress={onRestart}>
          <Text style={styles.primaryText}>Start new monitoring case</Text>
        </Pressable>
        {onExit ? (
          <Pressable style={styles.exitBtn} onPress={onExit}>
            <Text style={styles.exitText}>Back to TomatoDoc</Text>
          </Pressable>
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}

function makeStyles(p: MonitoringPalette) {
  return StyleSheet.create({
    safe: { flex: 1, backgroundColor: p.bg },
    content: { padding: 18, paddingBottom: 40 },
    title: { color: p.textPrimary, fontSize: 24, fontWeight: "800", marginBottom: 12 },
    summary: {
      backgroundColor: p.card,
      borderRadius: 14,
      borderWidth: 1,
      borderColor: p.cardBorder,
      padding: 14,
    },
    meta: { color: p.textMuted, marginTop: 4, lineHeight: 18 },
    guide: {
      marginTop: 12,
      backgroundColor: "#2a1012",
      borderRadius: 14,
      padding: 14,
      borderWidth: 1,
      borderColor: "#FF6B6B",
    },
    guideTitle: { color: "#FF6B6B", fontWeight: "700" },
    guideHint: { color: p.textMuted, marginTop: 4, fontSize: 12 },
    guideItem: { color: p.textPrimary, marginTop: 6, lineHeight: 18 },
    primary: {
      marginTop: 20,
      backgroundColor: p.accent,
      borderRadius: 12,
      paddingVertical: 14,
      alignItems: "center",
    },
    primaryText: { color: p.onAccent, fontWeight: "800" },
    exitBtn: {
      marginTop: 12,
      borderRadius: 12,
      paddingVertical: 14,
      alignItems: "center",
      borderWidth: 1,
      borderColor: p.cardBorder,
    },
    exitText: { color: p.textMuted, fontWeight: "700" },
  });
}
