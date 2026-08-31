import React from "react";
import { View, Text, StyleSheet } from "react-native";
import type { MonitoringSummary } from "../../api/observations";
import { MONITORING_DAY_LABELS } from "../../config/modality";
import { palette, severityColors } from "../../theme/colors";
import { formatPct, formatSignedPercent, trendHeadline } from "../../utils/observationDisplay";
import { recoveryHeadline, recoveryTone } from "../../utils/observationLabels";

type Props = {
  summary: MonitoringSummary;
};

function StatBox({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <View style={[styles.statBox, highlight && styles.statBoxPeak]}>
      <Text style={styles.statLabel}>{label}</Text>
      <Text style={[styles.statValue, highlight && styles.statValuePeak]}>{value}</Text>
    </View>
  );
}

export function OverallMonitoringSummaryCard({ summary }: Props) {
  const trend = summary.overall_trend;
  const tone = recoveryTone(trend);
  const trendColor =
    tone === "warning"
      ? severityColors.high.main
      : tone === "success" || tone === "positive"
        ? palette.accent
        : palette.textPrimary;

  const peakObs = summary.peak_observation_number;
  const peakDay = MONITORING_DAY_LABELS[peakObs - 1];
  const peakLine =
    summary.peak_note ??
    (peakDay != null
      ? `Highest severity was on Observation ${peakObs} (Day ${peakDay}): ${formatPct(summary.peak_severity_pct)}.`
      : `Highest severity was on Observation ${peakObs}: ${formatPct(summary.peak_severity_pct)}.`);

  const direction = trendHeadline(trend);

  return (
    <View style={styles.card}>
      <Text style={styles.kicker}>OVERALL MONITORING RESULT</Text>
      <Text style={[styles.headline, { color: trendColor }]}>
        {recoveryHeadline(trend)}
      </Text>

      <View style={styles.statRow}>
        <StatBox label="Initial" value={formatPct(summary.initial_severity_pct)} />
        <StatBox
          label="Peak"
          value={formatPct(summary.peak_severity_pct)}
          highlight
        />
        <StatBox label="Final" value={formatPct(summary.final_severity_pct)} />
      </View>

      <View style={styles.changeRow}>
        <Text style={styles.changeLabel}>Overall change</Text>
        <Text style={styles.changeValue}>
          {formatSignedPercent(summary.overall_change_pct)}
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Observation summary</Text>
        <Text style={styles.timelineValue}>{summary.severity_timeline}</Text>
        <Text style={styles.peakNote}>{peakLine}</Text>
        {direction ? (
          <Text style={styles.trendHint}>
            Compared with Observation 1, the condition looks {direction.toLowerCase()}.
          </Text>
        ) : (
          <Text style={styles.trendHint}>
            Only one observation so far - more photos will show the recovery trend.
          </Text>
        )}
      </View>

      <Text style={styles.disclaimer}>
        Based on observation-based severity estimates - not expert-validated clinical recovery.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: palette.card,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: palette.cardBorder,
    padding: 18,
    marginBottom: 12,
  },
  kicker: {
    color: palette.textMuted,
    fontSize: 11,
    letterSpacing: 1.1,
    fontWeight: "700",
  },
  headline: {
    fontSize: 26,
    fontWeight: "800",
    marginTop: 8,
    lineHeight: 32,
  },
  statRow: {
    flexDirection: "row",
    gap: 10,
    marginTop: 16,
  },
  statBox: {
    flex: 1,
    backgroundColor: palette.bgElevated,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: palette.cardBorder,
    paddingVertical: 12,
    paddingHorizontal: 8,
    alignItems: "center",
  },
  statBoxPeak: { borderColor: palette.accent },
  statLabel: {
    color: palette.textMuted,
    fontSize: 11,
    fontWeight: "700",
    textTransform: "uppercase",
  },
  statValue: {
    color: palette.textPrimary,
    fontSize: 22,
    fontWeight: "800",
    marginTop: 4,
  },
  statValuePeak: { color: palette.accent },
  changeRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginTop: 14,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: palette.cardBorder,
  },
  changeLabel: { color: palette.textMuted, fontWeight: "600" },
  changeValue: { color: palette.textPrimary, fontWeight: "800", fontSize: 18 },
  section: { marginTop: 14 },
  sectionTitle: { color: palette.textMuted, fontSize: 12, fontWeight: "700" },
  timelineValue: {
    color: palette.textPrimary,
    fontWeight: "700",
    fontSize: 16,
    marginTop: 6,
    lineHeight: 22,
  },
  peakNote: { color: palette.infoText, marginTop: 10, fontWeight: "600", lineHeight: 20 },
  trendHint: { color: palette.textMuted, marginTop: 8, lineHeight: 18 },
  disclaimer: { color: palette.textMuted, fontSize: 11, marginTop: 12, lineHeight: 16 },
});
