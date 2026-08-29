import React, { useContext, useRef, useEffect, useState } from 'react';
import {
  Alert,
  Animated,
  Image,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import TreatmentAdviceCard from '../components/TreatmentAdviceCard';
import { saveHistory } from '../api/historyApi';
import { exportScanReport } from '../utils/reportExport';
import { AuthContext } from '../context/AuthContext';
import { UIThemeContext } from '../context/UIThemeContext';
import { isLowConfidence } from '../utils/formatters';
import { computeSeverity } from '../utils/severity';

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

// ── Severity helpers ──────────────────────────────────────────────────────────
const SEVERITY_MAP = {
  low:    { label: 'Low',      color: C.success, dim: C.successDim, pct: '30%' },
  medium: { label: 'Moderate', color: C.warn,    dim: C.warnDim,    pct: '62%' },
  high:   { label: 'High',     color: C.danger,  dim: C.dangerDim,  pct: '88%' },
};

// ── Animated severity bar ─────────────────────────────────────────────────────
function SeverityBar({ severity }) {
  const meta  = SEVERITY_MAP[severity] ?? SEVERITY_MAP.medium;
  const width = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    Animated.timing(width, {
      toValue: 1,
      duration: 700,
      delay: 300,
      useNativeDriver: false,
    }).start();
  }, []);
  return (
    <View style={styles.sevRow}>
      <Text style={styles.sevLabel}>Severity</Text>
      <View style={styles.sevTrack}>
        <Animated.View
          style={[
            styles.sevFill,
            { backgroundColor: meta.color, width: width.interpolate({ inputRange: [0, 1], outputRange: ['0%', meta.pct] }) },
          ]}
        />
      </View>
      <View style={[styles.sevPill, { backgroundColor: meta.dim }]}>
        <Text style={[styles.sevPillTxt, { color: meta.color }]}>{meta.label}</Text>
      </View>
    </View>
  );
}

// ── Metric card ───────────────────────────────────────────────────────────────
function MetricCard({ label, value, valueColor }) {
  return (
    <View style={styles.metricCard}>
      <Text style={styles.metricLabel}>{label}</Text>
      <Text style={[styles.metricValue, valueColor && { color: valueColor }]}>{value}</Text>
    </View>
  );
}

// ── Recommendation row ────────────────────────────────────────────────────────
function RecItem({ text, delay = 0 }) {
  const op = useRef(new Animated.Value(0)).current;
  const x  = useRef(new Animated.Value(-12)).current;
  useEffect(() => {
    Animated.parallel([
      Animated.timing(op, { toValue: 1, duration: 350, delay, useNativeDriver: true }),
      Animated.spring(x,  { toValue: 0, delay, useNativeDriver: true }),
    ]).start();
  }, []);
  return (
    <Animated.View style={[styles.recItem, { opacity: op, transform: [{ translateX: x }] }]}>
      <View style={styles.recCheck}><Text style={styles.recCheckTxt}>✓</Text></View>
      <Text style={styles.recTxt}>{text}</Text>
    </Animated.View>
  );
}

