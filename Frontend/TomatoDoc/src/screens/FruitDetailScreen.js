import React from 'react';
import { ScrollView, StyleSheet, View } from 'react-native';
import { Card, Chip, Text } from 'react-native-paper';

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
  container: { flex: 1, backgroundColor: '#0f0f0f' },
  content: { padding: 16, gap: 12 },
  hero: { borderRadius: 16, backgroundColor: '#1a1a1a' },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  title: { color: '#f0f0f0', fontSize: 22, fontWeight: '800' },
  desc: { color: '#aaaaaa', marginTop: 8 },
  conf: { color: '#c8f135', fontWeight: '700', marginTop: 10 },
  sectionCard: { borderRadius: 16, backgroundColor: '#1a1a1a' },
  sectionTitle: { color: '#f0f0f0', fontWeight: '800', marginBottom: 8 },
  bullet: { color: '#d6d6d6', marginBottom: 6, lineHeight: 20 },
  empty: { color: '#888' },
  goodChip: { backgroundColor: 'rgba(74,223,111,0.16)' },
  alertChip: { backgroundColor: 'rgba(255,92,92,0.16)' },
});

