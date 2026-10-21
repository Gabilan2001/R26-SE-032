import React from "react";
import { Modal, View, Text, StyleSheet, Pressable } from "react-native";
import { palette, severityColors } from "../../theme/colors";
import { formatScore } from "../../utils/observationLabels";

type Props = {
  visible: boolean;
  consistency: string;
  similarity?: number | null;
  reason?: string | null;
  loading?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
};

/** Short mismatch-only alert. POSSIBLE_MATCH is accepted automatically by the backend. */
export function MismatchConfirmationModal({
  visible,
  consistency,
  similarity,
  loading,
  onConfirm,
  onCancel,
}: Props) {
  if (consistency !== "MISMATCH") {
    return null;
  }

  return (
    <Modal visible={visible} transparent animationType="fade">
      <View style={styles.backdrop}>
        <View style={styles.sheet}>
          <Text style={styles.title}>Mismatch alert</Text>
          <Text style={styles.body}>
            This photo looks different from the previous observation.
          </Text>
          {similarity != null ? (
            <Text style={styles.meta}>Similarity: {formatScore(similarity)}</Text>
          ) : null}
          <Text style={styles.meta}>
            Confirm only if this is the same plant / monitoring case.
          </Text>

          <Pressable
            style={[styles.primary, loading && styles.disabled]}
            onPress={onConfirm}
            disabled={loading}
          >
            <Text style={styles.primaryText}>Confirm & Continue</Text>
          </Pressable>
          <Pressable style={styles.secondary} onPress={onCancel} disabled={loading}>
            <Text style={styles.secondaryText}>Cancel</Text>
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
    justifyContent: "flex-end",
  },
  sheet: {
    backgroundColor: palette.bgElevated,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    borderTopWidth: 1,
    borderColor: severityColors.high.main,
  },
  title: { color: severityColors.high.main, fontSize: 18, fontWeight: "800" },
  body: { color: palette.textPrimary, marginTop: 10, lineHeight: 20 },
  meta: { color: palette.textMuted, marginTop: 8, lineHeight: 18 },
  primary: {
    marginTop: 18,
    backgroundColor: palette.accent,
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
  },
  primaryText: { color: "#04210f", fontWeight: "700" },
  secondary: {
    marginTop: 10,
    borderWidth: 1,
    borderColor: palette.cardBorder,
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
    marginBottom: 8,
  },
  secondaryText: { color: palette.textPrimary, fontWeight: "600" },
  disabled: { opacity: 0.5 },
});
