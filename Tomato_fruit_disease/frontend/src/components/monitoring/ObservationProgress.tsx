import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { TARGET_OBSERVATIONS } from "../../config/modality";
import { palette } from "../../theme/colors";

type Props = {
  current: number;
  /** When true, highlight Overview as active */
  overview?: boolean;
};

const STEPS = [
  { key: 1, label: "Obs 1" },
  { key: 2, label: "Obs 2" },
  { key: 3, label: "Obs 3" },
  { key: 4, label: "Overview" },
];

export function ObservationProgress({ current, overview }: Props) {
  const activeIndex = overview ? 3 : Math.min(Math.max(current, 1), TARGET_OBSERVATIONS) - 1;

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
            </View>
          </React.Fragment>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
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
    borderColor: palette.cardBorder,
    backgroundColor: palette.bgElevated,
    alignItems: "center",
    justifyContent: "center",
  },
  dotDone: {
    backgroundColor: palette.accentDim,
    borderColor: palette.accent,
  },
  dotActive: {
    backgroundColor: palette.accent,
    borderColor: palette.accent,
  },
  dotText: { color: palette.textMuted, fontSize: 11, fontWeight: "700" },
  dotTextOn: { color: "#04210f" },
  label: {
    marginTop: 6,
    color: palette.textMuted,
    fontSize: 10,
    fontWeight: "600",
    textAlign: "center",
  },
  labelActive: { color: palette.textPrimary },
  line: {
    flex: 1,
    height: 2,
    backgroundColor: palette.cardBorder,
    marginTop: 13,
    marginHorizontal: -4,
  },
  lineOn: { backgroundColor: palette.accentDim },
});
