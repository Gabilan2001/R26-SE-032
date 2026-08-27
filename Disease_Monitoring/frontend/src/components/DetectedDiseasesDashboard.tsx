import React, { useState } from "react";
import { StyleSheet, ScrollView } from "react-native";
import { DiseaseCard } from "./DiseaseCard";
import { DetectedDiseasesSection } from "./DetectedDiseasesSection";
import { palette } from "../theme/colors";
import type { DayKey, DiseaseTrack } from "../types/disease";

export type { DayKey, DiseaseTrack } from "../types/disease";

type Props = {
  diseases: DiseaseTrack[];
  /** Optional: lift day state per disease from parent */
  initialDayById?: Record<string, DayKey>;
};

export function DetectedDiseasesDashboard({
  diseases,
  initialDayById,
}: Props) {
  const [dayById, setDayById] = useState<Record<string, DayKey>>(() => {
    const init: Record<string, DayKey> = {};
    for (const d of diseases) {
      init[d.id] = initialDayById?.[d.id] ?? "d3";
    }
    return init;
  });

  return (
    <ScrollView
      style={styles.scroll}
      contentContainerStyle={styles.scrollContent}
      showsVerticalScrollIndicator={false}
    >
      <DetectedDiseasesSection />
      {diseases.map((d) => (
        <React.Fragment key={d.id}>
          <DiseaseCard
            disease={d}
            selectedDay={dayById[d.id] ?? "d3"}
            onSelectDay={(day) =>
              setDayById((prev: Record<string, DayKey>) => ({
                ...prev,
                [d.id]: day,
              }))
            }
          />
        </React.Fragment>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scroll: {
    flex: 1,
    backgroundColor: palette.bg,
  },
  scrollContent: {
    paddingHorizontal: 18,
    paddingBottom: 32,
    paddingTop: 8,
  },
});
