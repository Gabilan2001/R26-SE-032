import React from "react";
import { Modal, Pressable, StyleSheet, Text, View } from "react-native";
import { palette } from "../../theme/colors";
import { formatDiseaseName } from "../../utils/observationLabels";
import {
  formatLocationContextLine,
  type ObservationLocationSelection,
} from "../../utils/locationCapture";

type Props = {
  visible: boolean;
  caseId: string;
  disease: string;
  cropPartLabel?: string;
  location?: ObservationLocationSelection | null;
  onClose: () => void;
};

export function DiseaseContextModal({
  visible,
  caseId,
  disease,
  cropPartLabel,
  location,
  onClose,
}: Props) {
  const locationLine = formatLocationContextLine(location);

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <View style={styles.backdrop}>
        <View style={styles.sheet}>
          <Text style={styles.title}>Disease context</Text>
          <Text style={styles.body}>
            Summary for this monitoring case after your first observation.
          </Text>

          <View style={styles.row}>
            <Text style={styles.label}>Case ID</Text>
            <Text style={styles.value}>{caseId}</Text>
          </View>

          {cropPartLabel ? (
            <View style={styles.row}>
              <Text style={styles.label}>Crop part</Text>
              <Text style={styles.value}>{cropPartLabel}</Text>
            </View>
          ) : null}

          <View style={styles.row}>
            <Text style={styles.label}>Disease</Text>
            <Text style={styles.valueHighlight}>{formatDiseaseName(disease)}</Text>
          </View>

          <View style={[styles.locationBox, locationLine.available ? styles.locationOk : styles.locationMissing]}>
            <Text style={styles.locationLabel}>Location</Text>
            <Text style={locationLine.available ? styles.locationTextOk : styles.locationTextMissing}>
              {locationLine.text}
            </Text>
          </View>

          <Text style={styles.note}>
            Disease label comes from your monitoring case - not detected in this module.
          </Text>

          <Pressable style={styles.primary} onPress={onClose}>
            <Text style={styles.primaryText}>OK</Text>
          </Pressable>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.65)",
    justifyContent: "center",
    padding: 20,
  },
  sheet: {
    backgroundColor: palette.bgElevated,
    borderRadius: 18,
    padding: 20,
    borderWidth: 1,
    borderColor: palette.cardBorder,
  },
  title: { color: palette.textPrimary, fontSize: 18, fontWeight: "800" },
  body: { color: palette.textMuted, marginTop: 8, lineHeight: 20 },
  row: { marginTop: 14 },
  label: { color: palette.textMuted, fontSize: 12, fontWeight: "600" },
  value: { color: palette.textPrimary, marginTop: 4, fontWeight: "700" },
  valueHighlight: { color: palette.accent, marginTop: 4, fontWeight: "800", fontSize: 16 },
  locationBox: {
    marginTop: 16,
    padding: 12,
    borderRadius: 12,
    borderWidth: 1,
  },
  locationOk: {
    backgroundColor: "rgba(74,223,111,0.1)",
    borderColor: "rgba(74,223,111,0.35)",
  },
  locationMissing: {
    backgroundColor: "rgba(255,179,71,0.1)",
    borderColor: "rgba(255,179,71,0.35)",
  },
  locationLabel: { color: palette.textMuted, fontSize: 12, fontWeight: "700" },
  locationTextOk: { color: "#7CFF9C", marginTop: 6, lineHeight: 18, fontWeight: "600" },
  locationTextMissing: { color: "#FFB347", marginTop: 6, lineHeight: 18, fontWeight: "600" },
  note: { color: palette.textMuted, marginTop: 14, fontSize: 12, lineHeight: 18 },
  primary: {
    marginTop: 18,
    backgroundColor: palette.accent,
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
  },
  primaryText: { color: palette.onAccent, fontWeight: "800" },
});
