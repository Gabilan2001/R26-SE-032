import React from "react";
import { View, Text, StyleSheet, Pressable } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { useSafeAreaInsets } from "react-native-safe-area-context";

type Props = {
  title?: string;
  badge?: string;
  /** Circular back button, same as the other TomatoDoc module headers. */
  onBack?: () => void;
};

/**
 * Forest-green header shared by every Disease Monitoring screen. It handles the top safe-area
 * inset itself, so the screens around it use a plain frame. Matches src/components/ScreenHeader.
 */
export function LeafScanAppHeader({
  title = "Disease Monitoring",
  badge,
  onBack,
}: Props) {
  const insets = useSafeAreaInsets();

  return (
    <LinearGradient
      colors={["#0E3326", "#1B5A3F", "#357A4A"]}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
      style={[styles.wrap, { paddingTop: insets.top + 12 }]}
    >
      <View style={styles.topBar}>
        <View style={styles.left}>
          {onBack ? (
            <Pressable style={styles.backBtn} onPress={onBack} hitSlop={8}>
              <Text style={styles.backArrow}>←</Text>
            </Pressable>
          ) : null}
          <View style={{ flex: 1 }}>
            <Text style={styles.eyebrow}>Monitoring module</Text>
            <Text style={styles.appTitle} numberOfLines={2}>
              {title}
            </Text>
          </View>
        </View>
        {badge ? (
          <View style={styles.multiBadge}>
            <Text style={styles.multiBadgeText}>{badge}</Text>
          </View>
        ) : null}
      </View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  wrap: {
    paddingHorizontal: 18,
    paddingBottom: 20,
    borderBottomLeftRadius: 28,
    borderBottomRightRadius: 28,
    marginBottom: 6,
  },
  topBar: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  left: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    flex: 1,
    paddingRight: 8,
  },
  backBtn: {
    width: 40,
    height: 40,
    borderRadius: 14,
    backgroundColor: "rgba(255,255,255,0.10)",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.18)",
    alignItems: "center",
    justifyContent: "center",
  },
  backArrow: {
    fontSize: 18,
    color: "#FFFFFF",
  },
  eyebrow: {
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 1.6,
    textTransform: "uppercase",
    color: "#D6EF75",
    marginBottom: 2,
  },
  appTitle: {
    color: "#FFFFFF",
    fontSize: 21,
    fontWeight: "800",
    letterSpacing: -0.4,
    flexShrink: 1,
  },
  multiBadge: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 999,
    backgroundColor: "rgba(255,255,255,0.10)",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.18)",
  },
  multiBadgeText: {
    color: "#D6EF75",
    fontSize: 10,
    fontWeight: "800",
    letterSpacing: 0.8,
  },
});
