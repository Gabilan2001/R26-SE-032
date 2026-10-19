import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { palette, severityColors } from "../../theme/colors";
import { recoveryHeadline, recoveryTone } from "../../utils/observationLabels";

type Props = {
  trend: string | null | undefined;
};

export function RecoveryStatusCard({ trend }: Props) {
  const tone = recoveryTone(trend);
  const colors =
    tone === "success" || tone === "positive"
      ? { border: palette.accent, bg: palette.accentDim, text: palette.accent }
      : tone === "warning"
        ? {
            border: severityColors.high.main,
            bg: severityColors.high.badgeBg,
            text: severityColors.high.main,
          }
        : { border: palette.cardBorder, bg: palette.bgElevated, text: palette.textPrimary };

  return (
    <View style={[styles.card, { borderColor: colors.border, backgroundColor: colors.bg }]}>
      <Text style={styles.kicker}>RECOVERY STATUS</Text>
      <Text style={[styles.headline, { color: colors.text }]}>
        {recoveryHeadline(trend)}
      </Text>
      <Text style={styles.hint}>
        Observation-based trend from the backend. 
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: 18,
    borderWidth: 1.5,
    padding: 20,
    marginTop: 14,
  },
  kicker: {
    color: palette.textMuted,
    fontSize: 11,
    letterSpacing: 1.2,
    fontWeight: "700",
  },
  headline: { fontSize: 24, fontWeight: "800", marginTop: 8, lineHeight: 30 },
  hint: { color: palette.textMuted, marginTop: 10, lineHeight: 18, fontSize: 12 },
});
