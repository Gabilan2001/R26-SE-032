import React, { useContext, useEffect, useRef, useState } from 'react';
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
import FruitResultCard from '../components/FruitResultCard';
import TreatmentAdviceCard from '../components/TreatmentAdviceCard';
import { saveFruitHistory } from '../api/fruitHistoryApi';
import { exportScanReport } from '../utils/reportExport';
import { AuthContext } from '../context/AuthContext';
import { UIThemeContext } from '../context/UIThemeContext';
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
  muted:        '#555555',
  border:       'rgba(255,255,255,0.07)',
  // Tomato-red palette (matches FruitScanScreen)
  tomato:       '#ff5c5c',
  tomatoDim:    'rgba(255,92,92,0.08)',
  tomatoBorder: 'rgba(255,92,92,0.22)',
  warn:         '#f5a623',
  warnDim:      'rgba(245,166,35,0.10)',
  success:      '#4adf6f',
  successDim:   'rgba(74,223,111,0.10)',
  successBorder:'rgba(74,223,111,0.22)',
};

// ── Severity config ───────────────────────────────────────────────────────────
const SEVERITY_MAP = {
  low:    { label: 'Low',      color: C.success, dim: C.successDim, pct: '28%' },
  medium: { label: 'Moderate', color: C.warn,    dim: C.warnDim,    pct: '62%' },
  high:   { label: 'High',     color: C.tomato,  dim: C.tomatoDim,  pct: '90%' },
};

// ── Healthy vs disease status ─────────────────────────────────────────────────
const isHealthy = (cls) => cls === 'Healthy_Tomato' || cls === 'Healthy';

