import React, { useEffect, useState } from "react";
import {
  Alert,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { StatusBar } from "expo-status-bar";
import {
  downloadCaseReport,
  getFarmerInsight,
  type CaseStatus,
  type CropPart,
  type FarmerInsight,
  type Observation,
} from "../../api/observations";
import { LeafScanAppHeader } from "../../components/LeafScanAppHeader";
import {
  ConsistencySummary,
  MonitoringInsightCard,
  ObservationProgress,
  ObservationTimeline,
  OverallMonitoringCard,
  OverallMonitoringSummaryCard,
  RecoveryStatusCard,
  SeverityTrendGraph,
  WeatherTimeline,
} from "../../components/monitoring";
import { MODALITY } from "../../config/modality";
import { palette } from "../../theme/colors";
import { computeOverallSummary } from "../../utils/observationDisplay";

type Props = {
  cropPart: CropPart;
  caseId: string;
  status: CaseStatus | null;
  observations: Observation[];
  imageUris: Record<string, string>;
  onRestart: () => void;
};

export function OverallMonitoringScreen({
  cropPart,
  caseId,
  status,
  observations,
  imageUris,
  onRestart,
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
  const monitoringSummary =
    status?.monitoring_summary ?? computeOverallSummary(observations);

  const [insight, setInsight] = useState<FarmerInsight | null>(null);
  const [insightLoading, setInsightLoading] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setInsightLoading(true);
    getFarmerInsight(caseId)
      .then((data) => {
        if (!cancelled) setInsight(data);
      })
      .catch(() => {
        if (!cancelled) setInsight(null);
      })
      .finally(() => {
        if (!cancelled) setInsightLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [caseId, observations.length]);

  const onDownloadReport = async () => {
    setReportLoading(true);
    try {
      await downloadCaseReport(caseId);
    } catch (e) {
      Alert.alert(
        "Download failed",
        String(e).includes("saved to")
          ? String(e)
          : "Could not download the monitoring report. Please try again."
      );
    } finally {
      setReportLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar style="light" />
      <LeafScanAppHeader />
      <ScrollView contentContainerStyle={styles.content}>
        <ObservationProgress current={3} overview />
        <Text style={styles.title}>Overall Monitoring</Text>

        {monitoringSummary ? (
          <OverallMonitoringSummaryCard summary={monitoringSummary} />
        ) : null}

        <MonitoringInsightCard insight={insight} loading={insightLoading} />

        <SeverityTrendGraph
          observations={observations}
          peakObservationNumber={monitoringSummary?.peak_observation_number}
        />

        <View style={styles.summary}>
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

        <ObservationTimeline
          observations={observations}
          peakObservationNumber={monitoringSummary?.peak_observation_number}
        />
        <RecoveryStatusCard trend={trend} />
        <WeatherTimeline observations={observations} />
        <ConsistencySummary observations={observations} />

        {status?.latest_recommendation ? (
          <View style={styles.guide}>
            <Text style={styles.guideTitle}>
              {String(status.latest_recommendation.title ?? "Monitoring guidance")}
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

        <Text style={styles.caseFootnote}>Case ID: {caseId}</Text>

        <Pressable
          style={[styles.secondaryBtn, reportLoading && styles.disabled]}
          onPress={() => void onDownloadReport()}
          disabled={reportLoading || observations.length === 0}
        >
          <Text style={styles.secondaryBtnText}>
            {reportLoading ? "Preparing PDF…" : "Download monitoring report (PDF)"}
          </Text>
        </Pressable>

        <Pressable style={styles.primary} onPress={onRestart}>
          <Text style={styles.primaryText}>Start new monitoring case</Text>
        </Pressable>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: palette.bg },
  content: { padding: 18, paddingBottom: 40 },
  title: { color: palette.textPrimary, fontSize: 24, fontWeight: "800", marginBottom: 12 },
  summary: {
    backgroundColor: palette.card,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: palette.cardBorder,
    padding: 14,
  },
  meta: { color: palette.textMuted, marginTop: 4, lineHeight: 18 },
  guide: {
    marginTop: 12,
    backgroundColor: "#2a1012",
    borderRadius: 14,
    padding: 14,
    borderWidth: 1,
    borderColor: "#FF6B6B",
  },
  guideTitle: { color: "#FF6B6B", fontWeight: "700" },
  guideHint: { color: palette.textMuted, marginTop: 4, fontSize: 12 },
  guideItem: { color: palette.textPrimary, marginTop: 6, lineHeight: 18 },
  caseFootnote: { color: palette.textMuted, fontSize: 11, marginTop: 16, textAlign: "center" },
  secondaryBtn: {
    marginTop: 14,
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
    borderWidth: 1,
    borderColor: palette.accent,
    backgroundColor: palette.accentDim,
  },
  secondaryBtnText: { color: palette.accent, fontWeight: "800" },
  disabled: { opacity: 0.5 },
  primary: {
    marginTop: 20,
    backgroundColor: palette.accent,
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
  },
  primaryText: { color: "#04210f", fontWeight: "800" },
});
