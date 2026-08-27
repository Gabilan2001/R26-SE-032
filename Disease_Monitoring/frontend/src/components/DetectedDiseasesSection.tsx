import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { palette } from "../theme/colors";

/** Section title + “INDEPENDENT TRACKING” divider (no logic). */
export function DetectedDiseasesSection() {
  return (
    <>
      <Text style={styles.sectionKicker}>DETECTED DISEASES</Text>
      <View style={styles.dividerRow}>
        <View style={styles.dividerLine} />
        <Text style={styles.dividerText}>INDEPENDENT TRACKING</Text>
        <View style={styles.dividerLine} />
      </View>
    </>
  );
}

const styles = StyleSheet.create({
  sectionKicker: {
    color: palette.textMuted,
    fontSize: 11,
    letterSpacing: 1.4,
    fontWeight: "600",
    marginBottom: 14,
  },
  dividerRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 20,
    gap: 10,
  },
  dividerLine: {
    flex: 1,
    height: StyleSheet.hairlineWidth,
    backgroundColor: palette.divider,
  },
  dividerText: {
    color: palette.textMuted,
    fontSize: 10,
    letterSpacing: 1.2,
    fontWeight: "600",
  },
});
