import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { palette } from "../theme/colors";

export function LeafScanAppHeader() {
  return (
    <View style={styles.topBar}>
      <Text style={styles.appTitle}>LeafScan AI</Text>
      <View style={styles.multiBadge}>
        <Text style={styles.multiBadgeText}>LEAF + FRUIT</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  topBar: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 18,
    paddingTop: 6,
    paddingBottom: 4,
  },
  appTitle: {
    color: palette.textPrimary,
    fontSize: 20,
    fontWeight: "800",
  },
  multiBadge: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 999,
    backgroundColor: palette.accentDim,
    borderWidth: 1,
    borderColor: palette.accent,
  },
  multiBadgeText: {
    color: palette.accent,
    fontSize: 10,
    fontWeight: "800",
    letterSpacing: 0.8,
  },
});
