import React, { useMemo } from "react";
import { View, Text, StyleSheet, Pressable } from "react-native";
import { useMonitoringPalette } from "../theme/MonitoringThemeContext";
import type { MonitoringPalette } from "../theme/colors";

type Props = {
  title?: string;
  badge?: string;
  /** TomatoDoc-style circular back (same as Leaf Scanner). */
  onBack?: () => void;
};

/**
 * Header matching TomatoDoc Scan screens: circular ← + bold title.
 * Colors follow MonitoringThemeProvider (hub / leaf / fruit).
 */
export function LeafScanAppHeader({
  title = "Disease Monitoring",
  badge,
  onBack,
}: Props) {
  const p = useMonitoringPalette();
  const styles = useMemo(() => makeStyles(p), [p]);

  return (
    <View style={styles.topBar}>
      <View style={styles.left}>
        {onBack ? (
          <Pressable style={styles.backBtn} onPress={onBack} hitSlop={8}>
            <Text style={styles.backArrow}>←</Text>
          </Pressable>
        ) : null}
        <Text style={styles.appTitle} numberOfLines={1}>
          {title}
        </Text>
      </View>
      {badge ? (
        <View style={styles.multiBadge}>
          <Text style={styles.multiBadgeText}>{badge}</Text>
        </View>
      ) : null}
    </View>
  );
}

function makeStyles(p: MonitoringPalette) {
  return StyleSheet.create({
    topBar: {
      flexDirection: "row",
      alignItems: "center",
      justifyContent: "space-between",
      paddingHorizontal: 18,
      paddingTop: 6,
      paddingBottom: 8,
    },
    left: {
      flexDirection: "row",
      alignItems: "center",
      gap: 10,
      flex: 1,
      paddingRight: 8,
    },
    backBtn: {
      width: 32,
      height: 32,
      borderRadius: 16,
      backgroundColor: p.bgElevated,
      borderWidth: 1,
      borderColor: p.cardBorder,
      alignItems: "center",
      justifyContent: "center",
    },
    backArrow: {
      fontSize: 16,
      color: p.textPrimary,
    },
    appTitle: {
      color: p.textPrimary,
      fontSize: 18,
      fontWeight: "800",
      flexShrink: 1,
    },
    multiBadge: {
      paddingHorizontal: 10,
      paddingVertical: 5,
      borderRadius: 999,
      backgroundColor: p.accentDim,
      borderWidth: 1,
      borderColor: p.accentBorder,
    },
    multiBadgeText: {
      color: p.accent,
      fontSize: 10,
      fontWeight: "800",
      letterSpacing: 0.8,
    },
  });
}
