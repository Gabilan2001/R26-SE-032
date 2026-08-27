import React, { useState } from "react";
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
import { palette } from "../../theme/colors";

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
      <LeafScanAppHeader />
      <ScrollView contentContainerStyle={styles.content}>
        <Pressable onPress={onBack}>
          <Text style={styles.back}>← Back</Text>
        </Pressable>
        <Text style={styles.title}>Create monitoring case</Text>
        <Text style={styles.subtitle}>{cfg.title}</Text>

        <View style={styles.card}>
          <Row label="Selected type" value={cfg.shortLabel} />
          <Row label="Case ID" value="Created when you start" />
          <Row label="Start date / time" value={startedAt} />
          <Row label="Location" value={DEMO_WEATHER_COORDS.label} />
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
              trackColor={{ false: palette.cardBorder, true: palette.accentDim }}
              thumbColor={attachWeather ? palette.accent : "#888"}
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
            <ActivityIndicator color="#04210f" />
          ) : (
            <Text style={styles.primaryText}>Start Monitoring</Text>
          )}
        </Pressable>
      </ScrollView>
    </SafeAreaView>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.row}>
      <Text style={styles.rowLabel}>{label}</Text>
      <Text style={styles.rowValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: palette.bg },
  content: { padding: 18, paddingBottom: 40 },
  back: { color: palette.infoText, fontWeight: "600", marginBottom: 12 },
  title: { color: palette.textPrimary, fontSize: 24, fontWeight: "800" },
  subtitle: { color: palette.textMuted, marginTop: 6, marginBottom: 16 },
  card: {
    backgroundColor: palette.card,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: palette.cardBorder,
    padding: 16,
  },
  row: { marginBottom: 12 },
  rowLabel: { color: palette.textMuted, fontSize: 12, fontWeight: "600" },
  rowValue: { color: palette.textPrimary, marginTop: 3, fontWeight: "600" },
  rowHint: { color: palette.textMuted, fontSize: 12, marginTop: 4, lineHeight: 17 },
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
  warnBody: { color: palette.textMuted, marginTop: 6, lineHeight: 18 },
  primary: {
    marginTop: 20,
    backgroundColor: palette.accent,
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: "center",
  },
  primaryText: { color: "#04210f", fontWeight: "800", fontSize: 16 },
  disabled: { opacity: 0.45 },
});
