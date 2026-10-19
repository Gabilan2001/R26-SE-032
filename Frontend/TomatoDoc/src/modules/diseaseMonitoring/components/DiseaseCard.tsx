import React from "react";
import { View, Text, StyleSheet, Pressable } from "react-native";
import { SemicircularSeverityGauge } from "./SemicircularSeverityGauge";
import { ANALYSIS_DAYS } from "../constants/analysisDays";
import { palette, severityColors } from "../theme/colors";
import type { DayKey, DiseaseTrack } from "../types/disease";
import { bandLabel, monitoringLabel } from "../utils/severityLabels";

export type DiseaseCardProps = {
  disease: DiseaseTrack;
  selectedDay: DayKey;
  onSelectDay: (day: DayKey) => void;
};

function clampPct(n: number) {
  return Math.min(100, Math.max(0, n));
}

export function DiseaseCard({
  disease,
  selectedDay,
  onSelectDay,
}: DiseaseCardProps) {
  const snap = disease.daySnapshots?.[selectedDay];
  const infected = snap?.infectedPercent ?? disease.infectedPercent;
  const band = snap?.severityBand ?? disease.severityBand;
  const score = snap?.severityScore ?? disease.severityScore;
  const c = severityColors[band];
  const mon = severityColors[disease.monitoringBand];

  return (
    <View style={styles.card}>
      <View style={styles.cardHeader}>
        <View style={styles.titleRow}>
          <View style={[styles.dot, { backgroundColor: c.main }]} />
          <Text style={styles.diseaseName}>{disease.name}</Text>
        </View>
        <View style={[styles.badge, { backgroundColor: c.badgeBg }]}>
          <Text style={[styles.badgeText, { color: c.badgeText }]}>
            {bandLabel(band)}
          </Text>
        </View>
      </View>

      <Text style={styles.sectionLabel}>Disease severity (relative)</Text>
      <View style={styles.gaugeRow}>
        <SemicircularSeverityGauge score={score} band={band} size={190} />
      </View>

      <View style={styles.monitoringRow}>
        <Text style={styles.monitoringCaption}>Overall monitoring</Text>
        <View style={[styles.monitorPill, { borderColor: mon.main }]}>
          <View style={[styles.miniDot, { backgroundColor: mon.main }]} />
          <Text style={[styles.monitorText, { color: mon.main }]}>
            {monitoringLabel(disease.monitoringBand)}
          </Text>
        </View>
        <Text style={styles.monitoringHint}>
          From weather context with relative severity
        </Text>
      </View>

      <View style={styles.infectedRow}>
        <Text style={styles.infectedLabel}>Infected</Text>
        <Text style={[styles.infectedPct, { color: c.main }]}>
          {Math.round(infected)}%
        </Text>
      </View>
      <View style={styles.barTrack}>
        <View
          style={[
            styles.barFill,
            { width: `${clampPct(infected)}%`, backgroundColor: c.main },
          ]}
        />
      </View>

      <View style={styles.dayRow}>
        {ANALYSIS_DAYS.map(({ key, label }) => {
          const active = key === selectedDay;
          return (
            <Pressable
              key={key}
              onPress={() => onSelectDay(key)}
              style={({ pressed }) => [
                styles.dayChip,
                active && { borderColor: c.main, backgroundColor: c.muted },
                pressed && !active && { opacity: 0.85 },
              ]}
            >
              <Text
                style={[
                  styles.dayChipText,
                  { color: active ? c.main : palette.textMuted },
                ]}
              >
                {label}
              </Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: palette.card,
    borderRadius: 18,
    padding: 18,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: palette.cardBorder,
  },
  cardHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 6,
  },
  titleRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    flex: 1,
    paddingRight: 8,
  },
  dot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  diseaseName: {
    color: palette.textPrimary,
    fontSize: 18,
    fontWeight: "700",
    flexShrink: 1,
  },
  badge: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 999,
  },
  badgeText: {
    fontSize: 10,
    fontWeight: "800",
    letterSpacing: 0.6,
  },
  sectionLabel: {
    marginTop: 8,
    marginBottom: 4,
    color: palette.textMuted,
    fontSize: 11,
    fontWeight: "600",
    letterSpacing: 0.6,
  },
  gaugeRow: {
    alignItems: "center",
    marginBottom: 4,
  },
  monitoringRow: {
    marginTop: 4,
    marginBottom: 14,
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 12,
    backgroundColor: palette.bgElevated,
    borderWidth: 1,
    borderColor: palette.cardBorder,
  },
  monitoringCaption: {
    color: palette.textMuted,
    fontSize: 11,
    fontWeight: "600",
    marginBottom: 6,
  },
  monitorPill: {
    flexDirection: "row",
    alignItems: "center",
    alignSelf: "flex-start",
    gap: 8,
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 999,
    borderWidth: 1,
    backgroundColor: palette.bg,
  },
  miniDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  monitorText: {
    fontSize: 13,
    fontWeight: "700",
  },
  monitoringHint: {
    marginTop: 6,
    color: palette.textMuted,
    fontSize: 11,
    lineHeight: 16,
  },
  infectedRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "baseline",
    marginBottom: 8,
  },
  infectedLabel: {
    color: palette.textMuted,
    fontSize: 13,
    fontWeight: "600",
  },
  infectedPct: {
    fontSize: 15,
    fontWeight: "700",
  },
  barTrack: {
    height: 8,
    borderRadius: 4,
    backgroundColor: palette.trackLine,
    overflow: "hidden",
    marginBottom: 16,
  },
  barFill: {
    height: "100%",
    borderRadius: 4,
  },
  dayRow: {
    flexDirection: "row",
    gap: 10,
  },
  dayChip: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: palette.cardBorder,
    alignItems: "center",
    backgroundColor: palette.bgElevated,
  },
  dayChipText: {
    fontSize: 13,
    fontWeight: "700",
  },
});
