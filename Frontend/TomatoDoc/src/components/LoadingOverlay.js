import React, { useContext } from 'react';
import { ActivityIndicator, StyleSheet, View } from 'react-native';
import { Text } from 'react-native-paper';
import { UIThemeContext } from '../context/UIThemeContext';

export default function LoadingOverlay({ text = 'Loading...' }) {
  const { isDark, palette } = useContext(UIThemeContext);
  return (
    <View style={[styles.overlay, { backgroundColor: isDark ? 'rgba(0,0,0,0.65)' : 'rgba(255,255,255,0.85)' }]}>
      <ActivityIndicator size="large" color={palette.primary} />
      <Text style={[styles.text, { color: palette.primary }]}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  overlay: { ...StyleSheet.absoluteFillObject, alignItems: 'center', justifyContent: 'center', zIndex: 100 },
  text: { marginTop: 10, fontWeight: '600' },
});
