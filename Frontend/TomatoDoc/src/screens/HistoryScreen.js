import React, { useCallback, useContext, useEffect, useRef, useState } from 'react';
import {
  Animated,
  FlatList,
  Pressable,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { AuthContext } from '../context/AuthContext';
import { UIThemeContext } from '../context/UIThemeContext';
import { getHistory } from '../api/historyApi';
import { getFruitHistory } from '../api/fruitHistoryApi';
import { formatDateTime } from '../utils/formatters';

// ── Tokens ────────────────────────────────────────────────────────────────────
const C = {
  bg:           '#0f0f0f',
  surface:      '#1a1a1a',
  surface2:     '#222222',
  accent:       '#c8f135',
  accentDim:    'rgba(200,241,53,0.10)',
  accentBorder: 'rgba(200,241,53,0.22)',
  text:         '#f0f0f0',
  muted:        '#555555',
  border:       'rgba(255,255,255,0.07)',
  danger:       '#ff5c5c',
  dangerDim:    'rgba(255,92,92,0.10)',
  dangerBorder: 'rgba(255,92,92,0.18)',
  warn:         '#f5a623',
  warnDim:      'rgba(245,166,35,0.10)',
  warnBorder:   'rgba(245,166,35,0.20)',
  success:      '#4adf6f',
  successDim:   'rgba(74,223,111,0.10)',
  successBorder:'rgba(74,223,111,0.20)',
};

// ── Status helpers ────────────────────────────────────────────────────────────
const getStatus = (className, mode) => {
  if (mode === 'fruit') {
    return className === 'Healthy_Tomato' || className === 'Healthy' ? 'healthy' : 'disease';
  }
  return className === 'Healthy' ? 'healthy' : 'deficiency';
};

const STATUS_META = {
  healthy:    { label: 'Healthy',     color: C.success, dim: C.successDim, border: C.successBorder, emoji: '✅', accentColor: C.success },
  disease:    { label: 'Disease',     color: C.danger,  dim: C.dangerDim,  border: C.dangerBorder,  emoji: '🍅', accentColor: C.danger },
  deficiency: { label: 'Deficiency',  color: C.warn,    dim: C.warnDim,    border: C.warnBorder,    emoji: '🍃', accentColor: C.warn },
};

// ── Summary card ──────────────────────────────────────────────────────────────
function SummaryCard({ num, label, numColor, delay = 0 }) {
  const op = useRef(new Animated.Value(0)).current;
  const y  = useRef(new Animated.Value(12)).current;
  useEffect(() => {
    Animated.parallel([
      Animated.timing(op, { toValue: 1, duration: 320, delay, useNativeDriver: true }),
      Animated.spring(y,  { toValue: 0, delay,           useNativeDriver: true }),
    ]).start();
  }, [num]);
  return (
    <Animated.View style={[styles.sumCard, { opacity: op, transform: [{ translateY: y }] }]}>
      <Text style={[styles.sumNum, { color: numColor }]}>{num}</Text>
      <Text style={styles.sumLabel}>{label}</Text>
    </Animated.View>
  );
}

// ── History list item ─────────────────────────────────────────────────────────
function HistoryItem({ item, mode, onPress, index }) {
  const status = getStatus(item.class_name, mode);
  const meta   = STATUS_META[status];

  const op    = useRef(new Animated.Value(0)).current;
  const slideX= useRef(new Animated.Value(-16)).current;
  const scale = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(op,     { toValue: 1, duration: 300, delay: index * 55, useNativeDriver: true }),
      Animated.spring(slideX, { toValue: 0, delay: index * 55,               useNativeDriver: true }),
    ]).start();
  }, []);

  const onPressIn  = () => Animated.spring(scale, { toValue: 0.97, useNativeDriver: true }).start();
  const onPressOut = () => Animated.spring(scale, { toValue: 1,    useNativeDriver: true }).start();

  return (
    <Animated.View style={[{ opacity: op, transform: [{ translateX: slideX }, { scale }] }]}>
      <Pressable
        style={styles.histCard}
        onPressIn={onPressIn}
        onPressOut={onPressOut}
        onPress={onPress}
      >
        {/* Left accent bar */}
        <View style={[styles.histAccentBar, { backgroundColor: meta.accentColor }]} />

        {/* Thumbnail */}
        <View style={[styles.histThumb, { backgroundColor: meta.dim, borderColor: meta.border }]}>
          <Text style={{ fontSize: 22 }}>{meta.emoji}</Text>
        </View>

        {/* Body */}
        <View style={styles.histBody}>
          <Text style={styles.histName} numberOfLines={1}>{item.class_name}</Text>
          <Text style={styles.histConf}>Confidence: {item.confidence}%</Text>
          <Text style={styles.histDate}>🕐 {formatDateTime(item.created_at)}</Text>
        </View>

        {/* Right */}
        <View style={styles.histRight}>
          <View style={[styles.histBadge, { backgroundColor: meta.dim }]}>
            <Text style={[styles.histBadgeTxt, { color: meta.color }]}>{meta.label}</Text>
          </View>
          <Text style={styles.histChevron}>›</Text>
        </View>
      </Pressable>
    </Animated.View>
  );
}

