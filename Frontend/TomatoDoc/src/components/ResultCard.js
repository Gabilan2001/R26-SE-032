import React from 'react';
import { StyleSheet, View } from 'react-native';
import { Card, ProgressBar, Text } from 'react-native-paper';
import { colors } from '../constants/colors';

export default function ResultCard({ result }) {
  const isHealthy = result.class === 'Healthy';
  return (
    <Card style={[styles.card, { borderColor: isHealthy ? colors.healthy : colors.danger }] }>
      <Card.Content>
        <Text style={styles.title}>{result.class}</Text>
        <Text style={styles.desc}>{result.description}</Text>
        <View style={styles.row}><Text>Confidence: {result.confidence}%</Text></View>
        <ProgressBar progress={Math.min(result.confidence / 100, 1)} color={isHealthy ? colors.healthy : colors.accent} style={styles.progress} />
        <Text style={styles.section}>Symptoms</Text>
        <Text>{result.symptoms}</Text>
        <Text style={styles.section}>Solution</Text>
        <Text>{result.solution}</Text>
        <Text style={styles.section}>Fertilizer</Text>
        <Text>{result.fertilizer}</Text>
      </Card.Content>
    </Card>
  );
}

const styles = StyleSheet.create({
  card: { borderRadius: 16, borderWidth: 2, backgroundColor: colors.white },
  title: { fontSize: 24, fontWeight: '700', color: colors.text },
  desc: { marginVertical: 8, color: colors.text },
  row: { marginVertical: 8 },
  progress: { height: 10, borderRadius: 8, marginBottom: 12 },
  section: { fontWeight: '700', marginTop: 10, marginBottom: 4 },
});