// ── Main Screen ───────────────────────────────────────────────────────────────
export default function ResultScreen({ route, navigation }) {
  const { token }            = useContext(AuthContext);
  const { presentationMode } = useContext(UIThemeContext);
  const { result, imageUri } = route.params;
  const [saved, setSaved]    = useState(false);

  const severity = computeSeverity(result, 'nutrient');
  const lowConf  = isLowConfidence(result.confidence);

  // Entrance animations
  const cardOp = useRef(new Animated.Value(0)).current;
  const cardY  = useRef(new Animated.Value(28)).current;
  useEffect(() => {
    Animated.parallel([
      Animated.timing(cardOp, { toValue: 1, duration: 420, useNativeDriver: true }),
      Animated.spring(cardY,  { toValue: 0, useNativeDriver: true }),
    ]).start();
  }, []);

  // Button press scale
  const btnScale = useRef(new Animated.Value(1)).current;
  const onPressIn  = () => Animated.spring(btnScale, { toValue: 0.97, useNativeDriver: true }).start();
  const onPressOut = () => Animated.spring(btnScale, { toValue: 1,    useNativeDriver: true }).start();

  const onSave = async () => {
    try {
      await saveHistory(token, { ...result, image_uri: imageUri });
      setSaved(true);
    } catch (e) {
      Alert.alert('Save failed', e?.message || 'Could not save to history.');
    }
  };

  const onExport = async () => {
    try {
      const fileUri = await exportScanReport({
        moduleName: 'Nutrient Deficiency',
        result,
        imageUri,
        severity,
      });
      Alert.alert('Report Exported', `Saved at:\n${fileUri}`);
    } catch (e) {
      Alert.alert('Export failed', e?.message || 'Could not export report.');
    }
  };

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" backgroundColor={C.bg} />

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        {/* ── Back row ── */}
        <View style={styles.backRow}>
          <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()}>
            <Text style={styles.backArrow}>←</Text>
          </TouchableOpacity>
          <Text style={styles.screenTitle}>Scan Result</Text>
          <TouchableOpacity style={[styles.backBtn, { marginLeft: 'auto' }]} onPress={onExport}>
            <Text style={styles.backArrow}>⬆</Text>
          </TouchableOpacity>
        </View>

        {/* ── AI Banner ── */}
        <Animated.View style={[styles.banner, { opacity: cardOp, transform: [{ translateY: cardY }] }]}>
          {/* decorative blob */}
          <View style={styles.bannerBlob} pointerEvents="none" />

          <View style={styles.bannerRow}>
            <Text style={[styles.bannerTitle, presentationMode && { fontSize: 18 }]}>
              AI Recommendation Panel
            </Text>
            <Text style={{ fontSize: 16 }}>✦</Text>
          </View>
          <Text style={styles.bannerText}>
            Save this result to build your field history and monitor repeat deficiencies over time.
          </Text>
          <SeverityBar severity={severity} />
        </Animated.View>

        {/* ── Result card ── */}
        <Animated.View style={[styles.resultCard, { opacity: cardOp }]}>
          {/* Image / placeholder */}
          <View style={styles.resultImageWrap}>
            {imageUri ? (
              <Image source={{ uri: imageUri }} style={styles.resultImage} />
            ) : (
              <View style={[styles.resultImage, styles.resultImagePlaceholder]}>
                <Text style={{ fontSize: 60, opacity: 0.35 }}>🍃</Text>
              </View>
            )}
            <View style={styles.resultImageOverlay} />
            {/* Class chip */}
            <View style={styles.classChip}>
              <View style={styles.classChipDot} />
              <Text style={styles.classChipTxt}>Nutrient Deficiency</Text>
            </View>
          </View>

          <View style={styles.resultBody}>
            {/* Name + confidence */}
            <Text style={styles.resultName}>{result.class ?? 'Unknown'}</Text>
            <View style={styles.confRow}>
              <Text style={styles.confLabel}>Confidence</Text>
              <View style={styles.confTrack}>
                <View style={[styles.confFill, { width: `${Math.round((result.confidence ?? 0) * 100)}%` }]} />
              </View>
              <Text style={styles.confPct}>
                {Math.round((result.confidence ?? 0) * 100)}%
              </Text>
            </View>

            {/* Metrics grid */}
            <View style={styles.metricsGrid}>
              <MetricCard label="Class"      value={result.class ?? '—'} valueColor={C.accent} />
              <MetricCard label="Confidence" value={`${Math.round((result.confidence ?? 0) * 100)}%`} />
              <MetricCard label="Severity"   value={SEVERITY_MAP[severity]?.label ?? '—'} valueColor={SEVERITY_MAP[severity]?.color} />
              <MetricCard label="Module"     value="Nutrient" />
            </View>

            <TreatmentAdviceCard predictedClass={result.class} />

            {/* Recommendations */}
            {result.recommendations?.length > 0 && (
              <>
                <Text style={styles.recsTitle}>Recommendations</Text>
                {result.recommendations.map((r, i) => (
                  <RecItem key={i} text={r} delay={i * 80} />
                ))}
              </>
            )}
          </View>
        </Animated.View>

        {/* ── Low confidence warning ── */}
        {lowConf && (
          <View style={styles.warningBox}>
            <Text style={styles.warningIcon}>⚠</Text>
            <Text style={styles.warningTxt}>
              Confidence is below 70%. Please re-scan in better lighting for a more accurate result.
            </Text>
          </View>
        )}

        {/* ── Primary CTA ── */}
        <Animated.View style={{ transform: [{ scale: btnScale }] }}>
          <Pressable
            style={styles.btnPrimary}
            onPressIn={onPressIn}
            onPressOut={onPressOut}
            onPress={() => navigation.navigate('Detail', { className: result.class, result })}
          >
            <Text style={styles.btnPrimaryIcon}>🔍</Text>
            <Text style={styles.btnPrimaryTxt}>View Full Detail</Text>
          </Pressable>
        </Animated.View>

        {/* ── Secondary row ── */}
        <View style={styles.btnRow}>
          <TouchableOpacity
            style={[styles.btnOutline, saved && styles.btnOutlineSaved]}
            onPress={onSave}
            disabled={saved}
            activeOpacity={0.8}
          >
            <Text style={styles.btnOutlineIcon}>{saved ? '✓' : '💾'}</Text>
            <Text style={[styles.btnOutlineTxt, saved && { color: C.muted }]}>
              {saved ? 'Saved' : 'Save'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.btnOutline} onPress={onExport} activeOpacity={0.8}>
            <Text style={styles.btnOutlineIcon}>📄</Text>
            <Text style={styles.btnOutlineTxt}>Export .txt</Text>
          </TouchableOpacity>
        </View>

        {/* ── Text CTA ── */}
        <TouchableOpacity style={styles.btnText} onPress={() => navigation.navigate('Scan')}>
          <Text style={styles.btnTextTxt}>↩  Analyze Another</Text>
        </TouchableOpacity>
      </ScrollView>
    </View>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  root:    { flex: 1, backgroundColor: C.bg },
  scroll:  { flex: 1 },
  content: { padding: 18, paddingBottom: 40 },

  // Back row
  backRow:   { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 14, paddingTop: 4 },
  backBtn:   { width: 32, height: 32, backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: 16, alignItems: 'center', justifyContent: 'center' },
  backArrow: { fontSize: 15, color: C.text },
  screenTitle: { fontSize: 18, fontWeight: '800', color: C.text },

  // Banner
  banner: {
    backgroundColor: '#0f1a00',
    borderWidth: 1, borderColor: C.accentBorder,
    borderRadius: 20, padding: 16, marginBottom: 14, overflow: 'hidden',
  },
  bannerBlob: { position: 'absolute', top: -30, right: -30, width: 100, height: 100, borderRadius: 50, backgroundColor: C.accent, opacity: 0.07 },
  bannerRow:  { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  bannerTitle:{ fontSize: 15, fontWeight: '800', color: C.text },
  bannerText: { fontSize: 12, color: 'rgba(255,255,255,0.5)', lineHeight: 18, marginBottom: 12 },

  // Severity
  sevRow:    { flexDirection: 'row', alignItems: 'center', gap: 8 },
  sevLabel:  { fontSize: 10, color: C.muted, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.5 },
  sevTrack:  { flex: 1, height: 5, backgroundColor: C.surface2, borderRadius: 3, overflow: 'hidden' },
  sevFill:   { height: '100%', borderRadius: 3 },
  sevPill:   { borderRadius: 100, paddingHorizontal: 8, paddingVertical: 2 },
  sevPillTxt:{ fontSize: 9, fontWeight: '800', letterSpacing: 0.3 },

  // Result card
  resultCard: { backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: 20, overflow: 'hidden', marginBottom: 12 },
  resultImageWrap:       { width: '100%', height: 170, backgroundColor: '#0a1400', justifyContent: 'center', alignItems: 'center' },
  resultImage:           { position: 'absolute', width: '100%', height: '100%', resizeMode: 'cover' },
  resultImagePlaceholder:{ justifyContent: 'center', alignItems: 'center', position: 'relative' },
  resultImageOverlay:    { position: 'absolute', bottom: 0, left: 0, right: 0, height: 80,
                           backgroundColor: 'transparent',
                           /* gradient via nested view */ },
  classChip:    { position: 'absolute', top: 12, left: 12, flexDirection: 'row', alignItems: 'center', gap: 5,
                  backgroundColor: 'rgba(200,241,53,0.15)', borderWidth: 1, borderColor: C.accentBorder,
                  borderRadius: 100, paddingHorizontal: 10, paddingVertical: 3 },
  classChipDot: { width: 5, height: 5, borderRadius: 3, backgroundColor: C.accent },
  classChipTxt: { fontSize: 10, color: C.accent, fontWeight: '700', letterSpacing: 0.3 },

  resultBody: { padding: 14 },
  resultName: { fontSize: 20, fontWeight: '800', color: C.text, marginBottom: 8 },

  // Confidence bar
  confRow:   { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 14 },
  confLabel: { fontSize: 11, color: C.muted },
  confTrack: { flex: 1, height: 4, backgroundColor: C.surface2, borderRadius: 2, overflow: 'hidden' },
  confFill:  { height: '100%', backgroundColor: C.accent, borderRadius: 2 },
  confPct:   { fontSize: 11, fontWeight: '700', color: C.accent },

  // Metrics
  metricsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 14 },
  metricCard:  { flex: 1, minWidth: '45%', backgroundColor: C.surface2, borderRadius: 12, padding: 10 },
  metricLabel: { fontSize: 9, color: C.muted, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 4 },
  metricValue: { fontSize: 17, fontWeight: '800', color: C.text },

  // Recs
  recsTitle: { fontSize: 10, color: C.muted, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.7, marginBottom: 10 },
  recItem:   { flexDirection: 'row', gap: 10, alignItems: 'flex-start', marginBottom: 9 },
  recCheck:  { width: 18, height: 18, borderRadius: 5, backgroundColor: C.accentDim, borderWidth: 1,
               borderColor: C.accentBorder, alignItems: 'center', justifyContent: 'center', marginTop: 1 },
  recCheckTxt:{ fontSize: 9, color: C.accent, fontWeight: '800' },
  recTxt:    { flex: 1, fontSize: 12, color: 'rgba(255,255,255,0.65)', lineHeight: 18 },

  // Warning
  warningBox:  { flexDirection: 'row', gap: 9, alignItems: 'flex-start', backgroundColor: C.warnDim,
                 borderWidth: 1, borderColor: 'rgba(245,166,35,0.25)', borderRadius: 12, padding: 12, marginBottom: 12 },
  warningIcon: { fontSize: 13, color: C.warn, marginTop: 1 },
  warningTxt:  { flex: 1, fontSize: 11, color: C.warn, lineHeight: 17 },

  // Buttons
  btnPrimary:    { backgroundColor: C.accent, borderRadius: 14, paddingVertical: 15, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8 },
  btnPrimaryIcon:{ fontSize: 15 },
  btnPrimaryTxt: { fontSize: 14, fontWeight: '800', color: '#0f0f0f', letterSpacing: 0.3 },

  btnRow:        { flexDirection: 'row', gap: 9, marginTop: 10 },
  btnOutline:    { flex: 1, backgroundColor: C.surface, borderWidth: 1.5, borderColor: C.border,
                   borderRadius: 14, paddingVertical: 13, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6 },
  btnOutlineSaved:{ opacity: 0.4 },
  btnOutlineIcon: { fontSize: 14 },
  btnOutlineTxt:  { fontSize: 13, fontWeight: '600', color: C.text },
  btnText:    { paddingVertical: 14, alignItems: 'center', marginTop: 4 },
  btnTextTxt: { fontSize: 13, fontWeight: '600', color: C.muted },
});
