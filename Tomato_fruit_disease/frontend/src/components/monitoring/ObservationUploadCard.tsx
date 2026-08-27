import React from "react";
import { View, Text, StyleSheet, Pressable, Image, ActivityIndicator } from "react-native";
import { palette } from "../../theme/colors";

type Props = {
  observationNumber: number;
  dateLabel: string;
  previewUri: string | null;
  validationMessage: string | null;
  loading: boolean;
  disabled?: boolean;
  onPick: () => void;
  onUpload: () => void;
};

export function ObservationUploadCard({
  observationNumber,
  dateLabel,
  previewUri,
  validationMessage,
  loading,
  disabled,
  onPick,
  onUpload,
}: Props) {
  return (
    <View style={styles.card}>
      <Text style={styles.kicker}>OBSERVATION {observationNumber}</Text>
      <Text style={styles.date}>{dateLabel}</Text>

      {previewUri ? (
        <Image source={{ uri: previewUri }} style={styles.preview} resizeMode="cover" />
      ) : (
        <View style={styles.emptyPreview}>
          <Text style={styles.emptyText}>No image selected</Text>
        </View>
      )}

      {validationMessage ? (
        <Text style={styles.validation}>{validationMessage}</Text>
      ) : null}

      <Pressable
        style={[styles.secondary, disabled && styles.disabled]}
        onPress={onPick}
        disabled={disabled || loading}
      >
        <Text style={styles.secondaryText}>
          {previewUri ? "Change image" : "Select image"}
        </Text>
      </Pressable>

      <Pressable
        style={[styles.primary, (!previewUri || disabled) && styles.disabled]}
        onPress={onUpload}
        disabled={!previewUri || disabled || loading}
      >
        {loading ? (
          <ActivityIndicator color="#04210f" />
        ) : (
          <Text style={styles.primaryText}>Upload observation</Text>
        )}
      </Pressable>
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
  },
  kicker: {
    color: palette.textMuted,
    fontSize: 11,
    letterSpacing: 1.2,
    fontWeight: "700",
  },
  date: { color: palette.textPrimary, fontSize: 16, fontWeight: "700", marginTop: 4 },
  preview: {
    width: "100%",
    height: 220,
    borderRadius: 12,
    marginTop: 14,
    backgroundColor: palette.bgElevated,
  },
  emptyPreview: {
    height: 160,
    borderRadius: 12,
    marginTop: 14,
    borderWidth: 1,
    borderColor: palette.cardBorder,
    borderStyle: "dashed",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: palette.bgElevated,
  },
  emptyText: { color: palette.textMuted },
  validation: { color: palette.infoText, marginTop: 10, lineHeight: 18 },
  primary: {
    marginTop: 12,
    backgroundColor: palette.accent,
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
  },
  primaryText: { color: "#04210f", fontWeight: "700" },
  secondary: {
    marginTop: 12,
    borderWidth: 1,
    borderColor: palette.cardBorder,
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
  },
  secondaryText: { color: palette.textPrimary, fontWeight: "600" },
  disabled: { opacity: 0.45 },
});
