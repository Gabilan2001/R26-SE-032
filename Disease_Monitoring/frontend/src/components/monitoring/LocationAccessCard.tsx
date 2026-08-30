import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { fetchKnownLocations } from "../../api/locations";
import { palette } from "../../theme/colors";
import {
  formatLocationSummary,
  MANUAL_LOCATION_HINTS,
  manualLocationSelection,
  requestGpsLocation,
  type ObservationLocationSelection,
} from "../../utils/locationCapture";

type Props = {
  value: ObservationLocationSelection | null;
  onChange: (next: ObservationLocationSelection | null) => void;
  attachWeather: boolean;
};

export function LocationAccessCard({ value, onChange, attachWeather }: Props) {
  const [loading, setLoading] = useState(false);
  const [pickerOpen, setPickerOpen] = useState(false);
  const [options, setOptions] = useState<string[]>(Object.keys(MANUAL_LOCATION_HINTS));

  useEffect(() => {
    void fetchKnownLocations()
      .then(setOptions)
      .catch(() => setOptions(Object.keys(MANUAL_LOCATION_HINTS)));
  }, []);

  const summary = formatLocationSummary(value);

  const enableGps = async () => {
    setLoading(true);
    try {
      const gps = await requestGpsLocation();
      onChange(gps);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.card}>
      <Text style={styles.title}>Location access</Text>
      <Text style={styles.body}>
        {attachWeather
          ? "We use your location to retrieve local weather conditions for this observation."
          : "Optional — set your area so weather can be linked to this observation."}
      </Text>

      {summary ? (
        <View style={styles.summaryBox}>
          <Text style={styles.summaryLabel}>Selected location</Text>
          <Text style={styles.summaryValue}>{summary}</Text>
        </View>
      ) : (
        <Text style={styles.missing}>
          {attachWeather
            ? "No location yet — GPS, pick an area, or use Colombo default for weather."
            : "No location selected."}
        </Text>
      )}

      <View style={styles.actions}>
        <Pressable
          style={[styles.button, loading && styles.buttonDisabled]}
          onPress={() => void enableGps()}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color={palette.onAccent} size="small" />
          ) : (
            <Text style={styles.buttonText}>Enable location</Text>
          )}
        </Pressable>
        <Pressable style={styles.buttonSecondary} onPress={() => setPickerOpen(true)}>
          <Text style={styles.buttonSecondaryText}>Select manually</Text>
        </Pressable>
      </View>

      <Pressable
        onPress={() =>
          onChange(
            attachWeather
              ? manualLocationSelection("Colombo")
              : { source: "none" }
          )
        }
        style={styles.skip}
      >
        <Text style={styles.skipText}>
          {attachWeather
            ? "Use Colombo (default weather)"
            : "Continue without location"}
        </Text>
      </Pressable>

      <Modal visible={pickerOpen} animationType="slide" transparent>
        <View style={styles.modalBackdrop}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>Select your area</Text>
            <ScrollView style={styles.modalList}>
              {options.map((label) => (
                <Pressable
                  key={label}
                  style={styles.optionRow}
                  onPress={() => {
                    onChange(manualLocationSelection(label));
                    setPickerOpen(false);
                  }}
                >
                  <Text style={styles.optionText}>{label}</Text>
                </Pressable>
              ))}
            </ScrollView>
            <Pressable style={styles.modalClose} onPress={() => setPickerOpen(false)}>
              <Text style={styles.modalCloseText}>Cancel</Text>
            </Pressable>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: palette.card,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: palette.cardBorder,
    padding: 16,
    marginBottom: 16,
  },
  title: { color: palette.textPrimary, fontSize: 16, fontWeight: "800" },
  body: { color: palette.textMuted, marginTop: 8, lineHeight: 20 },
  summaryBox: {
    marginTop: 12,
    padding: 12,
    borderRadius: 10,
    backgroundColor: palette.bgElevated,
  },
  summaryLabel: { color: palette.textMuted, fontSize: 12, fontWeight: "600" },
  summaryValue: { color: palette.textPrimary, marginTop: 4, fontWeight: "700" },
  missing: { color: "#FFB347", marginTop: 12, lineHeight: 18 },
  actions: { flexDirection: "row", gap: 10, marginTop: 14 },
  button: {
    flex: 1,
    backgroundColor: palette.accent,
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: "center",
  },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: palette.onAccent, fontWeight: "800" },
  buttonSecondary: {
    flex: 1,
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: "center",
    borderWidth: 1,
    borderColor: palette.cardBorder,
  },
  buttonSecondaryText: { color: palette.textPrimary, fontWeight: "700" },
  skip: { marginTop: 12, alignItems: "center" },
  skipText: { color: palette.infoText, fontWeight: "600" },
  modalBackdrop: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.55)",
    justifyContent: "flex-end",
  },
  modalCard: {
    maxHeight: "70%",
    backgroundColor: palette.card,
    borderTopLeftRadius: 18,
    borderTopRightRadius: 18,
    padding: 18,
  },
  modalTitle: { color: palette.textPrimary, fontSize: 18, fontWeight: "800", marginBottom: 10 },
  modalList: { maxHeight: 360 },
  optionRow: {
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: palette.cardBorder,
  },
  optionText: { color: palette.textPrimary, fontWeight: "600" },
  modalClose: { marginTop: 12, alignItems: "center", paddingVertical: 10 },
  modalCloseText: { color: palette.textMuted, fontWeight: "700" },
});
