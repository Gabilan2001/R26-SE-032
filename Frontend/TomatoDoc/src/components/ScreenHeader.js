import React from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { palette as P, gradients, radius } from '../theme';

/**
 * Forest-green page header shared by every module screen: back button, title, subtitle and an
 * optional element on the right (status badge, action button). Purely presentational.
 */
export default function ScreenHeader({ title, subtitle, onBack, right, eyebrow, children }) {
  const insets = useSafeAreaInsets();
  return (
    <LinearGradient
      colors={gradients.hero}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
      style={[styles.wrap, { paddingTop: insets.top + 12 }]}
    >
      <View style={styles.row}>
        {onBack ? (
          <TouchableOpacity style={styles.backBtn} onPress={onBack} activeOpacity={0.75}>
            <MaterialCommunityIcons name="arrow-left" size={20} color={P.onDark} />
          </TouchableOpacity>
        ) : null}
        <View style={styles.textWrap}>
          {eyebrow ? <Text style={styles.eyebrow}>{eyebrow}</Text> : null}
          <Text style={styles.title} numberOfLines={1}>{title}</Text>
          {subtitle ? <Text style={styles.subtitle} numberOfLines={2}>{subtitle}</Text> : null}
        </View>
        {right || null}
      </View>
      {children}
    </LinearGradient>
  );
}

/** Small glassy status pill for the right side of the header. */
export function HeaderBadge({ label, dot = true }) {
  return (
    <View style={styles.badge}>
      {dot ? <View style={styles.badgeDot} /> : null}
      <Text style={styles.badgeText}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    paddingHorizontal: 18,
    paddingBottom: 22,
    borderBottomLeftRadius: radius.xl,
    borderBottomRightRadius: radius.xl,
  },
  row: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  backBtn: {
    width: 40,
    height: 40,
    borderRadius: 14,
    backgroundColor: 'rgba(255,255,255,0.10)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.18)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  textWrap: { flex: 1 },
  eyebrow: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1.6,
    textTransform: 'uppercase',
    color: P.lime,
    marginBottom: 2,
  },
  title: { fontSize: 22, fontWeight: '800', color: P.onDark, letterSpacing: -0.5 },
  subtitle: { fontSize: 12, color: P.onDarkSoft, marginTop: 2, lineHeight: 17 },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: 'rgba(255,255,255,0.10)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.18)',
    borderRadius: radius.pill,
    paddingHorizontal: 10,
    paddingVertical: 5,
  },
  badgeDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: P.lime },
  badgeText: { fontSize: 11, fontWeight: '700', color: P.lime },
});
