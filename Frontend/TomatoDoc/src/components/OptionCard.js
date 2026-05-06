import React from 'react';
import { Image, StyleSheet, View } from 'react-native';
import { Card, Chip, Text } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { colors } from '../constants/colors';

export default function OptionCard({
  title,
  subtitle,
  icon,
  locked,
  onPress,
  novelty,
  imageSource,
}) {
  return (
    <Card
      style={[styles.card, locked ? styles.locked : styles.active]}
      onPress={locked ? undefined : onPress}
    >
      <Card.Content style={styles.content}>
        <View style={styles.headerRow}>
          {imageSource ? (
            <Image source={imageSource} style={styles.preview} />
          ) : (
            <MaterialCommunityIcons
              name={icon}
              size={30}
              color={locked ? colors.muted : colors.primary}
            />
          )}
          <View style={styles.titleWrap}>
            <Text style={styles.title}>{title}</Text>
            {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
          </View>
        </View>
        <View style={styles.metaRow}>
          {novelty ? <Chip compact style={styles.noveltyChip}>Novelty</Chip> : null}
          {locked ? (
            <Text style={styles.lockText}>Locked</Text>
          ) : (
            <Text style={styles.openText}>Open</Text>
          )}
        </View>
      </Card.Content>
    </Card>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: 18,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.45)',
    shadowColor: '#000',
    shadowOpacity: 0.08,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 6 },
    elevation: 3,
  },
  content: { gap: 10, paddingVertical: 6 },
  headerRow: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  preview: { width: 52, height: 52, borderRadius: 14 },
  titleWrap: { flex: 1 },
  active: { backgroundColor: 'rgba(243,251,244,0.96)' },
  locked: { backgroundColor: 'rgba(236,239,241,0.96)' },
  title: { fontWeight: '800', color: colors.text, fontSize: 16 },
  subtitle: { color: '#546E57', marginTop: 2 },
  metaRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  noveltyChip: { backgroundColor: '#E8F5E9' },
  lockText: { color: colors.muted },
  openText: { color: colors.primary, fontWeight: '600' },
});
