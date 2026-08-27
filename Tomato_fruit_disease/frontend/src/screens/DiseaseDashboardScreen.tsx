import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  View,
} from "react-native";
import { StatusBar } from "expo-status-bar";
import * as ImagePicker from "expo-image-picker";
import { pingHealth } from "../api/health";
import {
  createCase,
  FRUIT_DISEASES,
  getCaseStatus,
  LEAF_DISEASES,
  listObservations,
  uploadObservation,
  type CropPart,
  type CaseStatus,
  type Observation,
} from "../api/observations";
import { LeafScanAppHeader } from "../components/LeafScanAppHeader";
import { SemicircularSeverityGauge } from "../components/SemicircularSeverityGauge";
import { API_BASE_URL } from "../config/env";
import { palette, severityColors } from "../theme/colors";
import {
  consistencyFarmerHint,
  consistencyFarmerTitle,
  formatDiseaseName,
  formatScore,
  trendFarmerLabel,
} from "../utils/observationLabels";

/** Demo weather coordinates (Colombo) — contextual only, not treatment advice. */
const DEMO_WEATHER_COORDS = { latitude: 6.9271, longitude: 79.8612 };

export default function DiseaseDashboardScreen() {
  const [cropPart, setCropPart] = useState<CropPart>("LEAF");
  const [caseId, setCaseId] = useState<string | null>(null);
  const [disease, setDisease] = useState<string>("early_blight");
  const [status, setStatus] = useState<CaseStatus | null>(null);
  const [observations, setObservations] = useState<Observation[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [attachWeather, setAttachWeather] = useState(true);
  const [pendingUri, setPendingUri] = useState<string | null>(null);
  const [pendingMeta, setPendingMeta] = useState<{
    consistency?: string;
    similarity?: number | null;
    reason?: string;
  } | null>(null);

  const diseases = useMemo(
    () => (cropPart === "LEAF" ? LEAF_DISEASES : FRUIT_DISEASES),
    [cropPart]
  );

  const latest = status?.latest_observation ?? null;
  const previous =
    observations.length >= 2 ? observations[observations.length - 2] : null;
  const observationNumber = observations.length;
  const pendingIsMismatch = pendingMeta?.consistency === "MISMATCH";
  const pendingIsPossible = pendingMeta?.consistency === "POSSIBLE_MATCH";

  useEffect(() => {
    setDisease(diseases[0]);
  }, [diseases]);

  useEffect(() => {
    if (!__DEV__) return;
    pingHealth().then((ok) => {
      if (!ok) console.warn("[API] Backend not reachable at", API_BASE_URL);
    });
  }, []);

  const refreshCase = useCallback(async (id: string) => {
    const [nextStatus, nextObs] = await Promise.all([
      getCaseStatus(id),
      listObservations(id),
    ]);
    setStatus(nextStatus);
    setObservations(nextObs.observations);
  }, []);

  const handleCreateCase = async () => {
    try {
      setLoading(true);
      setMessage(null);
      setPendingUri(null);
      setPendingMeta(null);
      const created = await createCase(cropPart, `${cropPart.toLowerCase()}-demo`);
      setCaseId(created.case_id);
      await refreshCase(created.case_id);
      setMessage(`Monitoring case created. You can upload Observation 1 next.`);
    } catch (e) {
      Alert.alert("Error", String(e));
    } finally {
      setLoading(false);
    }
  };

  const doUpload = async (uri: string, confirmSameCase: boolean) => {
    if (!caseId) return;
    setLoading(true);
    setMessage(null);
    try {
      const result = await uploadObservation({
        caseId,
        cropPart,
        disease,
        uri,
        confirmSameCase,
        latitude: attachWeather ? DEMO_WEATHER_COORDS.latitude : undefined,
        longitude: attachWeather ? DEMO_WEATHER_COORDS.longitude : undefined,
      });

      if (!result.accepted) {
        const consistency = String(result.consistency_status ?? "");
        const reason = String(result.rejection_reason ?? "Observation rejected.");
        const similarity =
          typeof result.similarity_score === "number" ? result.similarity_score : null;

        if (result.image_valid === false) {
          setPendingUri(null);
          setPendingMeta(null);
          setMessage(
            `This photo was not accepted as a valid leaf image. ${reason}`
          );
          return;
        }

        if (!confirmSameCase && consistency === "POSSIBLE_MATCH") {
          setPendingUri(uri);
          setPendingMeta({ consistency, similarity, reason });
          setMessage(null);
          return;
        }

        if (!confirmSameCase && consistency === "MISMATCH") {
          setPendingUri(uri);
          setPendingMeta({ consistency, similarity, reason });
          setMessage(null);
          return;
        }

        setPendingUri(null);
        setPendingMeta(null);
        setMessage(reason);
        return;
      }

      setPendingUri(null);
      setPendingMeta(null);
      const obs = result.observation as Observation | undefined;
      const isFirst = obs?.consistency_status === "BASELINE";
      setMessage(
        isFirst
          ? "Observation 1 saved as the baseline for this case."
          : `Observation saved. ${trendFarmerLabel(obs?.trend)}`
      );
      await refreshCase(caseId);
    } catch (e) {
      const text = String(e);
      if (cropPart === "FRUIT" && (text.includes("503") || text.toLowerCase().includes("fruit"))) {
        Alert.alert(
          "Fruit model unavailable",
          "Fruit severity CNN could not be loaded. Check FRUIT_SEVERITY_MODEL_PATH and restart the backend."
        );
      } else {
        Alert.alert("Upload failed", text);
      }
    } finally {
      setLoading(false);
    }
  };

  const handlePickAndUpload = async () => {
    if (!caseId) {
      Alert.alert("Create a case first");
      return;
    }
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      Alert.alert("Permission required", "Allow photo library access to upload observations.");
      return;
    }
    const picked = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.9,
    });
    if (picked.canceled || !picked.assets[0]?.uri) return;
    await doUpload(picked.assets[0].uri, false);
  };

  const weatherText = (() => {
    const wx = latest?.weather_context as
      | {
          interpretation?: string;
          available?: boolean;
          risk_level?: string;
          details?: Record<string, unknown>;
        }
      | null
      | undefined;
    if (!wx) return null;
    if (wx.interpretation) return wx.interpretation;
    if (wx.available === false) return "Weather data unavailable.";
    return null;
  })();

  const weatherDetails = (() => {
    const wx = latest?.weather_context as
      | { details?: { humidity?: number; temperature?: number; rainfall?: number } }
      | null
      | undefined;
    return wx?.details ?? null;
  })();

  const nextObservationLabel =
    observationNumber === 0
      ? "Upload Observation 1"
      : `Upload Observation ${observationNumber + 1}`;

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar style="light" />
      <LeafScanAppHeader />
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.title}>Leaf Observation Monitoring</Text>
        <Text style={styles.subtitle}>
          Track leaf severity over time for one monitoring case. Disease name comes from your
          selection. Fruit monitoring stays pending until a fruit model is ready.
        </Text>

        <View style={styles.row}>
          {(["LEAF", "FRUIT"] as CropPart[]).map((part) => (
            <Pressable
              key={part}
              style={[styles.chip, cropPart === part && styles.chipActive]}
              onPress={() => setCropPart(part)}
            >
              <Text style={[styles.chipText, cropPart === part && styles.chipTextActive]}>
                {part}
                {part === "FRUIT" ? " (soon)" : ""}
              </Text>
            </Pressable>
          ))}
        </View>

        <Pressable style={styles.primaryBtn} onPress={handleCreateCase} disabled={loading}>
          <Text style={styles.primaryBtnText}>Create {cropPart} Monitoring Case</Text>
        </Pressable>

        {caseId ? (
          <View style={styles.caseBox}>
            <Text style={styles.caseLabel}>Monitoring Case ID</Text>
            <Text style={styles.caseValue}>{caseId}</Text>
            <Text style={styles.meta}>
              Observations saved: {observationNumber}
              {observationNumber === 1 ? " · baseline set" : ""}
            </Text>
          </View>
        ) : null}

        <View style={styles.weatherToggleRow}>
          <View style={{ flex: 1 }}>
            <Text style={styles.sectionLabel}>Attach weather context</Text>
            <Text style={styles.meta}>
              Uses demo coordinates (Colombo). Weather is context only — not treatment advice.
            </Text>
          </View>
          <Switch
            value={attachWeather}
            onValueChange={setAttachWeather}
            trackColor={{ false: palette.cardBorder, true: palette.accentDim }}
            thumbColor={attachWeather ? palette.accent : "#888"}
          />
        </View>

        <Text style={styles.sectionLabel}>Disease (from disease ID)</Text>
        <View style={styles.rowWrap}>
          {diseases.map((d) => (
            <Pressable
              key={d}
              style={[styles.chip, disease === d && styles.chipActive]}
              onPress={() => setDisease(d)}
            >
              <Text style={[styles.chipText, disease === d && styles.chipTextActive]}>
                {formatDiseaseName(d)}
              </Text>
            </Pressable>
          ))}
        </View>

        <Pressable style={styles.secondaryBtn} onPress={handlePickAndUpload} disabled={loading}>
          <Text style={styles.secondaryBtnText}>{nextObservationLabel}</Text>
        </Pressable>

        {pendingUri && pendingMeta && pendingIsPossible ? (
          <View style={styles.confirmBox}>
            <Text style={styles.confirmTitle}>
              {consistencyFarmerTitle("POSSIBLE_MATCH")}
            </Text>
            <Text style={styles.meta}>
              Similarity score:{" "}
              {pendingMeta.similarity != null ? pendingMeta.similarity.toFixed(2) : "n/a"}
            </Text>
            <Text style={styles.meta}>{consistencyFarmerHint("POSSIBLE_MATCH")}</Text>
            {pendingMeta.reason ? <Text style={styles.meta}>{pendingMeta.reason}</Text> : null}
            <View style={styles.row}>
              <Pressable
                style={styles.primaryBtn}
                disabled={loading}
                onPress={() => doUpload(pendingUri, true)}
              >
                <Text style={styles.primaryBtnText}>Confirm same case</Text>
              </Pressable>
              <Pressable
                style={styles.secondaryBtn}
                disabled={loading}
                onPress={() => {
                  setPendingUri(null);
                  setPendingMeta(null);
                  setMessage("Upload cancelled. Create a new case if this is a different crop.");
                }}
              >
                <Text style={styles.secondaryBtnText}>Cancel</Text>
              </Pressable>
            </View>
          </View>
        ) : null}

        {pendingUri && pendingMeta && pendingIsMismatch ? (
          <View style={styles.mismatchBox}>
            <Text style={styles.mismatchTitle}>
              {consistencyFarmerTitle("MISMATCH")}
            </Text>
            <Text style={styles.meta}>
              Similarity score:{" "}
              {pendingMeta.similarity != null ? pendingMeta.similarity.toFixed(2) : "n/a"}
            </Text>
            <Text style={styles.meta}>{consistencyFarmerHint("MISMATCH")}</Text>
            {pendingMeta.reason ? <Text style={styles.meta}>{pendingMeta.reason}</Text> : null}
            <Text style={styles.mismatchAdvice}>
              Recommended: start a new monitoring case for this photo.
            </Text>
            <View style={styles.row}>
              <Pressable
                style={styles.secondaryBtn}
                disabled={loading}
                onPress={() => {
                  setPendingUri(null);
                  setPendingMeta(null);
                  setMessage("Upload cancelled. Create a new case for a different leaf or plant.");
                }}
              >
                <Text style={styles.secondaryBtnText}>Cancel upload</Text>
              </Pressable>
              <Pressable
                style={styles.overrideBtn}
                disabled={loading}
                onPress={() => doUpload(pendingUri, true)}
              >
                <Text style={styles.overrideBtnText}>Force add to this case</Text>
              </Pressable>
            </View>
          </View>
        ) : null}

        {loading ? <ActivityIndicator color={palette.accent} style={{ marginTop: 12 }} /> : null}
        {message ? <Text style={styles.message}>{message}</Text> : null}

        {status && latest ? (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Latest observation result</Text>

            <View style={styles.resultGrid}>
              <Text style={styles.resultKey}>Monitoring Case ID</Text>
              <Text style={styles.resultVal}>{status.case_id}</Text>

              <Text style={styles.resultKey}>Observation</Text>
              <Text style={styles.resultVal}>
                Observation {observationNumber}
                {observationNumber === 1 || latest.consistency_status === "BASELINE"
                  ? " · BASELINE"
                  : ""}
              </Text>

              <Text style={styles.resultKey}>Date / time</Text>
              <Text style={styles.resultVal}>
                {new Date(latest.created_at).toLocaleString()}
              </Text>

              <Text style={styles.resultKey}>Disease</Text>
              <Text style={styles.resultVal}>{formatDiseaseName(latest.disease)}</Text>

              <Text style={styles.resultKey}>Severity</Text>
              <Text
                style={[
                  styles.resultVal,
                  {
                    color:
                      latest.severity_class === "HIGH"
                        ? severityColors.high.main
                        : severityColors.low.main,
                  },
                ]}
              >
                {latest.severity_class}
              </Text>

              <Text style={styles.resultKey}>Relative P(HIGH)</Text>
              <Text style={styles.resultVal}>{formatScore(latest.severity_score)}</Text>
            </View>

            <View style={styles.gaugeWrap}>
              <SemicircularSeverityGauge
                score={Math.round(latest.severity_score * 100)}
                band={latest.severity_class === "HIGH" ? "high" : "low"}
              />
            </View>

            <View style={styles.compareBox}>
              <Text style={styles.recTitle}>
                {consistencyFarmerTitle(latest.consistency_status)}
              </Text>
              <Text style={styles.meta}>
                {consistencyFarmerHint(latest.consistency_status)}
              </Text>
              {latest.similarity_score != null ? (
                <Text style={styles.meta}>
                  Similarity score: {formatScore(latest.similarity_score)}
                </Text>
              ) : null}
            </View>

            {previous ? (
              <View style={styles.compareBox}>
                <Text style={styles.recTitle}>Previous vs current</Text>
                <Text style={styles.meta}>
                  Previous severity: {formatScore(previous.severity_score)} ({previous.severity_class})
                </Text>
                <Text style={styles.meta}>
                  Current severity: {formatScore(latest.severity_score)} ({latest.severity_class})
                </Text>
                <Text style={styles.trendLine}>{trendFarmerLabel(latest.trend)}</Text>
              </View>
            ) : (
              <View style={styles.compareBox}>
                <Text style={styles.recTitle}>Baseline set</Text>
                <Text style={styles.meta}>
                  No previous observation yet. Future uploads will check visual consistency and
                  show trend (Stable / Improving / Worsening / Recovered).
                </Text>
              </View>
            )}

            {weatherText ? (
              <View style={styles.recBox}>
                <Text style={styles.recTitle}>Weather context</Text>
                <Text style={styles.recItem}>{weatherText}</Text>
                {weatherDetails ? (
                  <Text style={styles.meta}>
                    Temp {String(weatherDetails.temperature ?? "n/a")}°C · Humidity{" "}
                    {String(weatherDetails.humidity ?? "n/a")}% · Rain{" "}
                    {String(weatherDetails.rainfall ?? "n/a")}
                  </Text>
                ) : null}
              </View>
            ) : null}

            {status.latest_recommendation ? (
              <View style={styles.guidanceBox}>
                <Text style={styles.guidanceTitle}>
                  {String(status.latest_recommendation.title ?? "Monitoring guidance")}
                </Text>
                <Text style={styles.meta}>
                  Monitoring tips only — not a treatment prescription.
                </Text>
                {Array.isArray(status.latest_recommendation.actions)
                  ? status.latest_recommendation.actions.map((a, i) => (
                      <Text key={i} style={styles.recItem}>
                        • {String(a)}
                      </Text>
                    ))
                  : null}
              </View>
            ) : null}

            <Text style={styles.overallLine}>
              Case status: {trendFarmerLabel(status.overall_status)}
            </Text>
          </View>
        ) : status ? (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Monitoring case ready</Text>
            <Text style={styles.meta}>Monitoring Case ID: {status.case_id}</Text>
            <Text style={styles.meta}>
              No observations yet — upload Observation 1 to set the baseline.
            </Text>
          </View>
        ) : null}

        {observations.length > 0 ? (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Observation history</Text>
            {observations.map((o, index) => (
              <View key={o.observation_id} style={styles.historyRow}>
                <Text style={styles.historyTitle}>
                  Observation {index + 1}
                  {index === 0 || o.consistency_status === "BASELINE" ? " · BASELINE" : ""}
                </Text>
                <Text style={styles.meta}>{new Date(o.created_at).toLocaleString()}</Text>
                <Text style={styles.meta}>Disease: {formatDiseaseName(o.disease)}</Text>
                <Text style={styles.meta}>
                  Severity {o.severity_class} · P(HIGH) {formatScore(o.severity_score)}
                </Text>
                <Text style={styles.meta}>
                  {consistencyFarmerTitle(o.consistency_status)}
                  {o.similarity_score != null
                    ? ` · similarity ${formatScore(o.similarity_score)}`
                    : ""}
                </Text>
                <Text style={styles.meta}>{trendFarmerLabel(o.trend)}</Text>
              </View>
            ))}
          </View>
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: palette.bg },
  content: { padding: 16, paddingBottom: 40 },
  title: { color: palette.textPrimary, fontSize: 22, fontWeight: "700" },
  subtitle: { color: palette.textMuted, marginTop: 6, marginBottom: 16, lineHeight: 20 },
  row: { flexDirection: "row", gap: 8, marginBottom: 12, flexWrap: "wrap" },
  rowWrap: { flexDirection: "row", flexWrap: "wrap", gap: 8, marginBottom: 12 },
  weatherToggleRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    marginBottom: 14,
  },
  chip: {
    borderWidth: 1,
    borderColor: palette.cardBorder,
    borderRadius: 999,
    paddingHorizontal: 14,
    paddingVertical: 8,
    backgroundColor: palette.card,
  },
  chipActive: { borderColor: palette.accent, backgroundColor: palette.accentDim },
  chipText: { color: palette.textMuted, fontWeight: "600" },
  chipTextActive: { color: palette.textPrimary },
  primaryBtn: {
    backgroundColor: palette.accent,
    borderRadius: 12,
    paddingVertical: 14,
    paddingHorizontal: 12,
    alignItems: "center",
    marginBottom: 8,
    flexGrow: 1,
  },
  primaryBtnText: { color: "#04210f", fontWeight: "700" },
  secondaryBtn: {
    borderWidth: 1,
    borderColor: palette.cardBorder,
    borderRadius: 12,
    paddingVertical: 14,
    paddingHorizontal: 12,
    alignItems: "center",
    marginTop: 4,
    flexGrow: 1,
  },
  secondaryBtnText: { color: palette.textPrimary, fontWeight: "600" },
  overrideBtn: {
    borderWidth: 1,
    borderColor: severityColors.high.main,
    borderRadius: 12,
    paddingVertical: 14,
    paddingHorizontal: 12,
    alignItems: "center",
    marginTop: 4,
    flexGrow: 1,
  },
  overrideBtnText: { color: severityColors.high.main, fontWeight: "600" },
  caseBox: {
    marginBottom: 12,
    padding: 12,
    borderRadius: 12,
    backgroundColor: palette.bgElevated,
    borderWidth: 1,
    borderColor: palette.cardBorder,
  },
  caseLabel: { color: palette.textMuted, fontSize: 12, fontWeight: "600" },
  caseValue: { color: palette.infoText, fontWeight: "700", marginTop: 2 },
  sectionLabel: { color: palette.textMuted, marginBottom: 8, fontWeight: "600" },
  message: { color: palette.infoText, marginTop: 10, lineHeight: 20 },
  confirmBox: {
    marginTop: 12,
    backgroundColor: palette.infoBanner,
    borderRadius: 12,
    padding: 12,
  },
  confirmTitle: { color: palette.infoText, fontWeight: "700", marginBottom: 6 },
  mismatchBox: {
    marginTop: 12,
    backgroundColor: severityColors.high.badgeBg,
    borderRadius: 12,
    padding: 12,
    borderWidth: 1,
    borderColor: severityColors.high.main,
  },
  mismatchTitle: { color: severityColors.high.main, fontWeight: "700", marginBottom: 6 },
  mismatchAdvice: {
    color: severityColors.high.main,
    fontWeight: "600",
    marginTop: 8,
    marginBottom: 4,
    lineHeight: 18,
  },
  card: {
    marginTop: 16,
    backgroundColor: palette.card,
    borderColor: palette.cardBorder,
    borderWidth: 1,
    borderRadius: 16,
    padding: 16,
  },
  cardTitle: { color: palette.textPrimary, fontSize: 16, fontWeight: "700", marginBottom: 8 },
  resultGrid: { marginBottom: 4 },
  resultKey: { color: palette.textMuted, marginTop: 8, fontSize: 12, fontWeight: "600" },
  resultVal: { color: palette.textPrimary, marginTop: 2, fontSize: 15, fontWeight: "600" },
  meta: { color: palette.textMuted, marginTop: 4, lineHeight: 18 },
  gaugeWrap: { alignItems: "center", marginTop: 8 },
  compareBox: {
    marginTop: 12,
    borderTopWidth: 1,
    borderTopColor: palette.divider,
    paddingTop: 10,
  },
  trendLine: {
    color: palette.textPrimary,
    fontWeight: "700",
    marginTop: 8,
    lineHeight: 20,
  },
  overallLine: {
    color: palette.textMuted,
    marginTop: 14,
    fontSize: 12,
    lineHeight: 18,
  },
  recBox: {
    marginTop: 12,
    backgroundColor: palette.infoBanner,
    borderRadius: 12,
    padding: 12,
  },
  guidanceBox: {
    marginTop: 12,
    backgroundColor: severityColors.high.badgeBg,
    borderRadius: 12,
    padding: 12,
    borderWidth: 1,
    borderColor: severityColors.high.main,
  },
  guidanceTitle: { color: severityColors.high.main, fontWeight: "700", marginBottom: 6 },
  recTitle: { color: palette.infoText, fontWeight: "700", marginBottom: 6 },
  recItem: { color: palette.textPrimary, marginTop: 4, lineHeight: 18 },
  historyRow: {
    borderTopWidth: 1,
    borderTopColor: palette.divider,
    paddingTop: 10,
    marginTop: 10,
  },
  historyTitle: { color: palette.textPrimary, fontWeight: "600" },
});
