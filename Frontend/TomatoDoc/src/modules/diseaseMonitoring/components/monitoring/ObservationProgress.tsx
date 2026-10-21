import React, { useMemo } from "react";
import { View, Text, StyleSheet } from "react-native";
import { TARGET_OBSERVATIONS, MONITORING_DAY_LABELS } from "../../config/modality";
import { useMonitoringPalette } from "../../theme/MonitoringThemeContext";
import type { MonitoringPalette } from "../../theme/colors";

type Props = {
  current: number;
  overview?: boolean;
};

const STEPS = [
  { key: 1, label: "Obs 1", sub: `Day ${MONITORING_DAY_LABELS[0]}` },
  { key: 2, label: "Obs 2", sub: `Day ${MONITORING_DAY_LABELS[1]}` },
  { key: 3, label: "Obs 3", sub: `Day ${MONITORING_DAY_LABELS[2]}` },
  { key: 4, label: "Overview", sub: "Summary" },
];

export function ObservationProgress({ current, overview }: Props) {
  const activeIndex = overview ? 3 : Math.min(Math.max(current, 1), TARGET_OBSERVATIONS) - 1;
  const p = useMonitoringPalette();
  const styles = useMemo(() => makeStyles(p), [p]);

  return (
    <View style={styles.wrap}>
      {STEPS.map((s, i) => {
        const done = overview ? i <= 3 : i < activeIndex;
        const active = i === activeIndex;
        return (
          <React.Fragment key={s.key}>
            {i > 0 ? <View style={[styles.line, (done || active) && styles.lineOn]} /> : null}
            <View style={styles.step}>
              <View
                style={[
                  styles.dot,
                  done && styles.dotDone,
                  active && styles.dotActive,
                ]}
              >
                <Text
                  style={[
                    styles.dotText,
                    (done || active) && styles.dotTextOn,
                  ]}
                >
                  {done && !active ? "✓" : String(i + 1)}
                </Text>
              </View>
              <Text style={[styles.label, active && styles.labelActive]}>{s.label}</Text>
              <Text style={styles.subLabel}>{s.sub}</Text>
            </View>
          </React.Fragment>
        );
      })}
    </View>
  );
}

function makeStyles(p: MonitoringPalette) {
  return StyleSheet.create({
    wrap: {
      flexDirection: "row",
      alignItems: "flex-start",
      justifyContent: "space-between",
      marginBottom: 18,
      paddingHorizontal: 4,
    },
    step: { alignItems: "center", width: 64 },
    dot: {
      width: 28,
      height: 28,
      borderRadius: 14,
      borderWidth: 1.5,
      borderColor: p.cardBorder,
      backgroundColor: p.bgElevated,
      alignItems: "center",
      justifyContent: "center",
    },
    dotDone: {
      backgroundColor: p.accentDim,
      borderColor: p.accent,
    },
    dotActive: {
      backgroundColor: p.accent,
      borderColor: p.accent,
    },
    dotText: { color: p.textMuted, fontSize: 11, fontWeight: "700" },
    dotTextOn: { color: p.onAccent },
    label: {
      marginTop: 6,
      color: p.textMuted,
      fontSize: 10,
      fontWeight: "600",
      textAlign: "center",
    },
    labelActive: { color: p.textPrimary },
    subLabel: {
      marginTop: 2,
      color: p.textMuted,
      fontSize: 9,
      fontWeight: "600",
      textAlign: "center",
    },
    line: {
      flex: 1,
      height: 2,
      backgroundColor: p.cardBorder,
      marginTop: 13,
      marginHorizontal: -4,
    },
    lineOn: { backgroundColor: p.accentDim },
  });
}
