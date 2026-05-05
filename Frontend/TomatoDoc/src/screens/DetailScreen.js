import React from 'react';
import { ScrollView, StyleSheet } from 'react-native';
import { List, Text } from 'react-native-paper';
import { nutrientDetails } from '../constants/nutrientDetails';
import { colors } from '../constants/colors';

export default function DetailScreen({ route }) {
  const { className } = route.params;
  const detail = nutrientDetails[className] || nutrientDetails.Healthy;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>{detail.title}</Text>
      <Text style={styles.sectionTitle}>Visual Symptoms Guide</Text>
      <Text>{detail.visualSymptoms}</Text>
      <Text style={styles.sectionTitle}>Step by Step Treatment Plan</Text>
      {detail.treatment.map((step, idx) => (
        <List.Item key={idx} title={`${idx + 1}. ${step}`} />
      ))}
      <Text style={styles.sectionTitle}>Fertilizer Dosage</Text>
      <Text>{detail.dosage}</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  content: { padding: 16 },
  title: { fontSize: 24, fontWeight: '700', color: colors.primary, marginBottom: 12 },
  sectionTitle: { marginTop: 16, marginBottom: 8, fontWeight: '700' },
});
