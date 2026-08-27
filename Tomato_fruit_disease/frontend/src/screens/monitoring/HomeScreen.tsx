import React from "react";
import { View, Text, StyleSheet, Pressable, SafeAreaView, ScrollView } from "react-native";
import { StatusBar } from "expo-status-bar";
import { LeafScanAppHeader } from "../../components/LeafScanAppHeader";
import { MODALITY } from "../../config/modality";
import type { CropPart } from "../../api/observations";
import { palette } from "../../theme/colors";

type Props = {
  onSelect: (cropPart: CropPart) => void;
};

export function HomeScreen({ onSelect }: Props) {
  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar style="light" />
      <LeafScanAppHeader />
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.title}>Tomato Disease Monitoring</Text>
        <Text style={styles.subtitle}>
          Observation-based severity and recovery tracking. Upload photos over time to compare
          relative severity, visual consistency, and weather context — not disease identification
          or treatment advice.
        </Text>

        <Text style={styles.section}>Choose monitoring type</Text>

        {(["LEAF", "FRUIT"] as CropPart[]).map((part) => {
          const cfg = MODALITY[part];
          return (
            <Pressable
              key={part}
              style={styles.card}
              onPress={() => onSelect(part)}
            >
              <View style={styles.cardTop}>
                <Text style={styles.cardTitle}>{cfg.shortLabel}</Text>
                {!cfg.severityReady ? (
                  <View style={styles.pendingBadge}>
                    <Text style={styles.pendingText}>PENDING</Text>
                  </View>
                ) : (
                  <View style={styles.readyBadge}>
                    <Text style={styles.readyText}>READY</Text>
                  </View>
                )}
              </View>
              <Text style={styles.cardBody}>{cfg.explanation}</Text>
            </Pressable>
          );
        })}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: palette.bg },
  content: { padding: 18, paddingBottom: 40 },
  title: { color: palette.textPrimary, fontSize: 26, fontWeight: "800", marginTop: 8 },
  subtitle: { color: palette.textMuted, marginTop: 10, lineHeight: 21, marginBottom: 22 },
  section: {
    color: palette.textMuted,
    fontSize: 12,
    letterSpacing: 1,
    fontWeight: "700",
    marginBottom: 12,
  },
  card: {
    backgroundColor: palette.card,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: palette.cardBorder,
    padding: 16,
    marginBottom: 12,
  },
  cardTop: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  cardTitle: { color: palette.textPrimary, fontSize: 20, fontWeight: "800" },
  cardBody: { color: palette.textMuted, marginTop: 8, lineHeight: 20 },
  readyBadge: {
    backgroundColor: palette.accentDim,
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderWidth: 1,
    borderColor: palette.accent,
  },
  readyText: { color: palette.accent, fontSize: 10, fontWeight: "800" },
  pendingBadge: {
    backgroundColor: "#2a2210",
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderWidth: 1,
    borderColor: "#FFB347",
  },
  pendingText: { color: "#FFB347", fontSize: 10, fontWeight: "800" },
});
