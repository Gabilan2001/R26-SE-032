import React from 'react';
import { ActivityIndicator, StyleSheet, View } from 'react-native';
import { Text } from 'react-native-paper';
import { colors } from '../constants/colors';

export default function LoadingOverlay({ text = 'Loading...' }) {
  return (
    <View style={styles.overlay}>
      <ActivityIndicator size="large" color={colors.primary} />
      <Text style={styles.text}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  overlay: { ...StyleSheet.absoluteFillObject, backgroundColor: 'rgba(255,255,255,0.85)', alignItems: 'center', justifyContent: 'center', zIndex: 100 },
  text: { marginTop: 10, color: colors.primary, fontWeight: '600' },
});
