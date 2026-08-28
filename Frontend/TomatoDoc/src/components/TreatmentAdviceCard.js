import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Animated,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { getTreatmentAdvice } from '../api/ragApi';

const PALETTE = {
  nutrient: {
    accent: '#c8f135',
    accentDim: 'rgba(200,241,53,0.10)',
    accentBorder: 'rgba(200,241,53,0.22)',
    bannerBg: '#0f1a00',
  },
  fruit: {
    accent: '#ff5c5c',
    accentDim: 'rgba(255,92,92,0.10)',
    accentBorder: 'rgba(255,92,92,0.22)',
    bannerBg: '#1a0500',
  },
};

const BASE = {
  surface: '#1a1a1a',
  surface2: '#222222',
  text: '#f0f0f0',
  muted: '#666666',
  border: 'rgba(255,255,255,0.07)',
  danger: '#ff5c5c',
  dangerDim: 'rgba(255,92,92,0.10)',
};

function BulletItem({ text, index, accent, accentDim, accentBorder, numbered = false }) {
  const op = useRef(new Animated.Value(0)).current;
  const x = useRef(new Animated.Value(-10)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(op, { toValue: 1, duration: 320, delay: index * 60, useNativeDriver: true }),
      Animated.spring(x, { toValue: 0, delay: index * 60, useNativeDriver: true }),
    ]).start();
  }, [index, op, x]);

  return (
    <Animated.View style={[styles.listItem, { opacity: op, transform: [{ translateX: x }] }]}>
      <View style={[styles.bullet, { backgroundColor: accentDim, borderColor: accentBorder }]}>
        <Text style={[styles.bulletTxt, { color: accent }]}>
          {numbered ? index + 1 : '•'}
        </Text>
      </View>
      <Text style={styles.listTxt}>{text}</Text>
    </Animated.View>
  );
}

export default function TreatmentAdviceCard({ predictedClass, variant = 'nutrient' }) {
  const theme = PALETTE[variant] ?? PALETTE.nutrient;
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [advice, setAdvice] = useState(null);

  const loadAdvice = useCallback(async () => {
    if (!predictedClass) {
      setError('No prediction class available.');
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
          ? 'Request timed out. The advice server may still be waking up — please try again.'
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
    <View style={[styles.card, { borderColor: theme.accentBorder }]}>
      <View style={[styles.header, { backgroundColor: theme.bannerBg }]}>
        <Text style={styles.headerIcon}>🌿</Text>
        <View style={styles.headerBody}>
          <Text style={[styles.headerTitle, { color: theme.accent }]}>Treatment Advice</Text>
          <Text style={styles.headerSub}>AI-powered guidance for farmers</Text>
        </View>
      </View>

      <View style={styles.body}>
        {loading && (
          <View style={styles.centerBox}>
            <ActivityIndicator size="large" color={theme.accent} />
            <Text style={styles.loadingTitle}>Loading advice…</Text>
            <Text style={styles.loadingSub}>
              First request may take 30–60 seconds while the server wakes up.
            </Text>
          </View>
        )}

        {!loading && error ? (
          <View style={styles.centerBox}>
            <Text style={styles.errorIcon}>⚠</Text>
            <Text style={styles.errorTxt}>{error}</Text>
            <TouchableOpacity
              style={[styles.retryBtn, { backgroundColor: theme.accent }]}
              onPress={loadAdvice}
              activeOpacity={0.85}
            >
              <Text style={styles.retryBtnTxt}>Retry</Text>
            </TouchableOpacity>
          </View>
        ) : null}

        {!loading && !error && advice ? (
          <>
            <Text style={styles.problemTitle}>{advice.problem}</Text>

            {Array.isArray(advice.why) && advice.why.length > 0 && (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Why it happened</Text>
                {advice.why.map((item, i) => (
                  <BulletItem
                    key={`why-${i}`}
                    text={item}
                    index={i}
                    accent={theme.accent}
                    accentDim={theme.accentDim}
                    accentBorder={theme.accentBorder}
                  />
                ))}
              </View>
            )}

            {Array.isArray(advice.what_to_do) && advice.what_to_do.length > 0 && (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>What to do</Text>
                {advice.what_to_do.map((item, i) => (
                  <BulletItem
                    key={`todo-${i}`}
                    text={item}
                    index={i}
                    accent={theme.accent}
                    accentDim={theme.accentDim}
                    accentBorder={theme.accentBorder}
                    numbered
                  />
                ))}
              </View>
            )}
          </>
        ) : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: BASE.surface,
    borderWidth: 1,
    borderRadius: 16,
    overflow: 'hidden',
    marginTop: 14,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    padding: 14,
    borderBottomWidth: 1,
    borderBottomColor: BASE.border,
  },
  headerIcon: { fontSize: 22 },
  headerBody: { flex: 1 },
  headerTitle: { fontSize: 14, fontWeight: '800', letterSpacing: 0.2 },
  headerSub: { fontSize: 11, color: BASE.muted, marginTop: 2 },
  body: { padding: 14 },
  centerBox: { alignItems: 'center', paddingVertical: 18, gap: 10 },
  loadingTitle: { fontSize: 14, fontWeight: '700', color: BASE.text, marginTop: 4 },
  loadingSub: {
    fontSize: 11,
    color: BASE.muted,
    textAlign: 'center',
    lineHeight: 17,
    paddingHorizontal: 12,
  },
  errorIcon: { fontSize: 22, color: BASE.danger },
  errorTxt: {
    fontSize: 12,
    color: BASE.danger,
    textAlign: 'center',
    lineHeight: 18,
    paddingHorizontal: 8,
  },
  retryBtn: {
    marginTop: 6,
    borderRadius: 10,
    paddingHorizontal: 22,
    paddingVertical: 10,
  },
  retryBtnTxt: { fontSize: 13, fontWeight: '800', color: '#0f0f0f' },
  problemTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: BASE.text,
    lineHeight: 22,
    marginBottom: 12,
  },
  section: { marginBottom: 10 },
  sectionTitle: {
    fontSize: 10,
    fontWeight: '700',
    color: BASE.muted,
    textTransform: 'uppercase',
    letterSpacing: 0.7,
    marginBottom: 8,
  },
  listItem: { flexDirection: 'row', gap: 9, alignItems: 'flex-start', marginBottom: 8 },
  bullet: {
    minWidth: 18,
    height: 18,
    borderRadius: 5,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 1,
    paddingHorizontal: 4,
  },
  bulletTxt: { fontSize: 9, fontWeight: '800' },
  listTxt: { flex: 1, fontSize: 12, color: 'rgba(255,255,255,0.68)', lineHeight: 18 },
});
