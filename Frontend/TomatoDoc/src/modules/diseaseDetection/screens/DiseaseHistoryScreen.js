import React, { useCallback, useEffect, useState } from 'react';
import {
  FlatList,
  Pressable,
  RefreshControl,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { getDiseaseHistory, getDiseaseStats } from '../api/history';
import { formatDateTime } from '../../../utils/formatters';
import DiseaseChip from '../components/DiseaseChip';

// ── Tokens (matches DiseaseScanScreen/DiseaseResultScreen's amber theme) ──────
const C = {
  bg:           '#0f0f0f',
  surface:      '#1a1a1a',
  surface2:     '#222222',
  accent:       '#c8f135',
  text:         '#f0f0f0',
  muted:        '#666666',
  border:       'rgba(255,255,255,0.07)',
  amber:        '#f5a623',
  amberDim:     'rgba(245,166,35,0.10)',
  amberBorder:  'rgba(245,166,35,0.22)',
};

function StatBox({ num, label }) {
  return (
    <View style={styles.statBox}>
      <Text style={styles.statNum} numberOfLines={1}>{num}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

function HistoryItem({ item }) {
  const [expanded, setExpanded] = useState(false);
  const diseases = item.diseases_found || [];
  const preview = item.treatment_answer
    ? item.treatment_answer.replace(/[#*]/g, '').trim()
    : null;

  return (
    <Pressable
      style={styles.itemCard}
      onPress={() => preview && setExpanded((v) => !v)}
    >
      <View style={styles.itemHeader}>
        <Text style={styles.itemDate}>{item.created_at ? formatDateTime(item.created_at) : '—'}</Text>
        {item.co_occurrence && <Text style={styles.itemCoOcc}>⚠ Multiple issues</Text>}
      </View>
      <View style={styles.chipRow}>
        {diseases.map((d) => <DiseaseChip key={d} name={d} compact />)}
      </View>
      {preview && (
        <Text style={styles.itemPreview} numberOfLines={expanded ? undefined : 2}>
          {preview}
        </Text>
      )}
      {preview && (
        <Text style={styles.itemToggle}>{expanded ? 'Show less ▲' : 'Show more ▾'}</Text>
      )}
    </Pressable>
  );
}

export default function DiseaseHistoryScreen() {
  const [history, setHistory]   = useState([]);
  const [stats, setStats]       = useState(null);
  const [loading, setLoading]   = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [unavailable, setUnavailable] = useState(false);

  const load = useCallback(async () => {
    try {
      const [historyRes, statsRes] = await Promise.all([
        getDiseaseHistory(30),
        getDiseaseStats(),
      ]);
      setHistory(historyRes.data.history || []);
      setStats(statsRes.data);
      setUnavailable(false);
    } catch (e) {
      // 503 = Firestore not configured server-side; any other error also
      // just falls back to an empty, friendly state rather than a crash.
      setUnavailable(true);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const onRefresh = () => {
    setRefreshing(true);
    load();
  };

  const topDisease = stats && Object.keys(stats.class_counts || {}).length
    ? Object.entries(stats.class_counts).sort((a, b) => b[1] - a[1])[0][0].replace('_', ' ')
    : '—';

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" backgroundColor={C.bg} />
      <FlatList
        style={styles.list}
        contentContainerStyle={styles.content}
        data={history}
        keyExtractor={(item) => item.id}
        refreshControl={<RefreshControl tintColor={C.amber} refreshing={refreshing} onRefresh={onRefresh} />}
        ListHeaderComponent={
          <View>
            <Text style={styles.screenTitle}>Scan History</Text>
            <Text style={styles.screenSub}>Past leaf scans and treatment advice for this app</Text>

            {stats && (
              <View style={styles.statsRow}>
                <StatBox num={stats.total_scans ?? 0} label="Total Scans" />
                <StatBox num={topDisease} label="Most Common" />
                <StatBox num={stats.co_occurrence_count ?? 0} label="Multi-Issue" />
              </View>
            )}

            {unavailable && (
              <View style={styles.emptyBox}>
                <Text style={styles.emptyIcon}>📡</Text>
                <Text style={styles.emptyTitle}>History unavailable</Text>
                <Text style={styles.emptyTxt}>
                  Couldn't reach the history service right now. Pull down to retry.
                </Text>
              </View>
            )}

            {!unavailable && !loading && history.length === 0 && (
              <View style={styles.emptyBox}>
                <Text style={styles.emptyIcon}>🍃</Text>
                <Text style={styles.emptyTitle}>No scans yet</Text>
                <Text style={styles.emptyTxt}>Scan a leaf and it'll show up here.</Text>
              </View>
            )}
          </View>
        }
        renderItem={({ item }) => <HistoryItem item={item} />}
      />
    </View>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: C.bg },
  list: { flex: 1 },
  content: { padding: 18, paddingBottom: 130 },

  screenTitle: { fontSize: 20, fontWeight: '800', color: C.text, marginTop: 4, marginBottom: 2 },
  screenSub:   { fontSize: 12, color: C.muted, marginBottom: 16 },

  statsRow: { flexDirection: 'row', gap: 10, marginBottom: 18 },
  statBox: {
    flex: 1, backgroundColor: C.surface, borderWidth: 1, borderColor: C.border,
    borderRadius: 16, padding: 12, alignItems: 'center',
  },
  statNum:   { fontSize: 17, fontWeight: '800', color: C.amber, marginBottom: 2 },
  statLabel: { fontSize: 9.5, color: C.muted, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.4, textAlign: 'center' },

  emptyBox: { alignItems: 'center', paddingVertical: 50 },
  emptyIcon: { fontSize: 34, marginBottom: 10, opacity: 0.6 },
  emptyTitle: { fontSize: 14, fontWeight: '800', color: C.text, marginBottom: 4 },
  emptyTxt: { fontSize: 11.5, color: C.muted, textAlign: 'center', paddingHorizontal: 30, lineHeight: 17 },

  itemCard: {
    backgroundColor: C.surface, borderWidth: 1, borderColor: C.border,
    borderRadius: 16, padding: 14, marginBottom: 10,
  },
  itemHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  itemDate: { fontSize: 11, color: C.muted, fontWeight: '600' },
  itemCoOcc: { fontSize: 10, color: '#ff5c5c', fontWeight: '700' },

  chipRow: { flexDirection: 'row', gap: 6, flexWrap: 'wrap', marginBottom: 8 },

  itemPreview: { fontSize: 11.5, color: 'rgba(255,255,255,0.65)', lineHeight: 17 },
  itemToggle:  { fontSize: 10, color: C.amber, fontWeight: '700', marginTop: 6 },
});
