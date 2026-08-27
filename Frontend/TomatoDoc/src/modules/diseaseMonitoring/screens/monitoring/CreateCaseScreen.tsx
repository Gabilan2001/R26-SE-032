import React, { useMemo, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  Pressable,
  SafeAreaView,
  ScrollView,
  ActivityIndicator,
  Alert,
  Switch,
} from "react-native";
import { StatusBar } from "expo-status-bar";
import { createCase, type CropPart, type MonitoringCase } from "../../api/observations";
import { LeafScanAppHeader } from "../../components/LeafScanAppHeader";
import { DEMO_WEATHER_COORDS, MODALITY } from "../../config/modality";
import { useMonitoringPalette } from "../../theme/MonitoringThemeContext";
import type { MonitoringPalette } from "../../theme/colors";

type Props = {
  cropPart: CropPart;
  attachWeather: boolean;
  onToggleWeather: (v: boolean) => void;
  onCreated: (created: MonitoringCase) => void;
  onBack: () => void;
};

export function CreateCaseScreen({
  cropPart,
  attachWeather,
  onToggleWeather,
  onCreated,
  onBack,
}: Props) {
  const [loading, setLoading] = useState(false);
  const cfg = MODALITY[cropPart];
  const startedAt = new Date().toLocaleString();
  const p = useMonitoringPalette();
  const styles = useMemo(() => makeStyles(p), [p]);

  const handleStart = async () => {
    if (!cfg.severityReady) {
      Alert.alert("Fruit model pending", cfg.pendingMessage ?? "Fruit CNN not ready.");
      return;
    }
    try {
      setLoading(true);
      const created = await createCase(cropPart, `${cropPart.toLowerCase()}-monitor`);
      onCreated(created);
    } catch (e) {
      Alert.alert("Could not create case", String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar style="light" />
      <LeafScanAppHeader
        title={cfg.title}
        badge={cfg.shortLabel.toUpperCase()}
        onBack={onBack}
      />
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.title}>Create monitoring case</Text>
        <Text style={styles.subtitle}>{cfg.title}</Text>

        <View style={styles.card}>
          <Row label="Selected type" value={cfg.shortLabel} styles={styles} />
          <Row label="Case ID" value="Created when you start" styles={styles} />
          <Row label="Start date / time" value={startedAt} styles={styles} />
          <Row label="Location" value={DEMO_WEATHER_COORDS.label} styles={styles} />
          <View style={styles.weatherRow}>
            <View style={{ flex: 1 }}>
              <Text style={styles.rowLabel}>Weather context</Text>
              <Text style={styles.rowHint}>
                Attach OpenWeather context on each upload using demo coordinates.
              </Text>
            </View>
            <Switch
              value={attachWeather}
              onValueChange={onToggleWeather}
              trackColor={{ false: p.cardBorder, true: p.accentDim }}
              thumbColor={attachWeather ? p.accent : "#888"}
            />
          </View>
        </View>

        {!cfg.severityReady ? (
          <View style={styles.warn}>
            <Text style={styles.warnTitle}>Fruit severity pending</Text>
            <Text style={styles.warnBody}>{cfg.pendingMessage}</Text>
          </View>
        ) : null}

        <Pressable
          style={[styles.primary, (!cfg.severityReady || loading) && styles.disabled]}
          onPress={handleStart}
          disabled={!cfg.severityReady || loading}
        >
          {loading ? (
            <ActivityIndicator color={p.onAccent} />
          ) : (
            <Text style={styles.primaryText}>Start Monitoring</Text>
          )}
        </Pressable>
      </ScrollView>
    </SafeAreaView>
  );
}

function Row({
  label,
  value,
  styles,
}: {
  label: string;
  value: string;
  styles: ReturnType<typeof makeStyles>;
}) {
  return (
    <View style={styles.row}>
      <Text style={styles.rowLabel}>{label}</Text>
      <Text style={styles.rowValue}>{value}</Text>
    </View>
  );
}

function makeStyles(p: MonitoringPalette) {
  return StyleSheet.create({
    safe: { flex: 1, backgroundColor: p.bg },
    content: { padding: 18, paddingBottom: 40 },
    title: { color: p.textPrimary, fontSize: 24, fontWeight: "800" },
    subtitle: { color: p.textMuted, marginTop: 6, marginBottom: 16 },
    card: {
      backgroundColor: p.card,
      borderRadius: 16,
      borderWidth: 1,
      borderColor: p.cardBorder,
      padding: 16,
    },
    row: { marginBottom: 12 },
    rowLabel: { color: p.textMuted, fontSize: 12, fontWeight: "600" },
    rowValue: { color: p.textPrimary, marginTop: 3, fontWeight: "600" },
    rowHint: { color: p.textMuted, fontSize: 12, marginTop: 4, lineHeight: 17 },
    weatherRow: { flexDirection: "row", alignItems: "center", gap: 12, marginTop: 4 },
    warn: {
      marginTop: 14,
      backgroundColor: "#2a2210",
      borderRadius: 12,
      padding: 14,
      borderWidth: 1,
      borderColor: "#FFB347",
    },
    warnTitle: { color: "#FFB347", fontWeight: "700" },
    warnBody: { color: p.textMuted, marginTop: 6, lineHeight: 18 },
    primary: {
      marginTop: 20,
      backgroundColor: p.accent,
      borderRadius: 12,
      paddingVertical: 16,
      alignItems: "center",
    },
    primaryText: { color: p.onAccent, fontWeight: "800", fontSize: 16 },
    disabled: { opacity: 0.45 },
  });
}
