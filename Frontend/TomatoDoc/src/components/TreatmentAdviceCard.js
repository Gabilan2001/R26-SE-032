import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { getTreatmentAdvice } from '../api/ragApi';

const LIGHT = {
  white: '#FFFFFF',
  bg: '#F4F7FB',
  border: '#D8E2EF',
  primary: '#1565C0',
  primaryDark: '#0D47A1',
  primaryLight: '#E8F1FA',
  text: '#1A2332',
  textSecondary: '#4A5568',
  muted: '#6B7280',
  error: '#B91C1C',
  errorBg: '#FEF2F2',
};

const DARK = {
  card: '#1a1a1a',
  cardInner: '#222222',
  border: 'rgba(255,255,255,0.07)',
  accent: '#c8f135',
  accentDim: 'rgba(200,241,53,0.10)',
  accentBorder: 'rgba(200,241,53,0.22)',
  text: '#f0f0f0',
  textSecondary: 'rgba(255,255,255,0.72)',
  muted: '#666666',
  error: '#ff5c5c',
  errorBg: 'rgba(255,92,92,0.10)',
};

function ListRow({ text, index, numbered = false, colors, styles }) {
  return (
    <View style={styles.listRow}>
      {numbered ? (
        <View style={styles.markerNumbered}>
          <Text style={styles.markerNumberText}>{index + 1}</Text>
        </View>
      ) : (
        <View style={styles.markerBullet}>
          <View style={[styles.dot, { backgroundColor: colors.primary }]} />
        </View>
      )}
      <Text style={styles.listText}>{text}</Text>
    </View>
  );
}

export default function TreatmentAdviceCard({ predictedClass, variant = 'light' }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [advice, setAdvice] = useState(null);

  const isDark = variant === 'dark';
  const colors = isDark
    ? { ...DARK, primary: DARK.accent, primaryDark: DARK.accent, primaryLight: DARK.accentDim, white: DARK.text }
    : LIGHT;
  const styles = isDark ? darkStyles(colors) : lightStyles;

  const loadAdvice = useCallback(async () => {
    if (!predictedClass) {
      setError('No diagnosis available to load treatment guidance.');
      setLoading(false);
      return;
    }

    setLoading(true);
    setError('');
    setAdvice(null);

    try {
      const data = await getTreatmentAdvice(predictedClass);
      setAdvice(data);
    } catch (e) {
      const message =
        e?.name === 'AbortError'
          ? 'The request timed out. The server may still be starting — please try again in a moment.'
          : e?.message || 'Could not load advice. Please try again.';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [predictedClass]);

  useEffect(() => {
    loadAdvice();
  }, [loadAdvice]);

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        {isDark && (
          <MaterialCommunityIcons name="medical-bag" size={18} color={colors.accent} style={{ marginBottom: 6 }} />
        )}
        <Text style={styles.headerLabel}>Treatment plan</Text>
        <Text style={styles.headerTitle}>Recommended actions</Text>
      </View>

      <View style={styles.body}>
        {loading && (
          <View style={styles.stateBox}>
            <ActivityIndicator size="small" color={colors.primary} />
            <Text style={styles.stateTitle}>Loading guidance</Text>
            <Text style={styles.stateSub}>
              This may take up to a minute on the first request.
            </Text>
          </View>
        )}

        {!loading && error ? (
          <View style={[styles.stateBox, styles.errorBox]}>
            <Text style={styles.errorTitle}>Unable to load guidance</Text>
            <Text style={styles.errorText}>{error}</Text>
            <TouchableOpacity style={styles.retryBtn} onPress={loadAdvice} activeOpacity={0.85}>
              <Text style={styles.retryBtnText}>Try again</Text>
            </TouchableOpacity>
          </View>
        ) : null}

        {!loading && !error && advice ? (
          <>
            <View style={styles.problemBlock}>
              <Text style={styles.problemLabel}>Diagnosis summary</Text>
              <Text style={styles.problemText}>{advice.problem}</Text>
            </View>

            {Array.isArray(advice.why) && advice.why.length > 0 && (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Why it happened</Text>
                {advice.why.map((item, i) => (
                  <ListRow key={`why-${i}`} text={item} index={i} colors={colors} styles={styles} />
                ))}
              </View>
            )}

            {Array.isArray(advice.what_to_do) && advice.what_to_do.length > 0 && (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>What to do</Text>
                {advice.what_to_do.map((item, i) => (
                  <ListRow key={`todo-${i}`} text={item} index={i} numbered colors={colors} styles={styles} />
                ))}
              </View>
            )}
          </>
        ) : null}
      </View>
    </View>
  );
}

const lightStyles = StyleSheet.create({
  card: {
    backgroundColor: LIGHT.white,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: LIGHT.border,
    marginTop: 16,
    overflow: 'hidden',
  },
  header: {
    backgroundColor: LIGHT.primaryLight,
    borderBottomWidth: 1,
    borderBottomColor: LIGHT.border,
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderLeftWidth: 4,
    borderLeftColor: LIGHT.primary,
  },
  headerLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: LIGHT.primary,
    letterSpacing: 0.6,
    textTransform: 'uppercase',
    marginBottom: 2,
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: LIGHT.text,
  },
  body: { padding: 16 },
  stateBox: { alignItems: 'center', paddingVertical: 20, gap: 8 },
  stateTitle: { fontSize: 14, fontWeight: '600', color: LIGHT.text, marginTop: 4 },
  stateSub: { fontSize: 13, color: LIGHT.muted, textAlign: 'center', lineHeight: 19, paddingHorizontal: 8 },
  errorBox: { backgroundColor: LIGHT.errorBg, borderRadius: 8, paddingHorizontal: 12 },
  errorTitle: { fontSize: 14, fontWeight: '600', color: LIGHT.error },
  errorText: { fontSize: 13, color: LIGHT.error, textAlign: 'center', lineHeight: 19 },
  retryBtn: { marginTop: 8, backgroundColor: LIGHT.primary, borderRadius: 8, paddingHorizontal: 20, paddingVertical: 10 },
  retryBtnText: { fontSize: 13, fontWeight: '600', color: LIGHT.white },
  problemBlock: {
    backgroundColor: LIGHT.bg,
    borderRadius: 8,
    padding: 14,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: LIGHT.border,
  },
  problemLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: LIGHT.muted,
    letterSpacing: 0.5,
    textTransform: 'uppercase',
    marginBottom: 6,
  },
  problemText: { fontSize: 15, fontWeight: '600', color: LIGHT.text, lineHeight: 22 },
  section: { marginBottom: 14 },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: LIGHT.primaryDark,
    marginBottom: 10,
    paddingBottom: 6,
    borderBottomWidth: 1,
    borderBottomColor: LIGHT.border,
  },
  listRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 10, marginBottom: 10 },
  markerBullet: { width: 14, paddingTop: 7, alignItems: 'center' },
  markerNumbered: {
    width: 22,
    height: 22,
    marginTop: 1,
    borderRadius: 11,
    backgroundColor: LIGHT.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  markerNumberText: { fontSize: 12, fontWeight: '700', color: LIGHT.white },
  dot: { width: 6, height: 6, borderRadius: 3 },
  listText: { flex: 1, fontSize: 14, color: LIGHT.textSecondary, lineHeight: 21 },
});

