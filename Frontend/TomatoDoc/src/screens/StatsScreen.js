import React, { useContext, useEffect, useRef, useState } from 'react';
import {
  Animated,
  Dimensions,
  Easing,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { BarChart, LineChart, PieChart } from 'react-native-chart-kit';
import { getStats } from '../api/historyApi';
import { getFruitStats } from '../api/fruitHistoryApi';
import { AuthContext } from '../context/AuthContext';
import { UIThemeContext } from '../context/UIThemeContext';

// ── Tokens ────────────────────────────────────────────────────────────────────
const C = {
  bg:           '#0f0f0f',
  surface:      '#1a1a1a',
  surface2:     '#222222',
  accent:       '#c8f135',
  accentDim:    'rgba(200,241,53,0.10)',
  accentBorder: 'rgba(200,241,53,0.22)',
  text:         '#f0f0f0',
  muted:        '#666666',
  border:       'rgba(255,255,255,0.07)',
  danger:       '#ff5c5c',
  dangerDim:    'rgba(255,92,92,0.10)',
  warn:         '#f5a623',
  warnDim:      'rgba(245,166,35,0.12)',
  success:      '#4adf6f',
  successDim:   'rgba(74,223,111,0.12)',
};

const CHART_PALETTE = [C.accent, C.success, C.warn, C.danger, '#7dd3fc'];

const SCREEN_W  = Dimensions.get('window').width;
const CHART_W   = SCREEN_W - 32;

// ── Chart config (dark-themed) ────────────────────────────────────────────────
const chartConfig = {
  backgroundGradientFrom:   C.surface,
  backgroundGradientTo:     C.surface,
  backgroundGradientFromOpacity: 1,
  backgroundGradientToOpacity:   1,
  decimalPlaces: 0,
  color:      (o = 1) => `rgba(200,241,53,${o})`,
  labelColor: ()      => C.muted,
  propsForBackgroundLines: { stroke: C.border },
  propsForDots: { r: '4', strokeWidth: '2', stroke: C.accent },
};

// ── Status label helpers ──────────────────────────────────────────────────────
const STATUS = {
  critical: { label: 'Critical', color: C.danger, dim: C.dangerDim },
  midRisk:  { label: 'Mid-risk', color: C.warn,   dim: C.warnDim   },
  normal:   { label: 'Normal',   color: C.success, dim: C.successDim },
};

// ── Animated KPI card ─────────────────────────────────────────────────────────
function KpiCard({ num, label, sub, accent = false, delay = 0 }) {
  const op = useRef(new Animated.Value(0)).current;
  const y  = useRef(new Animated.Value(16)).current;
  useEffect(() => {
    Animated.parallel([
      Animated.timing(op, { toValue: 1, duration: 380, delay, useNativeDriver: true }),
      Animated.spring(y,  { toValue: 0, delay,           useNativeDriver: true }),
    ]).start();
  }, [num]);
  return (
    <Animated.View style={[styles.kpiCard, accent && styles.kpiCardAccent, { opacity: op, transform: [{ translateY: y }] }]}>
      <Text style={[styles.kpiNum, accent && { color: '#0f0f0f' }]}>{num}</Text>
      <Text style={[styles.kpiLabel, accent && { color: 'rgba(0,0,0,0.45)' }]}>{label}</Text>
      {sub ? <Text style={[styles.kpiSub, accent && { color: 'rgba(0,0,0,0.45)' }]} numberOfLines={1}>{sub}</Text> : null}
    </Animated.View>
  );
}

// ── Section card wrapper ──────────────────────────────────────────────────────
function ChartCard({ title, children }) {
  return (
    <View style={styles.chartCard}>
      <Text style={styles.chartTitle}>{title}</Text>
      {children}
    </View>
  );
}

// ── History item ──────────────────────────────────────────────────────────────
function HistoryItem({ name, date, status }) {
  const meta = STATUS[status] ?? STATUS.normal;
  return (
    <View style={styles.histItem}>
      <View style={[styles.histDot, { backgroundColor: meta.color }]} />
      <View style={styles.histBody}>
        <Text style={styles.histName} numberOfLines={1}>{name}</Text>
        <Text style={styles.histDate}>{date}</Text>
      </View>
      <View style={[styles.histBadge, { backgroundColor: meta.dim }]}>
        <Text style={[styles.histBadgeTxt, { color: meta.color }]}>{meta.label}</Text>
      </View>
    </View>
  );
}

// ── Pie data builder ──────────────────────────────────────────────────────────
function buildPieData(classCounts) {
  return Object.entries(classCounts).map(([name, pop], i) => ({
    name,
    population: pop,
    color: CHART_PALETTE[i % CHART_PALETTE.length],
    legendFontColor: C.muted,
    legendFontSize: 11,
  }));
}

// ── Main Screen ───────────────────────────────────────────────────────────────
export default function StatsScreen({ route }) {
  const { token }            = useContext(AuthContext);
  const { presentationMode } = useContext(UIThemeContext);

  const [mode, setMode]   = useState(route?.params?.initialMode === 'fruit' ? 'fruit' : 'nutrient');
  const [stats, setStats] = useState({
    total_scans: 0,
    most_common_deficiency: 'N/A',
    class_counts: {},
    scans_per_day: [],
  });

  // Fetch on mode change
  useEffect(() => {
    (async () => {
      const res = mode === 'fruit'
        ? await getFruitStats(token)
        : await getStats(token);
      setStats(res.data);
    })();
  }, [token, mode]);

  const labels    = Object.keys(stats.class_counts);
  const values    = Object.values(stats.class_counts);
  const pieData   = buildPieData(stats.class_counts);
  const dayLabels = stats.scans_per_day.map(d => d.date.slice(5));
  const dayValues = stats.scans_per_day.map(d => d.count);

  // Mode toggle scale
  const nutrientScale = useRef(new Animated.Value(1)).current;
  const fruitScale    = useRef(new Animated.Value(1)).current;
  const animateChip = (anim) => {
    Animated.sequence([
      Animated.timing(anim, { toValue: 0.94, duration: 80, useNativeDriver: true }),
      Animated.spring(anim,  { toValue: 1,    useNativeDriver: true }),
    ]).start();
  };

  const switchMode = (m) => {
    animateChip(m === 'nutrient' ? nutrientScale : fruitScale);
    setMode(m);
  };

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" backgroundColor={C.bg} />

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        {/* ── Header ── */}
        <View style={styles.header}>
          <Text style={[styles.title, presentationMode && { fontSize: 28 }]}>Scan Statistics</Text>
          <View style={styles.headerIcons}>
            <TouchableOpacity style={styles.iconBtn}>
              <Text style={styles.iconBtnTxt}>⬇</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.iconBtn}>
              <Text style={styles.iconBtnTxt}>📈</Text>
            </TouchableOpacity>
          </View>
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

        {/* ── KPI row ── */}
        <View style={styles.kpiRow}>
          <KpiCard
            num={stats.total_scans}
            label="Total Scans"
            sub={`Most: ${stats.most_common_deficiency}`}
            accent
            delay={0}
          />
          <KpiCard
            num="85%"
            label="Avg Accuracy"
            sub="Last 30 days"
            delay={80}
          />
        </View>

        {/* ── Bar chart ── */}
        {labels.length > 0 && (
          <ChartCard title="Deficiency Breakdown">
            <BarChart
              data={{ labels, datasets: [{ data: values }] }}
              width={CHART_W - 32}
              height={200}
              chartConfig={chartConfig}
              fromZero
              showValuesOnTopOfBars
              style={styles.chartInner}
            />
          </ChartCard>
        )}

        {/* ── Pie chart ── */}
        {pieData.length > 0 && (
          <ChartCard title="Distribution">
            <PieChart
              data={pieData}
              width={CHART_W - 32}
              height={180}
              chartConfig={chartConfig}
              accessor="population"
              backgroundColor="transparent"
              paddingLeft="8"
              style={styles.chartInner}
            />
          </ChartCard>
        )}

        {/* ── Line chart ── */}
        {dayValues.length > 0 && (
          <ChartCard title="Scans Per Day">
            <LineChart
              data={{ labels: dayLabels, datasets: [{ data: dayValues }] }}
              width={CHART_W - 32}
              height={180}
              chartConfig={chartConfig}
              fromZero
              bezier
              style={styles.chartInner}
            />
          </ChartCard>
        )}

        {/* ── Recent history ── */}
        {stats.recent_history?.length > 0 && (
          <>
            <Text style={styles.sectionLabel}>Recent Scans</Text>
            <View style={styles.histList}>
              {stats.recent_history.map((item, i) => (
                <HistoryItem key={i} name={item.name} date={item.date} status={item.status} />
              ))}
            </View>
          </>
        )}
      </ScrollView>
    </View>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  root:    { flex: 1, backgroundColor: C.bg },
  scroll:  { flex: 1 },
  content: { padding: 16, gap: 14, paddingBottom: 40 },

  // Header
  header:      { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingTop: 8, paddingBottom: 4 },
  title:       { fontSize: 24, fontWeight: '800', color: C.text },
  headerIcons: { flexDirection: 'row', gap: 8 },
  iconBtn:     { width: 32, height: 32, backgroundColor: C.surface, borderWidth: 1, borderColor: C.border,
                 borderRadius: 16, alignItems: 'center', justifyContent: 'center' },
  iconBtnTxt:  { fontSize: 14 },

  // Mode toggle
  modeRow:         { flexDirection: 'row', gap: 8 },
  modeChip:        { flex: 1, paddingVertical: 10, borderRadius: 12, borderWidth: 1.5, borderColor: C.border,
                     backgroundColor: C.surface, alignItems: 'center' },
  modeChipActive:  { backgroundColor: C.accentDim, borderColor: C.accentBorder },
  modeChipTxt:     { fontSize: 12, fontWeight: '700', color: C.muted },
  modeChipTxtActive:{ color: C.accent },

  // KPI
  kpiRow:       { flexDirection: 'row', gap: 10 },
  kpiCard:      { flex: 1, backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: 16, padding: 14 },
  kpiCardAccent:{ backgroundColor: C.accent, borderColor: C.accent },
  kpiNum:       { fontSize: 28, fontWeight: '800', color: C.accent, lineHeight: 32 },
  kpiLabel:     { fontSize: 9, color: C.muted, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.5, marginTop: 4 },
  kpiSub:       { fontSize: 11, color: C.muted, marginTop: 5 },

  // Chart card
  chartCard:  { backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: 18, padding: 16 },
  chartTitle: { fontSize: 13, fontWeight: '700', color: C.text, marginBottom: 12 },
  chartInner: { borderRadius: 10, marginLeft: -8 },

  // Section
  sectionLabel: { fontSize: 10, fontWeight: '700', color: C.muted, textTransform: 'uppercase', letterSpacing: 0.8, marginLeft: 2, marginBottom: -4 },
  // History
  histList:   { gap: 8 },
  histItem:   { flexDirection: 'row', alignItems: 'center', gap: 10, backgroundColor: C.surface2, borderRadius: 12, padding: 10 },
  histDot:    { width: 8, height: 8, borderRadius: 4 },
  histBody:   { flex: 1, minWidth: 0 },
  histName:   { fontSize: 12, fontWeight: '600', color: C.text },
  histDate:   { fontSize: 10, color: C.muted, marginTop: 1 },
  histBadge:  { borderRadius: 100, paddingHorizontal: 8, paddingVertical: 2 },
  histBadgeTxt:{ fontSize: 9, fontWeight: '800', letterSpacing: 0.3 },
});
