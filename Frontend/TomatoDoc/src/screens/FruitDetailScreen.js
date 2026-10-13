import React from 'react';
import { ScrollView, StyleSheet, View } from 'react-native';
import { Card, Chip, Text } from 'react-native-paper';
import { palette as P, radius, shadow } from '../theme';

const splitText = (value) =>
  Array.isArray(value)
    ? value
    : String(value || '')
        .split(/\r?\n|,\s*/)
        .map((s) => s.trim())
        .filter(Boolean);

export default function FruitDetailScreen({ route }) {
  const { result } = route.params || {};
  const symptoms = splitText(result?.symptoms);
  const treatments = splitText(result?.treatment || result?.solution);
  const isHealthy = result?.class === 'Healthy_Tomato' || result?.class === 'Healthy';

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Card style={styles.hero}>
        <Card.Content>
          <View style={styles.headerRow}>
            <Text style={styles.title}>{result?.class || 'Unknown'}</Text>
            <Chip style={isHealthy ? styles.goodChip : styles.alertChip}>
              {isHealthy ? 'Healthy' : 'Disease'}
            </Chip>
          </View>
          <Text style={styles.desc}>{result?.description || 'No description available.'}</Text>
          <Text style={styles.conf}>Confidence: {Math.round(Number(result?.confidence || 0))}%</Text>
        </Card.Content>
      </Card>

      <Card style={styles.sectionCard}>
        <Card.Content>
          <Text style={styles.sectionTitle}>Symptoms</Text>
          {symptoms.length ? symptoms.map((s, i) => <Text key={i} style={styles.bullet}>- {s}</Text>) : <Text style={styles.empty}>No symptoms listed.</Text>}
        </Card.Content>
      </Card>

      <Card style={styles.sectionCard}>
        <Card.Content>
          <Text style={styles.sectionTitle}>Treatment Guide</Text>
          {treatments.length ? treatments.map((t, i) => <Text key={i} style={styles.bullet}>{i + 1}. {t}</Text>) : <Text style={styles.empty}>No treatment listed.</Text>}
        </Card.Content>
      </Card>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: P.bg },
  content: { padding: 16, gap: 12, paddingBottom: 40 },
  hero: { borderRadius: radius.xl, backgroundColor: P.forestMid, ...shadow.card },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  title: { color: '#FFFFFF', fontSize: 24, fontWeight: '800', letterSpacing: -0.5, flex: 1, marginRight: 10 },
  desc: { color: 'rgba(255,255,255,0.8)', marginTop: 8, lineHeight: 20 },
  conf: { color: P.lime, fontWeight: '800', marginTop: 10 },
  sectionCard: { borderRadius: radius.lg, backgroundColor: P.surface, borderWidth: 1, borderColor: P.border, ...shadow.card },
  sectionTitle: { color: P.text, fontWeight: '800', fontSize: 15, marginBottom: 10 },
  bullet: { color: P.textSoft, marginBottom: 8, lineHeight: 21 },
  empty: { color: P.muted },
  goodChip: { backgroundColor: P.goodDim },
  alertChip: { backgroundColor: P.dangerDim },
});
