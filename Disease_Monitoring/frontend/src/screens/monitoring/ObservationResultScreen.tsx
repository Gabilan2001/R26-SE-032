import React, { useState } from "react";
import {
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { StatusBar } from "expo-status-bar";
import type { CropPart, Observation } from "../../api/observations";
import { LeafScanAppHeader } from "../../components/LeafScanAppHeader";
import {
  DiseaseContextModal,
  ObservationProgress,
  ObservationResultCard,
} from "../../components/monitoring";
import { NEXT_OBSERVATION_GUIDANCE, TARGET_OBSERVATIONS, MODALITY } from "../../config/modality";
import { palette } from "../../theme/colors";
import type { ObservationLocationSelection } from "../../utils/locationCapture";

type Props = {
  caseId: string;
  observationNumber: number;
  observation: Observation;
  previousObservation?: Observation | null;
  imageUri?: string | null;
  cropPart?: CropPart;
  caseLocation?: ObservationLocationSelection | null;
  onBack?: () => void;
  onNextObservation: () => void;
  onViewOverall: () => void;
};

export function ObservationResultScreen({
  caseId,
  observationNumber,
  observation,
  previousObservation,
  imageUri,
  cropPart,
  caseLocation = null,
  onBack,
  onNextObservation,
  onViewOverall,
}: Props) {
  const [contextOpen, setContextOpen] = useState(false);
  const complete = observationNumber >= TARGET_OBSERVATIONS;
  const cfg = cropPart ? MODALITY[cropPart] : null;

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar style="light" />
      <LeafScanAppHeader onBack={onBack} />
      <ScrollView contentContainerStyle={styles.content}>
        <ObservationProgress current={observationNumber} />

        <ObservationResultCard
          observationNumber={observationNumber}
          observation={observation}
          previousObservation={previousObservation}
          cropPart={cropPart}
          imageUri={imageUri}
        />

        {observation.recommendation ? (
          <View style={styles.guideBox}>
            <Text style={styles.guideTitle}>
              {String(observation.recommendation.title ?? "Monitoring guidance")}
            </Text>
            {Array.isArray(observation.recommendation.actions)
              ? observation.recommendation.actions.map((a, i) => (
                  <Text key={i} style={styles.guideItem}>
                    • {String(a)}
                  </Text>
                ))
              : null}
          </View>
        ) : null}

        <View style={styles.nextCard}>
          <Text style={styles.nextTitle}>
            {complete ? "Monitoring sequence complete" : "Next observation"}
          </Text>
          <Text style={styles.nextBody}>{NEXT_OBSERVATION_GUIDANCE}</Text>

          {complete ? (
            <Pressable style={styles.primary} onPress={onViewOverall}>
              <Text style={styles.primaryText}>View Overall Monitoring</Text>
            </Pressable>
          ) : (
            <Pressable style={styles.primary} onPress={onNextObservation}>
              <Text style={styles.primaryText}>
                Upload Observation {observationNumber + 1}
              </Text>
            </Pressable>
          )}
        </View>

        <Pressable style={styles.link} onPress={() => setContextOpen(true)}>
          <Text style={styles.linkText}>About disease context</Text>
        </Pressable>

        <Text style={styles.caseFootnote}>Case reference: {caseId}</Text>
      </ScrollView>

      <DiseaseContextModal
        visible={contextOpen}
        caseId={caseId}
        disease={observation.disease}
        cropPartLabel={cfg?.shortLabel}
        location={caseLocation}
        onClose={() => setContextOpen(false)}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: palette.bg },
  content: { padding: 18, paddingBottom: 40 },
  guideBox: {
    marginTop: 12,
    backgroundColor: "#2a1012",
    borderRadius: 14,
    padding: 14,
    borderWidth: 1,
    borderColor: "#FF6B6B",
  },
  guideTitle: { color: "#FF6B6B", fontWeight: "700" },
  guideHint: { color: palette.textMuted, marginTop: 4, fontSize: 12 },
  guideItem: { color: palette.textPrimary, marginTop: 6, lineHeight: 18 },
  nextCard: {
    marginTop: 16,
    backgroundColor: palette.card,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: palette.cardBorder,
    padding: 16,
  },
  nextTitle: { color: palette.textPrimary, fontWeight: "800", fontSize: 16 },
  nextBody: { color: palette.textMuted, marginTop: 8, lineHeight: 20 },
  primary: {
    marginTop: 16,
    backgroundColor: palette.accent,
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
  },
  primaryText: { color: "#04210f", fontWeight: "800" },
  link: { marginTop: 16, alignItems: "center" },
  linkText: { color: palette.infoText, fontWeight: "600" },
  caseFootnote: {
    color: palette.textMuted,
    fontSize: 11,
    marginTop: 14,
    textAlign: "center",
  },
});
