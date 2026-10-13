import React, { useContext, useEffect, useRef, useState } from 'react';
import {
  Alert,
  Animated,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { nutrientDetails } from '../constants/nutrientDetails';
import { AuthContext } from '../context/AuthContext';
import { saveHistory } from '../api/historyApi';
import { computeSeverity } from '../utils/severity';
import { exportScanReport } from '../utils/reportExport';

import { palette as P, radius, shadow } from '../theme';
import ScreenHeader from '../components/ScreenHeader';
import { MaterialCommunityIcons } from '@expo/vector-icons';
// ── Tokens ────────────────────────────────────────────────────────────────────
const C = {
  bg: P.bg,
  surface: P.surface,
  surface2: P.surface2,
  accent: P.forestMid,
  accentDim: P.surfaceTint,
  accentBorder: '#CFE3B8',
  text: P.text,
  muted: P.muted,
  textSoft: P.textSoft,
  border: P.border,
  borderStrong: P.borderStrong,
  warn: P.warn,
  warnDim: P.warnDim,
  warnBorder:   'rgba(245,166,35,0.22)',
  blue: P.info,
  blueDim: P.infoDim,
  blueBorder:   'rgba(55,138,221,0.20)',
};

// ── Quick stat card ───────────────────────────────────────────────────────────
function QuickStat({ label, value, valueColor, delay = 0 }) {
  const op = useRef(new Animated.Value(0)).current;
  const y  = useRef(new Animated.Value(14)).current;
  useEffect(() => {
    Animated.parallel([
      Animated.timing(op, { toValue: 1, duration: 350, delay, useNativeDriver: true }),
      Animated.spring(y,  { toValue: 0, delay,           useNativeDriver: true }),
    ]).start();
  }, []);
  return (
    <Animated.View style={[styles.qstatCard, { opacity: op, transform: [{ translateY: y }] }]}>
      <Text style={styles.qstatLabel}>{label}</Text>
      <Text style={[styles.qstatValue, valueColor && { color: valueColor }]}>{value}</Text>
    </Animated.View>
  );
}

// ── Section card ──────────────────────────────────────────────────────────────
function SectionCard({ iconEmoji, iconStyle, title, children, delay = 0 }) {
  const op = useRef(new Animated.Value(0)).current;
  const y  = useRef(new Animated.Value(16)).current;
  useEffect(() => {
    Animated.parallel([
      Animated.timing(op, { toValue: 1, duration: 380, delay, useNativeDriver: true }),
      Animated.spring(y,  { toValue: 0, delay,           useNativeDriver: true }),
    ]).start();
  }, []);
  return (
    <Animated.View style={[styles.sectionCard, { opacity: op, transform: [{ translateY: y }] }]}>
      <View style={styles.sectionHeader}>
        <View style={[styles.sectionIcon, iconStyle]}>
          <Text style={{ fontSize: 15 }}>{iconEmoji}</Text>
        </View>
        <Text style={styles.sectionTitle}>{title}</Text>
      </View>
      {children}
    </Animated.View>
  );
}

// ── Treatment step ────────────────────────────────────────────────────────────
function TreatmentStep({ step, text, delay = 0 }) {
  const op = useRef(new Animated.Value(0)).current;
  const x  = useRef(new Animated.Value(-12)).current;
  useEffect(() => {
    Animated.parallel([
      Animated.timing(op, { toValue: 1, duration: 320, delay, useNativeDriver: true }),
      Animated.spring(x,  { toValue: 0, delay,           useNativeDriver: true }),
    ]).start();
  }, []);
  return (
    <Animated.View style={[styles.stepItem, { opacity: op, transform: [{ translateX: x }] }]}>
      <View style={styles.stepBadge}>
        <Text style={styles.stepBadgeTxt}>{step}</Text>
      </View>
      <Text style={styles.stepTxt}>{text}</Text>
    </Animated.View>
  );
}

// ── Dosage row ────────────────────────────────────────────────────────────────
function DosageRow({ text }) {
  return (
    <View style={styles.dosageRow}>
      <View style={styles.dosageDot} />
      <Text style={styles.dosageTxt}>{text}</Text>
    </View>
  );
}

// ── Main Screen ───────────────────────────────────────────────────────────────
export default function DetailScreen({ route, navigation }) {
  const { token } = useContext(AuthContext);
  const { className, result } = route.params;
  const [saved, setSaved] = useState(false);
  const detail = nutrientDetails[className] ?? nutrientDetails.Healthy;

  // Determine module type from className for badge label
  const isHealthy = className === 'Healthy' || className === 'Healthy_Tomato';

  // Hero entrance
  const heroOp = useRef(new Animated.Value(0)).current;
  const heroY  = useRef(new Animated.Value(24)).current;
  useEffect(() => {
    Animated.parallel([
      Animated.timing(heroOp, { toValue: 1, duration: 420, useNativeDriver: true }),
      Animated.spring(heroY,  { toValue: 0, useNativeDriver: true }),
    ]).start();
  }, []);

  // Parse dosage into lines if string, or use as-is if array
  const dosageLines = Array.isArray(detail.dosage)
    ? detail.dosage
    : (detail.dosage ?? '').split('\n').filter(Boolean);

  const stepCount = detail.treatment?.length ?? 0;
  const severity = computeSeverity(
    result || { class: className, confidence: 0 },
    'nutrient',
  );

  const onSave = async () => {
    if (saved) return;
    const payload = {
      class: className,
      confidence: result?.confidence ?? 0,
      description: result?.description || detail.title,
      symptoms: result?.symptoms || detail.visualSymptoms,
      solution: result?.solution || (detail.treatment?.join(' ') ?? ''),
      fertilizer: result?.fertilizer || (Array.isArray(detail.dosage) ? detail.dosage.join('; ') : (detail.dosage ?? '')),
    };
    await saveHistory(token, payload);
    setSaved(true);
    Alert.alert('Saved', 'Detail has been saved to history.');
  };

  const onExport = async () => {
    const fileUri = await exportScanReport({
      moduleName: 'Nutrient Deficiency',
      result: {
        class: className,
        confidence: result?.confidence ?? 0,
        description: result?.description || detail.title,
        symptoms: result?.symptoms || detail.visualSymptoms,
        solution: result?.solution || (detail.treatment?.join(' ') ?? ''),
        fertilizer: result?.fertilizer || (Array.isArray(detail.dosage) ? detail.dosage.join('; ') : (detail.dosage ?? '')),
      },
      imageUri: null,
      severity,
    });
    Alert.alert('Report exported', `Saved at:\n${fileUri}`);
  };

  return (
    <View style={styles.root}>
      <StatusBar barStyle="dark-content" backgroundColor={C.bg} />

      <ScreenHeader
        title="Treatment Guide"
        subtitle={detail.title}
        eyebrow="Nutrient module"
        onBack={() => navigation.goBack()}
        right={
          <TouchableOpacity style={styles.exportBtn} onPress={onExport} activeOpacity={0.75}>
            <MaterialCommunityIcons name="export-variant" size={20} color={P.lime} />
          </TouchableOpacity>
        }
      />

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        {/* ── Hero card ── */}
        <Animated.View style={[styles.heroCard, { opacity: heroOp, transform: [{ translateY: heroY }] }]}>
          <View style={styles.heroBlob} pointerEvents="none" />

          <View style={styles.heroBadge}>
            <View style={styles.badgeDot} />
            <Text style={styles.badgeTxt}>
              {isHealthy ? 'Healthy Plant' : 'Nutrient Deficiency'}
            </Text>
          </View>

          <Text style={styles.heroTitle}>{detail.title}</Text>
          <Text style={styles.heroSub} numberOfLines={3}>
            {detail.visualSymptoms}
          </Text>
        </Animated.View>

        {/* ── Quick stats ── */}
        <View style={styles.quickStats}>
          <QuickStat
            label="Recovery Time"
            value={detail.recoveryTime ?? '7–14 days'}
            valueColor={C.warn}
            delay={80}
          />
          <QuickStat
            label="Treatment Steps"
            value={`${stepCount} steps`}
            valueColor={C.accent}
            delay={140}
          />
        </View>

        {/* ── Visual Symptoms ── */}
        <SectionCard
          iconEmoji="👁"
          iconStyle={styles.iconWarn}
          title="Visual Symptoms Guide"
          delay={180}
        >
          <Text style={styles.sectionBody}>{detail.visualSymptoms}</Text>
        </SectionCard>

        {/* ── Treatment steps ── */}
        <SectionCard
          iconEmoji="🧪"
          iconStyle={styles.iconGreen}
          title="Step-by-Step Treatment Plan"
          delay={240}
        >
          {detail.treatment?.map((step, idx) => (
            <TreatmentStep
              key={idx}
              step={idx + 1}
              text={step}
              delay={idx * 60}
            />
          ))}
        </SectionCard>

        {/* ── Fertilizer dosage ── */}
        {dosageLines.length > 0 && (
          <SectionCard
            iconEmoji="💊"
            iconStyle={styles.iconBlue}
            title="Fertilizer Dosage"
            delay={320}
          >
            <View style={styles.dosageCard}>
              {dosageLines.map((line, i) => (
                <DosageRow key={i} text={line} />
              ))}
            </View>
          </SectionCard>
        )}

        {/* ── CTAs ── */}
        <TouchableOpacity style={[styles.btnPrimary, saved && styles.btnPrimaryDisabled]} activeOpacity={0.85} onPress={onSave} disabled={saved}>
          <Text style={styles.btnPrimaryIcon}>💾</Text>
          <Text style={styles.btnPrimaryTxt}>{saved ? 'Saved to History' : 'Save to History'}</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.btnOutline} activeOpacity={0.85} onPress={onExport}>
          <Text style={styles.btnOutlineIcon}>📄</Text>
          <Text style={styles.btnOutlineTxt}>Export as Report</Text>
        </TouchableOpacity>
      </ScrollView>
    </View>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  root:    { flex: 1, backgroundColor: C.bg },
  scroll:  { flex: 1 },
  content: { padding: 18, paddingTop: 18, paddingBottom: 120 },

  exportBtn: {
    width: 42, height: 42, borderRadius: 14,
    backgroundColor: 'rgba(214,239,117,0.14)', borderWidth: 1, borderColor: 'rgba(214,239,117,0.35)',
    alignItems: 'center', justifyContent: 'center',
  },

  // Hero
  heroCard: {
    backgroundColor: P.forestMid,
    borderRadius: radius.xl, padding: 20, marginBottom: 14, overflow: 'hidden', ...shadow.card,
  },
  heroBlob:  { position: 'absolute', top: -40, right: -40, width: 120, height: 120, borderRadius: 60, backgroundColor: P.lime, opacity: 0.14 },
  heroBadge: { flexDirection: 'row', alignItems: 'center', gap: 5, alignSelf: 'flex-start',
               backgroundColor: 'rgba(214,239,117,0.16)', borderWidth: 1, borderColor: 'rgba(214,239,117,0.35)',
               borderRadius: 100, paddingHorizontal: 10, paddingVertical: 4, marginBottom: 12 },
  badgeDot:  { width: 5, height: 5, borderRadius: 3, backgroundColor: P.lime },
  badgeTxt:  { fontSize: 10, color: P.lime, fontWeight: '700', letterSpacing: 0.4 },
  heroTitle: { fontSize: 24, fontWeight: '800', color: '#fff', lineHeight: 29, marginBottom: 8, letterSpacing: -0.5 },
  heroSub:   { fontSize: 13, color: 'rgba(255,255,255,0.78)', lineHeight: 19 },

  // Quick stats
  quickStats: { flexDirection: 'row', gap: 10, marginBottom: 14 },
  qstatCard:  { flex: 1, backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: radius.md, padding: 14, ...shadow.card },
  qstatLabel: { fontSize: 9, color: C.muted, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 4 },
  qstatValue: { fontSize: 16, fontWeight: '800', color: C.text },

  // Section card
  sectionCard:   { backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: radius.lg, padding: 16, marginBottom: 12, ...shadow.card },
  sectionHeader: { flexDirection: 'row', alignItems: 'center', gap: 9, marginBottom: 12 },
  sectionIcon:   { width: 30, height: 30, borderRadius: 9, alignItems: 'center', justifyContent: 'center' },
  iconGreen:     { backgroundColor: C.accentDim, borderWidth: 1, borderColor: C.accentBorder },
  iconWarn:      { backgroundColor: C.warnDim,   borderWidth: 1, borderColor: C.warnBorder   },
  iconBlue:      { backgroundColor: C.blueDim,   borderWidth: 1, borderColor: C.blueBorder   },
  sectionTitle:  { fontSize: 14, fontWeight: '800', color: C.text },
  sectionBody:   { fontSize: 12.5, color: C.textSoft, lineHeight: 20 },

  // Steps
  stepItem:     { flexDirection: 'row', gap: 10, alignItems: 'flex-start', marginBottom: 10 },
  stepBadge:    { width: 22, height: 22, borderRadius: 7, backgroundColor: C.accent, alignItems: 'center', justifyContent: 'center', marginTop: 1 },
  stepBadgeTxt: { fontSize: 10, fontWeight: '800', color: P.onDark },
  stepTxt:      { flex: 1, fontSize: 12.5, color: C.textSoft, lineHeight: 19 },

  // Dosage
  dosageCard:  { backgroundColor: C.accentDim, borderWidth: 1, borderColor: C.accentBorder, borderRadius: 12, padding: 12, gap: 7 },
  dosageRow:   { flexDirection: 'row', alignItems: 'flex-start', gap: 8 },
  dosageDot:   { width: 6, height: 6, borderRadius: 3, backgroundColor: C.accent, marginTop: 6 },
  dosageTxt:   { flex: 1, fontSize: 12, color: C.textSoft, lineHeight: 19 },

  // Buttons
  btnPrimary:    { backgroundColor: C.accent, borderRadius: radius.md, ...shadow.card, paddingVertical: 15, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7, marginBottom: 10 },
  btnPrimaryDisabled: { opacity: 0.65 },
  btnPrimaryIcon:{ fontSize: 15 },
  btnPrimaryTxt: { fontSize: 14, fontWeight: '800', color: P.onDark, letterSpacing: 0.3 },
  btnOutline:    { backgroundColor: C.surface, borderWidth: 1.5, borderColor: C.borderStrong, borderRadius: radius.md, paddingVertical: 13, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6 },
  btnOutlineIcon:{ fontSize: 14 },
  btnOutlineTxt: { fontSize: 13, fontWeight: '700', color: C.text },
});