function darkStyles(colors) {
  return StyleSheet.create({
    card: {
      backgroundColor: colors.card,
      borderRadius: 16,
      borderWidth: 1,
      borderColor: colors.border,
      marginTop: 2,
      overflow: 'hidden',
    },
    header: {
      backgroundColor: colors.accentDim,
      borderBottomWidth: 1,
      borderBottomColor: colors.border,
      paddingHorizontal: 16,
      paddingVertical: 14,
      borderLeftWidth: 3,
      borderLeftColor: colors.accent,
    },
    headerLabel: {
      fontSize: 11,
      fontWeight: '600',
      color: colors.accent,
      letterSpacing: 0.6,
      textTransform: 'uppercase',
      marginBottom: 2,
    },
    headerTitle: { fontSize: 17, fontWeight: '700', color: colors.text },
    body: { padding: 16 },
    stateBox: { alignItems: 'center', paddingVertical: 20, gap: 8 },
    stateTitle: { fontSize: 14, fontWeight: '600', color: colors.text, marginTop: 4 },
    stateSub: { fontSize: 13, color: colors.muted, textAlign: 'center', lineHeight: 19, paddingHorizontal: 8 },
    errorBox: { backgroundColor: colors.errorBg, borderRadius: 10, paddingHorizontal: 12 },
    errorTitle: { fontSize: 14, fontWeight: '600', color: colors.error },
    errorText: { fontSize: 13, color: colors.error, textAlign: 'center', lineHeight: 19 },
    retryBtn: {
      marginTop: 8,
      backgroundColor: colors.accent,
      borderRadius: 10,
      paddingHorizontal: 20,
      paddingVertical: 10,
    },
    retryBtnText: { fontSize: 13, fontWeight: '700', color: '#0f0f0f' },
    problemBlock: {
      backgroundColor: colors.cardInner,
      borderRadius: 12,
      padding: 14,
      marginBottom: 16,
      borderWidth: 1,
      borderColor: colors.border,
    },
    problemLabel: {
      fontSize: 11,
      fontWeight: '600',
      color: colors.muted,
      letterSpacing: 0.5,
      textTransform: 'uppercase',
      marginBottom: 6,
    },
    problemText: { fontSize: 15, fontWeight: '600', color: colors.text, lineHeight: 22 },
    section: { marginBottom: 14 },
    sectionTitle: {
      fontSize: 13,
      fontWeight: '700',
      color: colors.accent,
      marginBottom: 10,
      paddingBottom: 6,
      borderBottomWidth: 1,
      borderBottomColor: colors.border,
    },
    listRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 10, marginBottom: 10 },
    markerBullet: { width: 14, paddingTop: 7, alignItems: 'center' },
    markerNumbered: {
      width: 22,
      height: 22,
      marginTop: 1,
      borderRadius: 11,
      backgroundColor: colors.accent,
      alignItems: 'center',
      justifyContent: 'center',
    },
    markerNumberText: { fontSize: 12, fontWeight: '700', color: '#0f0f0f' },
    dot: { width: 6, height: 6, borderRadius: 3 },
    listText: { flex: 1, fontSize: 14, color: colors.textSecondary, lineHeight: 21 },
  });
}