// ── Empty state ───────────────────────────────────────────────────────────────
function EmptyState({ query }) {
  return (
    <View style={styles.empty}>
      <Text style={styles.emptyIcon}>{query ? '🔍' : '🌱'}</Text>
      <Text style={styles.emptyTxt}>
        {query
          ? `No results for "${query}".\nTry a different search term.`
          : 'No scan history yet.\nStart your first scan!'}
      </Text>
    </View>
  );
}

// ── Main Screen ───────────────────────────────────────────────────────────────
export default function HistoryScreen({ navigation, route }) {
  const { token }            = useContext(AuthContext);
  const { presentationMode } = useContext(UIThemeContext);

  const [history, setHistory] = useState([]);
  const [mode,    setMode]    = useState(route?.params?.initialMode === 'fruit' ? 'fruit' : 'nutrient');
  const [query,   setQuery]   = useState('');
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState('');

  // Mode toggle scale
  const nutrientScale = useRef(new Animated.Value(1)).current;
  const fruitScale    = useRef(new Animated.Value(1)).current;

  const switchMode = (m) => {
    const anim = m === 'nutrient' ? nutrientScale : fruitScale;
    Animated.sequence([
      Animated.timing(anim, { toValue: 0.93, duration: 80, useNativeDriver: true }),
      Animated.spring(anim, { toValue: 1,    useNativeDriver: true }),
    ]).start();
    setMode(m);
    setQuery('');
  };

  const fetchData = useCallback(async () => {
    if (!token) {
      setHistory([]);
      setError('Log in to view your scan history.');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const res = mode === 'fruit'
        ? await getFruitHistory(token)
        : await getHistory(token);
      setHistory(res.data.history || []);
    } catch (e) {
      setHistory([]);
      setError(
        e?.response?.data?.message ||
        e?.response?.data?.msg ||
        e?.message ||
        'Could not load history.'
      );
    } finally {
      setLoading(false);
    }
  }, [token, mode]);

  useFocusEffect(
    useCallback(() => {
      if (route?.params?.initialMode === 'fruit') setMode('fruit');
      if (route?.params?.initialMode === 'nutrient') setMode('nutrient');
      fetchData();
    }, [fetchData, route?.params?.initialMode])
  );

  useEffect(() => {
    fetchData();
  }, [mode, fetchData]);

  // Navigate to correct result screen
  const onPressItem = useCallback((item) => {
    if (mode === 'fruit') {
      navigation.navigate('FruitResult', {
        result: {
          class:       item.class_name,
          confidence:  item.confidence,
          warning:     item.warning,
          description: item.description,
          symptoms:    item.symptoms,
          solution:    item.solution,
          treatment:   item.treatment,
        },
        imageUri: item.image_uri || null,
      });
    } else {
      navigation.navigate('Result', {
        result: {
          class:       item.class_name,
          confidence:  item.confidence,
          description: item.description,
          symptoms:    item.symptoms,
          solution:    item.solution,
          fertilizer:  item.fertilizer,
        },
        imageUri: item.image_uri || null,
      });
    }
  }, [mode, navigation]);

  // Filter
  const filtered = history.filter(h =>
    h.class_name?.toLowerCase().includes(query.toLowerCase())
  );

  const totalHealthy = filtered.filter(h => getStatus(h.class_name, mode) === 'healthy').length;
  const totalIssues  = filtered.filter(h => getStatus(h.class_name, mode) !== 'healthy').length;

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" backgroundColor={C.bg} />

      {/* ── Header ── */}
      <View style={styles.header}>
        <View>
          <Text style={[styles.title, presentationMode && { fontSize: 28 }]}>Scan History</Text>
          <Text style={styles.headerSub}>{filtered.length} records total</Text>
        </View>
        <View style={styles.headerIcons}>
          <TouchableOpacity style={styles.iconBtn}>
            <Text style={styles.iconBtnTxt}>🔍</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.iconBtn}>
            <Text style={styles.iconBtnTxt}>⚙</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* ── Search ── */}
      <View style={styles.searchWrap}>
        <Text style={styles.searchIcon}>🔍</Text>
        <TextInput
          style={styles.searchInput}
          placeholder="Search by class name…"
          placeholderTextColor={C.muted}
          value={query}
          onChangeText={setQuery}
          selectionColor={C.accent}
        />
        {!!query && (
          <TouchableOpacity onPress={() => setQuery('')} style={styles.clearBtn}>
            <Text style={styles.clearBtnTxt}>✕</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* ── Mode toggle ── */}
      <View style={styles.modeRow}>
        {['nutrient', 'fruit'].map((m) => (
          <Animated.View
            key={m}
            style={[{ flex: 1 }, { transform: [{ scale: m === 'nutrient' ? nutrientScale : fruitScale }] }]}
          >
            <TouchableOpacity
              style={[styles.modeChip, mode === m && styles.modeChipActive]}
              onPress={() => switchMode(m)}
              activeOpacity={0.85}
            >
              <Text style={[styles.modeChipTxt, mode === m && styles.modeChipTxtActive]}>
                {m === 'nutrient' ? '🍃 Nutrient' : '🍅 Fruit Disease'}
              </Text>
            </TouchableOpacity>
          </Animated.View>
        ))}
      </View>

      {/* ── Summary strip ── */}
      <View style={styles.summaryRow}>
        <SummaryCard num={filtered.length} label="Total"   numColor={C.accent}  delay={0}  />
        <SummaryCard num={totalHealthy}    label="Healthy" numColor={C.success} delay={60} />
        <SummaryCard num={totalIssues}     label="Issues"  numColor={C.danger}  delay={120}/>
      </View>

      {/* ── Section label ── */}
      <Text style={styles.sectionLabel}>
        Recent — {mode === 'nutrient' ? 'Nutrient' : 'Fruit Disease'}
      </Text>

      {/* ── List ── */}
      {!!error && !loading && (
        <Text style={styles.errorText}>{error}</Text>
      )}
      <FlatList
        data={filtered}
        keyExtractor={item => String(item._id)}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
        refreshing={loading}
        onRefresh={fetchData}
        renderItem={({ item, index }) => (
          <HistoryItem
            item={item}
            mode={mode}
            index={index}
            onPress={() => onPressItem(item)}
          />
        )}
        ListEmptyComponent={<EmptyState query={query} />}
      />
    </View>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: C.bg },

  // Header
  header:      { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', paddingHorizontal: 18, paddingTop: 58, paddingBottom: 12 },
  title:       { fontSize: 24, fontWeight: '800', color: C.text },
  headerSub:   { fontSize: 11, color: C.muted, marginTop: 3 },
  headerIcons: { flexDirection: 'row', gap: 8 },
  iconBtn:     { width: 32, height: 32, backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: 16, alignItems: 'center', justifyContent: 'center' },
  iconBtnTxt:  { fontSize: 14 },

  // Search
  searchWrap:  { flexDirection: 'row', alignItems: 'center', marginHorizontal: 18, marginBottom: 12,
                 backgroundColor: C.surface, borderWidth: 1.5, borderColor: C.border, borderRadius: 12 },
  searchIcon:  { paddingLeft: 13, fontSize: 13 },
  searchInput: { flex: 1, padding: 11, paddingLeft: 8, color: C.text, fontSize: 13 },
  clearBtn:    { paddingRight: 13, paddingLeft: 4 },
  clearBtnTxt: { fontSize: 12, color: C.muted },

  // Mode
  modeRow:         { flexDirection: 'row', gap: 8, marginHorizontal: 18, marginBottom: 14 },
  modeChip:        { flex: 1, paddingVertical: 10, borderRadius: 12, borderWidth: 1.5, borderColor: C.border, backgroundColor: C.surface, alignItems: 'center' },
  modeChipActive:  { backgroundColor: C.accentDim, borderColor: C.accentBorder },
  modeChipTxt:     { fontSize: 12, fontWeight: '700', color: C.muted },
  modeChipTxtActive:{ color: C.accent },

  // Summary
  summaryRow: { flexDirection: 'row', gap: 8, marginHorizontal: 18, marginBottom: 14 },
  sumCard:    { flex: 1, backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: 14, padding: 10, alignItems: 'center' },
  sumNum:     { fontSize: 20, fontWeight: '800', lineHeight: 24 },
  sumLabel:   { fontSize: 9, color: C.muted, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.4, marginTop: 3 },

  // Section
  sectionLabel: { fontSize: 10, fontWeight: '700', color: C.muted, textTransform: 'uppercase', letterSpacing: 0.8, marginHorizontal: 20, marginBottom: 10 },
  errorText: { fontSize: 12, color: C.danger, marginHorizontal: 18, marginBottom: 10, lineHeight: 18 },

  // List
  listContent: { paddingHorizontal: 18, paddingBottom: 32 },

  // History card
  histCard:      { flexDirection: 'row', alignItems: 'center', gap: 12, backgroundColor: C.surface,
                   borderWidth: 1, borderColor: C.border, borderRadius: 18, padding: 14,
                   marginBottom: 10, overflow: 'hidden', position: 'relative' },
  histAccentBar: { position: 'absolute', left: 0, top: 0, bottom: 0, width: 3, borderRadius: 3 },
  histThumb:     { width: 48, height: 48, borderRadius: 12, borderWidth: 1, alignItems: 'center', justifyContent: 'center', flexShrink: 0 },
  histBody:      { flex: 1, minWidth: 0 },
  histName:      { fontSize: 13, fontWeight: '700', color: C.text },
  histConf:      { fontSize: 11, color: C.muted, marginTop: 2 },
  histDate:      { fontSize: 10, color: C.muted, marginTop: 3 },
  histRight:     { alignItems: 'flex-end', gap: 6 },
  histBadge:     { borderRadius: 100, paddingHorizontal: 9, paddingVertical: 3 },
  histBadgeTxt:  { fontSize: 9, fontWeight: '800', letterSpacing: 0.3 },
  histChevron:   { fontSize: 18, color: C.muted },
  // Empty
  empty:    { alignItems: 'center', paddingVertical: 48, gap: 12 },
  emptyIcon:{ fontSize: 44, opacity: 0.25 },
  emptyTxt: { fontSize: 13, color: C.muted, textAlign: 'center', lineHeight: 20 },
});
