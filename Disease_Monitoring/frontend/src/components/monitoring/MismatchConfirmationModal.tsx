import React from "react";
import { Modal, View, Text, StyleSheet, Pressable } from "react-native";
import { palette, severityColors } from "../../theme/colors";
import {
  consistencyFarmerHint,
  consistencyFarmerTitle,
  formatScore,
} from "../../utils/observationLabels";

type Props = {
  visible: boolean;
  consistency: string;
  similarity?: number | null;
  reason?: string | null;
  loading?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
};

export function MismatchConfirmationModal({
  visible,
  consistency,
  similarity,
  reason,
  loading,
  onConfirm,
  onCancel,
}: Props) {
  const isMismatch = consistency === "MISMATCH";

  return (
    <Modal visible={visible} transparent animationType="fade">
      <View style={styles.backdrop}>
        <View style={[styles.sheet, isMismatch && styles.sheetWarn]}>
          <Text style={[styles.title, isMismatch && styles.titleWarn]}>
            {consistencyFarmerTitle(consistency)}
          </Text>
          <Text style={styles.body}>
            This image could not be confidently matched with the previous observation.
          </Text>
          <Text style={styles.body}>{consistencyFarmerHint(consistency)}</Text>
          {similarity != null ? (
            <Text style={styles.meta}>Similarity: {formatScore(similarity)}</Text>
          ) : null}
          {reason ? <Text style={styles.meta}>{reason}</Text> : null}

          {isMismatch ? (
            <Text style={styles.advice}>
              Recommended: start a new monitoring case unless you are sure this photo belongs here.
            </Text>
          ) : null}

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
    borderColor: palette.cardBorder,
  },
  sheetWarn: { borderColor: severityColors.high.main },
  title: { color: palette.infoText, fontSize: 18, fontWeight: "800" },
  titleWarn: { color: severityColors.high.main },
  body: { color: palette.textPrimary, marginTop: 10, lineHeight: 20 },
  meta: { color: palette.textMuted, marginTop: 8, lineHeight: 18 },
  advice: {
    color: severityColors.high.main,
    marginTop: 12,
    fontWeight: "600",
    lineHeight: 18,
  },
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
