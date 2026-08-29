import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { getTreatmentAdvice } from '../api/ragApi';

const COLORS = {
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

function ListRow({ text, index, numbered = false }) {
  return (
    <View style={styles.listRow}>
      {numbered ? (
        <View style={styles.markerNumbered}>
          <Text style={styles.markerNumberText}>{index + 1}</Text>
        </View>
      ) : (
        <View style={styles.markerBullet}>
          <View style={styles.dot} />
        </View>
      )}
      <Text style={styles.listText}>{text}</Text>
    </View>
  );
}

export default function TreatmentAdviceCard({ predictedClass }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [advice, setAdvice] = useState(null);

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
        <Text style={styles.headerLabel}>Treatment Plan</Text>
        <Text style={styles.headerTitle}>Recommended Actions</Text>
      </View>

      <View style={styles.body}>
        {loading && (
          <View style={styles.stateBox}>
            <ActivityIndicator size="small" color={COLORS.primary} />
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
                  <ListRow key={`why-${i}`} text={item} index={i} />
                ))}
              </View>
            )}

            {Array.isArray(advice.what_to_do) && advice.what_to_do.length > 0 && (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>What to do</Text>
                {advice.what_to_do.map((item, i) => (
                  <ListRow key={`todo-${i}`} text={item} index={i} numbered />
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
    backgroundColor: COLORS.white,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
    marginTop: 16,
    overflow: 'hidden',
  },
  header: {
    backgroundColor: COLORS.primaryLight,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderLeftWidth: 4,
    borderLeftColor: COLORS.primary,
  },
  headerLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: COLORS.primary,
    letterSpacing: 0.6,
    textTransform: 'uppercase',
    marginBottom: 2,
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: COLORS.text,
  },
  body: {
    padding: 16,
  },
  stateBox: {
    alignItems: 'center',
    paddingVertical: 20,
    gap: 8,
  },
  stateTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
    marginTop: 4,
  },
  stateSub: {
    fontSize: 13,
    color: COLORS.muted,
    textAlign: 'center',
    lineHeight: 19,
    paddingHorizontal: 8,
  },
  errorBox: {
    backgroundColor: COLORS.errorBg,
    borderRadius: 8,
    paddingHorizontal: 12,
  },
  errorTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.error,
  },
  errorText: {
    fontSize: 13,
    color: COLORS.error,
    textAlign: 'center',
    lineHeight: 19,
  },
  retryBtn: {
    marginTop: 8,
    backgroundColor: COLORS.primary,
    borderRadius: 8,
    paddingHorizontal: 20,
    paddingVertical: 10,
  },
  retryBtnText: {
    fontSize: 13,
    fontWeight: '600',
    color: COLORS.white,
  },
  problemBlock: {
    backgroundColor: COLORS.bg,
    borderRadius: 8,
    padding: 14,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  problemLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: COLORS.muted,
    letterSpacing: 0.5,
    textTransform: 'uppercase',
    marginBottom: 6,
  },
  problemText: {
    fontSize: 15,
    fontWeight: '600',
    color: COLORS.text,
    lineHeight: 22,
  },
  section: {
    marginBottom: 14,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: COLORS.primaryDark,
    marginBottom: 10,
    paddingBottom: 6,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  listRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    marginBottom: 10,
  },
  markerBullet: {
    width: 14,
    paddingTop: 7,
    alignItems: 'center',
  },
  markerNumbered: {
    width: 22,
    height: 22,
    marginTop: 1,
    borderRadius: 11,
    backgroundColor: COLORS.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  markerNumberText: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.white,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: COLORS.primary,
  },
  listText: {
    flex: 1,
    fontSize: 14,
    color: COLORS.textSecondary,
    lineHeight: 21,
  },
});
