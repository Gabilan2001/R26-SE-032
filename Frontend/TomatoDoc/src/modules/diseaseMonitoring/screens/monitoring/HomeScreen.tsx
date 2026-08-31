import React, { useMemo, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  Pressable,
  SafeAreaView,
  ScrollView,
} from "react-native";
import { StatusBar } from "expo-status-bar";
import { LeafScanAppHeader } from "../../components/LeafScanAppHeader";
import { MODALITY } from "../../config/modality";
import type { CropPart } from "../../api/observations";
import { useMonitoringPalette } from "../../theme/MonitoringThemeContext";
import type { MonitoringPalette } from "../../theme/colors";

type Props = {
  onSelect: (cropPart: CropPart) => void;
  onExit?: () => void;
};

export function HomeScreen({ onSelect, onExit }: Props) {
  const p = useMonitoringPalette();
  const styles = useMemo(() => makeStyles(p), [p]);

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar style="light" />
      <LeafScanAppHeader
        title="Disease Monitoring"
        badge="LEAF + FRUIT"
        onBack={onExit}
      />
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.title}>Tomato Disease Monitoring</Text>
        <Text style={styles.subtitle}>
          Observation-based severity and recovery tracking. Upload photos over time to compare
          relative severity, visual consistency, and weather context - not disease identification.
        </Text>

        <Text style={styles.section}>Choose monitoring type</Text>

        {(["LEAF", "FRUIT"] as CropPart[]).map((part) => {
          const cfg = MODALITY[part];
          const isFruit = part === "FRUIT";
          return (
            <Pressable
              key={part}
              style={[styles.card, isFruit && styles.cardFruit]}
              onPress={() => onSelect(part)}
            >
              <View style={styles.cardTop}>
                <Text style={styles.cardTitle}>{cfg.title}</Text>
                {!cfg.severityReady ? (
                  <View style={styles.pendingBadge}>
                    <Text style={styles.pendingText}>PENDING</Text>
                  </View>
                ) : (
                  <View style={[styles.readyBadge, isFruit && styles.readyBadgeFruit]}>
                    <Text style={[styles.readyText, isFruit && styles.readyTextFruit]}>
                      READY
                    </Text>
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

function makeStyles(p: MonitoringPalette) {
  return StyleSheet.create({
    safe: { flex: 1, backgroundColor: p.bg },
    content: { padding: 18, paddingBottom: 40 },
    title: { color: p.textPrimary, fontSize: 26, fontWeight: "800", marginTop: 8 },
    subtitle: { color: p.textMuted, marginTop: 10, lineHeight: 21, marginBottom: 22 },
    section: {
      color: p.textMuted,
      fontSize: 12,
      letterSpacing: 1,
      fontWeight: "700",
      marginBottom: 12,
    },
    card: {
      backgroundColor: p.card,
      borderRadius: 16,
      borderWidth: 1,
      borderColor: p.accentBorder,
      padding: 16,
      marginBottom: 12,
    },
    cardFruit: {
      borderColor: "rgba(255,92,92,0.20)",
    },
    cardTop: {
      flexDirection: "row",
      justifyContent: "space-between",
      alignItems: "center",
    },
    cardTitle: { color: p.textPrimary, fontSize: 20, fontWeight: "800" },
    cardBody: { color: p.textMuted, marginTop: 8, lineHeight: 20 },
    readyBadge: {
      backgroundColor: p.accentDim,
      borderRadius: 999,
      paddingHorizontal: 10,
      paddingVertical: 4,
      borderWidth: 1,
      borderColor: p.accentBorder,
    },
    readyBadgeFruit: {
      backgroundColor: "rgba(255,92,92,0.08)",
      borderColor: "rgba(255,92,92,0.20)",
    },
    readyText: { color: p.accent, fontSize: 10, fontWeight: "800" },
    readyTextFruit: { color: "#ff5c5c" },
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
}