// ── Animated severity bar ─────────────────────────────────────────────────────
function SeverityBar({ severity }) {
  const meta  = SEVERITY_MAP[severity] ?? SEVERITY_MAP.medium;
  const width = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    Animated.timing(width, {
      toValue: 1, duration: 700, delay: 300, useNativeDriver: false,
    }).start();
  }, []);
  return (
    <View style={styles.sevRow}>
      <Text style={styles.sevLabel}>Severity</Text>
      <View style={styles.sevTrack}>
        <Animated.View
          style={[
            styles.sevFill,
            {
              backgroundColor: meta.color,
              width: width.interpolate({ inputRange: [0, 1], outputRange: ['0%', meta.pct] }),
            },
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

// ── Detail item row ───────────────────────────────────────────────────────────
function DetailItem({ text, type = 'warning', delay = 0 }) {
  const op = useRef(new Animated.Value(0)).current;
  const x  = useRef(new Animated.Value(-12)).current;
  useEffect(() => {
    Animated.parallel([
      Animated.timing(op, { toValue: 1, duration: 340, delay, useNativeDriver: true }),
      Animated.spring(x,  { toValue: 0, delay,           useNativeDriver: true }),
    ]).start();
  }, []);
  const bulletColor = type === 'symptom' ? C.tomato : C.accent;
  const bulletDim   = type === 'symptom' ? C.tomatoDim : C.accentDim;
  const bulletBorder= type === 'symptom' ? C.tomatoBorder : C.accentBorder;
  const bulletLabel = type === 'symptom' ? '!' : '✓';
  return (
    <Animated.View style={[styles.detailItem, { opacity: op, transform: [{ translateX: x }] }]}>
      <View style={[styles.detailBullet, { backgroundColor: bulletDim, borderColor: bulletBorder }]}>
        <Text style={[styles.detailBulletTxt, { color: bulletColor }]}>{bulletLabel}</Text>
      </View>
      <Text style={styles.detailTxt}>{text}</Text>
    </Animated.View>
  );
}

// ── Main Screen ───────────────────────────────────────────────────────────────
export default function FruitResultScreen({ route, navigation }) {
  const { token }            = useContext(AuthContext);
  const { presentationMode } = useContext(UIThemeContext);
  const { result, imageUri } = route.params;
  const [saved, setSaved]    = useState(false);

  const severity = computeSeverity(result, 'fruit');
  const healthy  = isHealthy(result.class);
  const sevMeta  = SEVERITY_MAP[severity] ?? SEVERITY_MAP.medium;
  const symptomList = Array.isArray(result.symptoms)
    ? result.symptoms
    : String(result.symptoms || '')
        .split(/\r?\n|,\s*/)
        .map((s) => s.trim())
        .filter(Boolean);
  const treatmentList = Array.isArray(result.treatment)
    ? result.treatment
    : String(result.treatment || '')
        .split(/\r?\n|,\s*/)
        .map((s) => s.trim())
        .filter(Boolean);
  const confidencePct = Number(result.confidence || 0);

  // Entrance animations
  const bannerOp = useRef(new Animated.Value(0)).current;
  const bannerY  = useRef(new Animated.Value(28)).current;
  const cardOp   = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    Animated.parallel([
      Animated.timing(bannerOp, { toValue: 1, duration: 400, useNativeDriver: true }),
      Animated.spring(bannerY,  { toValue: 0, useNativeDriver: true }),
    ]).start(() =>
      Animated.timing(cardOp, { toValue: 1, duration: 350, useNativeDriver: true }).start()
    );
  }, []);

  // Button scale
  const btnScale = useRef(new Animated.Value(1)).current;
  const onPressIn  = () => Animated.spring(btnScale, { toValue: 0.97, useNativeDriver: true }).start();
  const onPressOut = () => Animated.spring(btnScale, { toValue: 1,    useNativeDriver: true }).start();

  const onSave = async () => {
    try {
      await saveFruitHistory(token, { ...result, image_uri: imageUri });
      setSaved(true);
    } catch (e) {
      Alert.alert('Save failed', e?.message || 'Could not save to history.');
    }
  };

  const onExport = async () => {
    try {
      const fileUri = await exportScanReport({
        moduleName: 'Fruit Disease',
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
          <View style={styles.backLeft}>
            <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()}>
              <Text style={styles.backArrow}>←</Text>
            </TouchableOpacity>
            <Text style={styles.screenTitle}>Disease Result</Text>
          </View>
          <TouchableOpacity style={styles.backBtn} onPress={onExport}>
            <Text style={styles.backArrow}>⬆</Text>
          </TouchableOpacity>
        </View>

        {/* ── Banner ── */}
        <Animated.View
          style={[styles.banner, { opacity: bannerOp, transform: [{ translateY: bannerY }] }]}
        >
          <View style={styles.bannerBlob} pointerEvents="none" />
          <View style={styles.bannerRow}>
            <Text style={[styles.bannerTitle, presentationMode && { fontSize: 17 }]}>
              Disease Management Panel
            </Text>
            <Text style={{ fontSize: 16 }}>🛡</Text>
          </View>
          <Text style={styles.bannerText}>
            Save and track disease trends for targeted spraying and better harvest quality.
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
                <Text style={{ fontSize: 60, opacity: 0.3 }}>🍅</Text>
              </View>
            )}
            <View style={styles.resultImageOverlay} />

            {/* Class chip — red for disease, green for healthy */}
            <View style={[styles.classChip, healthy && styles.classChipHealthy]}>
              <View style={[styles.classChipDot, healthy && { backgroundColor: C.success }]} />
              <Text style={[styles.classChipTxt, healthy && { color: C.success }]}>
                {healthy ? 'Healthy' : 'Fruit Disease'}
              </Text>
            </View>
          </View>

          <View style={styles.resultBody}>
            {/* Name */}
            <Text style={styles.resultName}>{result.class ?? 'Unknown'}</Text>

            {/* Confidence */}
            <View style={styles.confRow}>
              <Text style={styles.confLabel}>Confidence</Text>
              <View style={styles.confTrack}>
                <View
                  style={[
                    styles.confFill,
                    {
                  width: `${Math.max(0, Math.min(100, confidencePct))}%`,
                      backgroundColor: healthy ? C.success : C.tomato,
                    },
                  ]}
                />
              </View>
              <Text style={[styles.confPct, { color: healthy ? C.success : C.tomato }]}>
                {Math.round(confidencePct)}%
              </Text>
            </View>

            {/* Metrics */}
            <View style={styles.metricsGrid}>
              <MetricCard label="Disease"    value={result.class ?? '—'} valueColor={healthy ? C.success : C.tomato} />
              <MetricCard label="Confidence" value={`${Math.round(confidencePct)}%`} />
              <MetricCard label="Severity"   value={sevMeta.label} valueColor={sevMeta.color} />
              <MetricCard label="Module"     value="Fruit" />
            </View>

            {/* Existing FruitResultCard (keeps component) */}
            <FruitResultCard result={result} presentationMode={presentationMode} />

            <TreatmentAdviceCard predictedClass={result.class} variant="fruit" />

            {/* Symptoms */}
            {symptomList.length > 0 && (
              <>
                <Text style={styles.detailTitle}>Symptoms</Text>
                {symptomList.map((s, i) => (
                  <DetailItem key={i} text={s} type="symptom" delay={i * 70} />
                ))}
              </>
            )}

            {/* Treatment */}
            {treatmentList.length > 0 && (
              <>
                <Text style={[styles.detailTitle, { marginTop: 14 }]}>Treatment</Text>
                {treatmentList.map((t, i) => (
                  <DetailItem key={i} text={t} type="treatment" delay={i * 70} />
                ))}
              </>
            )}
          </View>
        </Animated.View>

        {/* ── Warning box (disease only) ── */}
        {!healthy && (
          <View style={styles.warningBox}>
            <Text style={styles.warningIcon}>⚠</Text>
            <Text style={styles.warningTxt}>
              Disease detected. Immediate treatment recommended to prevent spread to healthy plants.
            </Text>
          </View>
        )}

        {/* ── Primary CTA ── */}
        <Animated.View style={{ transform: [{ scale: btnScale }] }}>
          <Pressable
            style={styles.btnPrimary}
            onPressIn={onPressIn}
            onPressOut={onPressOut}
            onPress={() => navigation.navigate('FruitDetail', { result })}
          >
            <Text style={styles.btnPrimaryIcon}>🔍</Text>
            <Text style={styles.btnPrimaryTxt}>View Treatment Guide</Text>
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
        <TouchableOpacity style={styles.btnText} onPress={() => navigation.navigate('FruitScan')}>
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

  // Back
  backRow:   { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14, paddingTop: 4 },
  backLeft:  { flexDirection: 'row', alignItems: 'center', gap: 10 },
  backBtn:   { width: 32, height: 32, backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: 16, alignItems: 'center', justifyContent: 'center' },
  backArrow: { fontSize: 15, color: C.text },
  screenTitle: { fontSize: 18, fontWeight: '800', color: C.text },

  // Banner (tomato dark red)
  banner: {
    backgroundColor: '#1a0500',
    borderWidth: 1, borderColor: C.tomatoBorder,
    borderRadius: 20, padding: 16, marginBottom: 14, overflow: 'hidden',
  },
  bannerBlob:  { position: 'absolute', top: -30, right: -30, width: 100, height: 100, borderRadius: 50, backgroundColor: C.tomato, opacity: 0.07 },
  bannerRow:   { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  bannerTitle: { fontSize: 15, fontWeight: '800', color: C.text, flex: 1 },
  bannerText:  { fontSize: 12, color: 'rgba(255,255,255,0.45)', lineHeight: 18, marginBottom: 12 },

  // Severity
  sevRow:    { flexDirection: 'row', alignItems: 'center', gap: 8 },
  sevLabel:  { fontSize: 10, color: C.muted, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.5 },
  sevTrack:  { flex: 1, height: 5, backgroundColor: C.surface2, borderRadius: 3, overflow: 'hidden' },
  sevFill:   { height: '100%', borderRadius: 3 },
  sevPill:   { borderRadius: 100, paddingHorizontal: 8, paddingVertical: 2 },
  sevPillTxt:{ fontSize: 9, fontWeight: '800', letterSpacing: 0.3 },

  // Result card
  resultCard:            { backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: 20, overflow: 'hidden', marginBottom: 12 },
  resultImageWrap:       { width: '100%', height: 170, backgroundColor: '#1a0500', justifyContent: 'center', alignItems: 'center' },
  resultImage:           { position: 'absolute', width: '100%', height: '100%', resizeMode: 'cover' },
  resultImagePlaceholder:{ justifyContent: 'center', alignItems: 'center', position: 'relative' },
  resultImageOverlay:    { position: 'absolute', bottom: 0, left: 0, right: 0, height: 80, backgroundColor: 'transparent' },
  classChip:             { position: 'absolute', top: 12, left: 12, flexDirection: 'row', alignItems: 'center', gap: 5,
                           backgroundColor: 'rgba(255,92,92,0.15)', borderWidth: 1, borderColor: C.tomatoBorder,
                           borderRadius: 100, paddingHorizontal: 10, paddingVertical: 3 },
  classChipHealthy:      { backgroundColor: 'rgba(74,223,111,0.12)', borderColor: C.successBorder },
  classChipDot:          { width: 5, height: 5, borderRadius: 3, backgroundColor: C.tomato },
  classChipTxt:          { fontSize: 10, color: C.tomato, fontWeight: '700', letterSpacing: 0.3 },

  resultBody: { padding: 14 },
  resultName: { fontSize: 20, fontWeight: '800', color: C.text, marginBottom: 8 },

  confRow:   { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 14 },
  confLabel: { fontSize: 11, color: C.muted },
  confTrack: { flex: 1, height: 4, backgroundColor: C.surface2, borderRadius: 2, overflow: 'hidden' },
  confFill:  { height: '100%', borderRadius: 2 },
  confPct:   { fontSize: 11, fontWeight: '700' },

  metricsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 14 },
  metricCard:  { flex: 1, minWidth: '45%', backgroundColor: C.surface2, borderRadius: 12, padding: 10 },
  metricLabel: { fontSize: 9, color: C.muted, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 4 },
  metricValue: { fontSize: 17, fontWeight: '800', color: C.text },

  detailTitle: { fontSize: 10, color: C.muted, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.7, marginBottom: 8 },
  detailItem:  { flexDirection: 'row', gap: 9, alignItems: 'flex-start', marginBottom: 8 },
  detailBullet:{ width: 16, height: 16, borderRadius: 4, borderWidth: 1, alignItems: 'center', justifyContent: 'center', marginTop: 1 },
  detailBulletTxt: { fontSize: 8, fontWeight: '900' },
  detailTxt:   { flex: 1, fontSize: 12, color: 'rgba(255,255,255,0.62)', lineHeight: 18 },

  // Warning
  warningBox:  { flexDirection: 'row', gap: 9, alignItems: 'flex-start',
                 backgroundColor: C.tomatoDim, borderWidth: 1, borderColor: 'rgba(255,92,92,0.22)',
                 borderRadius: 12, padding: 12, marginBottom: 12 },
  warningIcon: { fontSize: 13, color: C.tomato, marginTop: 1 },
  warningTxt:  { flex: 1, fontSize: 11, color: C.tomato, lineHeight: 17 },

  // Buttons
  btnPrimary:    { backgroundColor: C.accent, borderRadius: 14, paddingVertical: 15,
                   flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7 },
  btnPrimaryIcon:{ fontSize: 15 },
  btnPrimaryTxt: { fontSize: 14, fontWeight: '800', color: '#0f0f0f', letterSpacing: 0.3 },

  btnRow:        { flexDirection: 'row', gap: 9, marginTop: 10 },
  btnOutline:    { flex: 1, backgroundColor: C.surface, borderWidth: 1.5, borderColor: C.border,
                   borderRadius: 14, paddingVertical: 13,
                   flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6 },
  btnOutlineSaved:{ opacity: 0.4 },
  btnOutlineIcon: { fontSize: 14 },
  btnOutlineTxt:  { fontSize: 13, fontWeight: '600', color: C.text },

  btnText:    { paddingVertical: 14, alignItems: 'center', marginTop: 4 },
  btnTextTxt: { fontSize: 13, fontWeight: '600', color: C.muted },
});