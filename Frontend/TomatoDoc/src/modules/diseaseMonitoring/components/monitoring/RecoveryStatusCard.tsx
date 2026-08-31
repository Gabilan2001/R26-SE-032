import React, { useMemo } from "react";
import { View, Text, StyleSheet } from "react-native";
import { severityColors, type MonitoringPalette } from "../../theme/colors";
import { useMonitoringPalette } from "../../theme/MonitoringThemeContext";
import { recoveryHeadline, recoveryTone } from "../../utils/observationLabels";

type Props = {
  trend: string | null | undefined;
};

export function RecoveryStatusCard({ trend }: Props) {
  const p = useMonitoringPalette();
  const styles = useMemo(() => makeStyles(p), [p]);
  const tone = recoveryTone(trend);
  const colors =
    tone === "success" || tone === "positive"
      ? { border: p.accent, bg: p.accentDim, text: p.accent }
      : tone === "warning"
        ? {
            border: severityColors.high.main,
            bg: severityColors.high.badgeBg,
            text: severityColors.high.main,
          }
        : { border: p.cardBorder, bg: p.bgElevated, text: p.textPrimary };

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

function makeStyles(p: MonitoringPalette) {
  return StyleSheet.create({
    card: {
      borderRadius: 18,
      borderWidth: 1.5,
      padding: 20,
      marginTop: 14,
    },
    kicker: {
      color: p.textMuted,
      fontSize: 11,
      letterSpacing: 1.2,
      fontWeight: "700",
    },
    headline: { fontSize: 24, fontWeight: "800", marginTop: 8, lineHeight: 30 },
    hint: { color: p.textMuted, marginTop: 10, lineHeight: 18, fontSize: 12 },
  });
}
