import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { palette } from "../../theme/colors";

type LocationPayload = {
  area?: string;
  district?: string;
  province?: string;
  source?: string;
};

type Props = {
  location?: LocationPayload | null;
};

export function LocationObservationCard({ location }: Props) {
  if (!location?.area && !location?.district && !location?.province) {
    return null;
  }

  const lines = [location.area, location.district, location.province].filter(Boolean);

  return (
    <View style={styles.card}>
      <Text style={styles.title}>Location</Text>
      <Text style={styles.value}>{lines.join(" · ")}</Text>
      {location.source ? (
        <Text style={styles.meta}>
          {location.source === "gps" ? "From device GPS" : "Selected manually"}
        </Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    marginTop: 12,
    backgroundColor: palette.card,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: palette.cardBorder,
    padding: 16,
  },
  title: { color: palette.textMuted, fontSize: 12, fontWeight: "700", letterSpacing: 0.8 },
  value: { color: palette.textPrimary, marginTop: 8, fontSize: 16, fontWeight: "700" },
  meta: { color: palette.textMuted, marginTop: 6, fontSize: 12 },
});
