import React, { useEffect, useRef, useState } from "react";
import {
  Alert,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { StatusBar } from "expo-status-bar";
import * as ImagePicker from "expo-image-picker";
import {
  getCaseStatus,
  listObservations,
  uploadObservation,
  type CropPart,
  type CaseStatus,
  type MonitoringCase,
  type Observation,
} from "../../api/observations";
import { LeafScanAppHeader } from "../../components/LeafScanAppHeader";
import {
  ImageQualityCard,
  LocationAccessCard,
  MismatchConfirmationModal,
  ObservationProgress,
  ObservationUploadCard,
} from "../../components/monitoring";
import { MODALITY } from "../../config/modality";
import { checkImageQuality, type ImageQualityResult } from "../../api/imageQuality";
import { palette } from "../../theme/colors";
import { formatGateRejection } from "../../utils/gateMessages";
import {
  formatLocationSummary,
  type ObservationLocationSelection,
} from "../../utils/locationCapture";

type Props = {
  caseData: MonitoringCase;
  cropPart: CropPart;
  observationNumber: number;
  attachWeather: boolean;
  savedLocation?: ObservationLocationSelection | null;
  onLocationCommitted?: (location: ObservationLocationSelection | null) => void;
  onSuccess: (payload: {
    observation: Observation;
    status: CaseStatus;
    observations: Observation[];
    imageUri: string;
    location?: ObservationLocationSelection | null;
  }) => void;
};

type Pending = {
  uri: string;
  consistency: string;
  similarity?: number | null;
  reason?: string;
};

export function ObservationUploadScreen({
  caseData,
  cropPart,
  observationNumber,
  attachWeather,
  savedLocation = null,
  onLocationCommitted,
  onSuccess,
}: Props) {
  const isFirstObservation = observationNumber === 1;
  const [previewUri, setPreviewUri] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [qualityLoading, setQualityLoading] = useState(false);
  const [qualityResult, setQualityResult] = useState<ImageQualityResult | null>(null);
  const [qualitySkipped, setQualitySkipped] = useState(false);
  const [validationMessage, setValidationMessage] = useState<string | null>(null);
  const [pending, setPending] = useState<Pending | null>(null);
  const [location, setLocation] = useState<ObservationLocationSelection | null>(
    () => (isFirstObservation ? null : savedLocation)
  );
  const uploadingRef = useRef(false);
  const cfg = MODALITY[cropPart];

  useEffect(() => {
    if (!isFirstObservation && savedLocation) {
      setLocation(savedLocation);
    }
  }, [isFirstObservation, savedLocation]);

  const runQualityCheck = async (uri: string) => {
    setQualityLoading(true);
    setQualityResult(null);
    setQualitySkipped(false);
    try {
      const result = await checkImageQuality(uri, cropPart);
      setQualityResult(result);
    } catch {
      setQualitySkipped(true);
    } finally {
      setQualityLoading(false);
    }
  };

  const pickImage = async () => {
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
    const uri = picked.assets[0].uri;
    setPreviewUri(uri);
    setValidationMessage(null);
    setQualityResult(null);
    setQualitySkipped(false);
    await runQualityCheck(uri);
  };

  const activeLocation = isFirstObservation ? location : savedLocation ?? location;

  const buildLocationParams = () => {
    if (!activeLocation || activeLocation.source === "none") {
      return {};
    }
    if (
      activeLocation.source === "manual" &&
      activeLocation.label &&
      activeLocation.latitude == null
    ) {
      return {
        locationLabel: activeLocation.label,
        locationSource: "manual" as const,
        area: activeLocation.area,
        district: activeLocation.district,
        province: activeLocation.province,
      };
    }
    return {
      latitude: activeLocation.latitude,
      longitude: activeLocation.longitude,
      area: activeLocation.area,
      district: activeLocation.district,
      province: activeLocation.province,
      locationLabel: activeLocation.label,
      locationSource: activeLocation.source,
    };
  };

  const runUpload = async (uri: string, confirmSameCase: boolean) => {
    if (uploadingRef.current) return;
    uploadingRef.current = true;
    setLoading(true);
    setValidationMessage("Validating image…");
    try {
      const result = await uploadObservation({
        caseId: caseData.case_id,
        cropPart,
        disease: cfg.defaultDisease,
        uri,
        confirmSameCase,
        ...buildLocationParams(),
      });

      if (!result.accepted) {
        if (result.image_valid === false) {
          setPending(null);
          setValidationMessage(
            formatGateRejection(cropPart, result.rejection_reason)
          );
          return;
        }

        const consistency = String(result.consistency_status ?? "");
        if (
          !confirmSameCase &&
          (consistency === "POSSIBLE_MATCH" || consistency === "MISMATCH")
        ) {
          setPending({
            uri,
            consistency,
            similarity:
              typeof result.similarity_score === "number" ? result.similarity_score : null,
            reason: String(result.rejection_reason ?? ""),
          });
          setValidationMessage(null);
          return;
        }

        setValidationMessage(String(result.rejection_reason ?? "Observation rejected."));
        return;
      }

      const obs = result.observation as Observation;
      const [status, listed] = await Promise.all([
        getCaseStatus(caseData.case_id),
        listObservations(caseData.case_id),
      ]);
      setPending(null);
      setValidationMessage(null);
      const committedLocation = isFirstObservation ? location : activeLocation;
      if (isFirstObservation) {
        onLocationCommitted?.(committedLocation);
      }
      onSuccess({
        observation: obs,
        status,
        observations: listed.observations,
        imageUri: uri,
        location: committedLocation,
      });
    } catch (e) {
      const text = String(e);
      if (cropPart === "FRUIT" && (text.includes("503") || text.toLowerCase().includes("fruit"))) {
        Alert.alert(
          "Fruit model unavailable",
          cfg.pendingMessage ??
            "Fruit severity CNN could not be loaded. Check FRUIT_SEVERITY_MODEL_PATH."
        );
      } else {
        Alert.alert("Upload failed", "Could not upload this observation. Please try again.");
      }
      setValidationMessage(null);
    } finally {
      uploadingRef.current = false;
      setLoading(false);
    }
  };

  const reusedSummary = formatLocationSummary(activeLocation);

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar style="light" />
      <LeafScanAppHeader />
      <ScrollView contentContainerStyle={styles.content}>
        <ObservationProgress current={observationNumber} />
        <Text style={styles.title}>Observation {observationNumber}</Text>
        <Text style={styles.meta}>Case ID: {caseData.case_id}</Text>
        <Text style={styles.meta}>{cfg.shortLabel} · disease context: external default</Text>

        {isFirstObservation ? (
          <LocationAccessCard
            value={location}
            onChange={setLocation}
            attachWeather={attachWeather}
          />
        ) : attachWeather ? (
          <View style={styles.reuseCard}>
            <Text style={styles.reuseTitle}>Location for weather</Text>
            <Text style={styles.reuseBody}>
              {reusedSummary
                ? `Using location from Observation 1: ${reusedSummary}`
                : "No location was set on Observation 1, so weather may be unavailable for this upload."}
            </Text>
          </View>
        ) : null}

        <ObservationUploadCard
          observationNumber={observationNumber}
          dateLabel={new Date().toLocaleDateString(undefined, {
            weekday: "short",
            year: "numeric",
            month: "short",
            day: "numeric",
          })}
          previewUri={previewUri}
          validationMessage={validationMessage}
          loading={loading}
          onPick={pickImage}
          onUpload={() => {
            if (!previewUri) return;
            void runUpload(previewUri, false);
          }}
        />

        {previewUri && !loading ? (
          <ImageQualityCard
            result={qualityResult}
            loading={qualityLoading}
            skipped={qualitySkipped}
          />
        ) : null}

        <Pressable
          style={styles.link}
          onPress={() =>
            Alert.alert(
              "Disease context",
              "Disease identification belongs to another component. This app sends a modality default required by the observation API."
            )
          }
        >
          <Text style={styles.linkText}>About disease context</Text>
        </Pressable>
      </ScrollView>

      <MismatchConfirmationModal
        visible={!!pending}
        consistency={pending?.consistency ?? ""}
        similarity={pending?.similarity}
        reason={pending?.reason}
        loading={loading}
        onConfirm={() => {
          if (!pending) return;
          void runUpload(pending.uri, true);
        }}
        onCancel={() => {
          setPending(null);
          setValidationMessage("Upload cancelled.");
        }}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: palette.bg },
  content: { padding: 18, paddingBottom: 40 },
  title: { color: palette.textPrimary, fontSize: 22, fontWeight: "800", marginBottom: 4 },
  meta: { color: palette.textMuted, marginBottom: 4 },
  reuseCard: {
    marginTop: 12,
    marginBottom: 4,
    backgroundColor: palette.card,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: palette.cardBorder,
    padding: 14,
  },
  reuseTitle: { color: palette.textPrimary, fontWeight: "700", fontSize: 14 },
  reuseBody: { color: palette.textMuted, marginTop: 6, lineHeight: 18 },
  link: { marginTop: 16, alignItems: "center" },
  linkText: { color: palette.infoText, fontWeight: "600" },
});
