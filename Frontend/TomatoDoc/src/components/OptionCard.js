import React from 'react';
import { StyleSheet } from 'react-native';
import { Card, Text } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { colors } from '../constants/colors';

export default function OptionCard({ title, icon, locked, onPress }) {
  return (
    <Card style={[styles.card, locked ? styles.locked : styles.active]} onPress={locked ? undefined : onPress}>
      <Card.Content style={styles.content}>
        <MaterialCommunityIcons name={icon} size={28} color={locked ? colors.muted : colors.primary} />
        <Text style={styles.title}>{title}</Text>
        {locked ? <Text style={styles.lockText}>Locked</Text> : <Text style={styles.openText}>Open</Text>}
      </Card.Content>
    </Card>
  );
}

const styles = StyleSheet.create({
  card: { borderRadius: 16, marginBottom: 12 },
  content: { alignItems: 'center', gap: 8 },
  active: { backgroundColor: '#E8F5E9' },
  locked: { backgroundColor: '#ECEFF1' },
  title: { fontWeight: '700', color: colors.text },
  lockText: { color: colors.muted },
  openText: { color: colors.primary, fontWeight: '600' },
});
