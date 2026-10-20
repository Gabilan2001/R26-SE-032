import React from 'react';
import { Animated, StyleSheet, View } from 'react-native';
import { Card, Chip, ProgressBar, Surface, Text } from 'react-native-paper';
import { colors } from '../constants/colors';
import { computeSeverity } from '../utils/severity';

export default function ResultCard({ result }) {
  const isHealthy = result.class === 'Healthy';
  const confidence = Number(result.confidence || 0);
  const confidenceBand = confidence >= 85 ? 'High Confidence' : confidence >= 70 ? 'Moderate Confidence' : 'Retake Recommended';
  const severity = computeSeverity(result, 'nutrient');
  const fade = React.useRef(new Animated.Value(0)).current;

  React.useEffect(() => {
    Animated.timing(fade, { toValue: 1, duration: 450, useNativeDriver: true }).start();
  }, [fade]);

  return (
    <Animated.View style={{ opacity: fade }}>
      <Card style={[styles.card, { borderColor: isHealthy ? colors.healthy : colors.danger }] }>
        <Card.Content>
        <View style={styles.headerRow}>
          <Text style={styles.title}>{result.class}</Text>
          <Chip compact style={isHealthy ? styles.goodChip : styles.alertChip}>
            {isHealthy ? 'Healthy' : 'Needs Action'}
          </Chip>
        </View>
        <Text style={styles.desc}>{result.description}</Text>
        <View style={styles.row}>
          <Text>Confidence: {result.confidence}%</Text>
          <Text style={styles.band}>{confidenceBand}</Text>
        </View>
        <View style={styles.kpiRow}>
          <Surface style={styles.kpiCard} elevation={0}>
            <Text style={styles.kpiLabel}>Severity</Text>
            <Text style={styles.kpiValue}>{severity.score}/100</Text>
            <Text style={styles.kpiSub}>{severity.level}</Text>
          </Surface>
          <Surface style={styles.kpiCard} elevation={0}>
            <Text style={styles.kpiLabel}>Confidence</Text>
            <Text style={styles.kpiValue}>{result.confidence}%</Text>
            <Text style={styles.kpiSub}>{confidenceBand}</Text>
          </Surface>
        </View>
        <ProgressBar progress={Math.min(result.confidence / 100, 1)} color={isHealthy ? colors.healthy : colors.accent} style={styles.progress} />
        <Text style={styles.section}>Symptoms</Text>
        <Text>{result.symptoms}</Text>
        <Text style={styles.section}>Solution</Text>
        <Text>{result.solution}</Text>
        <Text style={styles.section}>Fertilizer</Text>
        <Text>{result.fertilizer}</Text>
        </Card.Content>
      </Card>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  card: { borderRadius: 16, borderWidth: 2, backgroundColor: colors.white },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 8 },
  title: { fontSize: 24, fontWeight: '700', color: colors.text },
  desc: { marginVertical: 8, color: colors.text },
  row: { marginVertical: 8, flexDirection: 'row', justifyContent: 'space-between' },
  band: { fontWeight: '700', color: colors.primary },
  kpiRow: { flexDirection: 'row', gap: 10, marginBottom: 10 },
  kpiCard: { flex: 1, borderRadius: 12, padding: 10, backgroundColor: '#F2F5F2' },
  kpiLabel: { color: '#5A6A5B', fontSize: 12 },
  kpiValue: { fontWeight: '800', fontSize: 18, color: '#1E2A1F', marginTop: 2 },
  kpiSub: { color: colors.primary, marginTop: 2, fontWeight: '600', fontSize: 12 },
  progress: { height: 10, borderRadius: 8, marginBottom: 12 },
  section: { fontWeight: '700', marginTop: 10, marginBottom: 4 },
  goodChip: { backgroundColor: '#D8F5DC' },
  alertChip: { backgroundColor: '#FFE3E3' },
});
