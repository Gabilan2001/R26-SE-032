import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { CLASS_COLORS } from '../constants/classColors';

// Small colored pill showing a disease class name -- shared between
// DiseaseResultScreen (scan result) and DiseaseHistoryScreen (past scans,
// via `compact` for the denser list). Pure visual styling here is
// intentionally left as-is pending the planned screen redesign; only the
// duplicated markup/logic was worth pulling out now.
export default function DiseaseChip({ name, compact = false }) {
  const color = CLASS_COLORS[name] || '#666666';
  return (
    <View style={[styles.chip, compact && styles.chipCompact, { borderColor: color + '55', backgroundColor: color + '18' }]}>
      <View style={[styles.dot, compact && styles.dotCompact, { backgroundColor: color }]} />
      <Text style={[styles.txt, compact && styles.txtCompact, { color }]}>
        {name.replace('_', ' ')}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  chip:        { flexDirection: 'row', alignItems: 'center', gap: 6, borderWidth: 1, borderRadius: 100, paddingHorizontal: 11, paddingVertical: 5 },
  chipCompact: { gap: 5, paddingHorizontal: 9, paddingVertical: 4 },
  dot:         { width: 6, height: 6, borderRadius: 3 },
  dotCompact:  { width: 5, height: 5 },
  txt:         { fontSize: 11, fontWeight: '700' },
  txtCompact:  { fontSize: 10 },
});
