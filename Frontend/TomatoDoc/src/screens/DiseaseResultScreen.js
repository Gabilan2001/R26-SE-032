import React, { useContext, useEffect, useRef } from 'react';
import {
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
import { UIThemeContext } from '../context/UIThemeContext';

// ── Tokens ────────────────────────────────────────────────────────────────────
const C = {
  bg:           '#0f0f0f',
  surface:      '#1a1a1a',
  surface2:     '#222222',
  accent:       '#c8f135',
  text:         '#f0f0f0',
  muted:        '#555555',
  border:       'rgba(255,255,255,0.07)',
  amber:        '#f5a623',
  amberDim:     'rgba(245,166,35,0.08)',
  amberBorder:  'rgba(245,166,35,0.22)',
  success:      '#4adf6f',
  successDim:   'rgba(74,223,111,0.10)',
  successBorder:'rgba(74,223,111,0.22)',
  warnBg:       'rgba(255,92,92,0.10)',
  warnBorder:   'rgba(255,92,92,0.25)',
  warn:         '#ff5c5c',
};

// Matches CLASS_COLORS_BGR in app_mobile.py (converted BGR -> RGB hex)
const CLASS_COLORS = {
  Early_Blight: '#ff6432',
  Late_Blight:  '#32b4ff',
  Healthy:      '#3cc83c',
  Leaf_Miner:   '#ffa500',
};

// ── Lightweight renderer for the Gemini treatment text ────────────────────────
// Handles the light markdown Gemini tends to produce (### headers, **bold**,
// bullet lines, horizontal rules) without pulling in a markdown dependency.
function renderInlineBold(text, keyPrefix) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g).filter(Boolean);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <Text key={`${keyPrefix}-${i}`} style={styles.treatBold}>
          {part.slice(2, -2)}
        </Text>
      );
    }
    return <Text key={`${keyPrefix}-${i}`}>{part}</Text>;
  });
}

function TreatmentText({ text }) {
  const lines = text.split(/\r?\n/);
  return (
    <View>
      {lines.map((line, i) => {
        const trimmed = line.trim();
        if (!trimmed || /^-{3,}$/.test(trimmed)) return null;
        if (trimmed.startsWith('### ')) {
          return (
            <Text key={i} style={styles.treatH3}>{trimmed.replace(/^###\s*/, '')}</Text>
          );
        }
        if (/^[-*]\s+/.test(trimmed)) {
          return (
            <View key={i} style={styles.treatBulletRow}>
              <Text style={styles.treatBulletDot}>•</Text>
              <Text style={styles.treatBody}>
                {renderInlineBold(trimmed.replace(/^[-*]\s+/, ''), `l${i}`)}
              </Text>
            </View>
          );
        }
        if (/^\d+\.\s+/.test(trimmed)) {
          return (
            <View key={i} style={styles.treatBulletRow}>
              <Text style={styles.treatBulletDot}>{trimmed.match(/^\d+/)[0]}.</Text>
              <Text style={styles.treatBody}>
                {renderInlineBold(trimmed.replace(/^\d+\.\s+/, ''), `l${i}`)}
              </Text>
            </View>
          );
        }
        return (
          <Text key={i} style={[styles.treatBody, { marginBottom: 8 }]}>
            {renderInlineBold(trimmed, `l${i}`)}
          </Text>
        );
      })}
    </View>
  );
}

function DiseaseChip({ name }) {
  const color = CLASS_COLORS[name] || C.muted;
  const healthy = name === 'Healthy';
  return (
    <View style={[styles.diseaseChip, { borderColor: color + '55', backgroundColor: color + '18' }]}>
      <View style={[styles.diseaseChipDot, { backgroundColor: color }]} />
      <Text style={[styles.diseaseChipTxt, { color }]}>
        {healthy ? 'Healthy' : name.replace('_', ' ')}
      </Text>
    </View>
  );
}

// ── Main Screen ───────────────────────────────────────────────────────────────
export default function DiseaseResultScreen({ route, navigation }) {
  const { presentationMode } = useContext(UIThemeContext);
  const { result, imageUri } = route.params;

  const diseasesFound = result.diseases_found || [];
  const onlyHealthy = diseasesFound.length === 1 && diseasesFound[0] === 'Healthy';
  const hasProblem = diseasesFound.some((d) => d !== 'Healthy');

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

  const btnScale = useRef(new Animated.Value(1)).current;
  const onPressIn  = () => Animated.spring(btnScale, { toValue: 0.97, useNativeDriver: true }).start();
  const onPressOut = () => Animated.spring(btnScale, { toValue: 1,    useNativeDriver: true }).start();

  const displayImage = result.annotated_image
    ? `data:image/jpeg;base64,${result.annotated_image}`
    : imageUri;

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" backgroundColor={C.bg} />
      <ScrollView style={styles.scroll} contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        {/* ── Back row ── */}
        <View style={styles.backRow}>
          <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()}>
            <Text style={styles.backArrow}>←</Text>
          </TouchableOpacity>
          <Text style={styles.screenTitle}>Disease Result</Text>
        </View>

        {/* ── Banner ── */}
        <Animated.View style={[styles.banner, { opacity: bannerOp, transform: [{ translateY: bannerY }] }]}>
          <View style={styles.bannerBlob} pointerEvents="none" />
          <Text style={[styles.bannerTitle, presentationMode && { fontSize: 17 }]}>
            {onlyHealthy ? '✅ Leaf looks healthy' : hasProblem ? '🦠 Issue(s) Detected' : 'Scan Complete'}
          </Text>
          <Text style={styles.bannerText}>
            {onlyHealthy
              ? 'No disease or pest symptoms found on this leaf.'
              : `${diseasesFound.length} class${diseasesFound.length !== 1 ? 'es' : ''} detected across ${result.total_boxes || 0} region(s).`}
          </Text>
          <View style={styles.chipRow}>
            {diseasesFound.map((d) => <DiseaseChip key={d} name={d} />)}
          </View>
        </Animated.View>

        {/* ── Annotated image ── */}
        <Animated.View style={[styles.resultCard, { opacity: cardOp }]}>
          <View style={styles.resultImageWrap}>
            {displayImage ? (
              <Image source={{ uri: displayImage }} style={styles.resultImage} />
            ) : (
              <View style={[styles.resultImage, styles.resultImagePlaceholder]}>
                <Text style={{ fontSize: 60, opacity: 0.3 }}>🍃</Text>
              </View>
            )}
          </View>
          {result.annotated_image && (
            <Text style={styles.imageCaption}>Boxes show detected regions, color-coded by class</Text>
          )}
        </Animated.View>

        {/* ── Co-occurrence warning ── */}
        {result.co_occurrence && (
          <View style={styles.warningBox}>
            <Text style={styles.warningIcon}>⚠</Text>
            <Text style={styles.warningTxt}>
              Multiple issues detected on the same plant — see the treatment section below for whether
              they can be handled together or need separate sprays.
            </Text>
          </View>
        )}

        {/* ── Treatment ── */}
        {result.treatment?.answer && (
          <View style={styles.treatCard}>
            <Text style={styles.treatCardTitle}>💊 Treatment Guidance</Text>
            <TreatmentText text={result.treatment.answer} />

            {Array.isArray(result.treatment.sources) && result.treatment.sources.length > 0 && (
              <View style={styles.sourcesBox}>
                <Text style={styles.sourcesTitle}>Sources</Text>
                {result.treatment.sources.map((s, i) => (
                  <Text key={i} style={styles.sourceLine}>• {s}</Text>
                ))}
              </View>
            )}
          </View>
        )}

        {/* ── Text CTA ── */}
        <Animated.View style={{ transform: [{ scale: btnScale }] }}>
          <Pressable
            style={styles.btnPrimary}
            onPressIn={onPressIn}
            onPressOut={onPressOut}
            onPress={() => navigation.navigate('DiseaseScan')}
          >
            <Text style={styles.btnPrimaryIcon}>↩</Text>
            <Text style={styles.btnPrimaryTxt}>Scan Another Leaf</Text>
          </Pressable>
        </Animated.View>
      </ScrollView>
    </View>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  root:    { flex: 1, backgroundColor: C.bg },
  scroll:  { flex: 1 },
  content: { padding: 18, paddingBottom: 40 },

  backRow:   { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 14, paddingTop: 4 },
  backBtn:   { width: 32, height: 32, backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: 16, alignItems: 'center', justifyContent: 'center' },
  backArrow: { fontSize: 15, color: C.text },
  screenTitle: { fontSize: 18, fontWeight: '800', color: C.text },

  banner: {
    backgroundColor: '#1a1200',
    borderWidth: 1, borderColor: C.amberBorder,
    borderRadius: 20, padding: 16, marginBottom: 14, overflow: 'hidden',
  },
  bannerBlob:  { position: 'absolute', top: -30, right: -30, width: 100, height: 100, borderRadius: 50, backgroundColor: C.amber, opacity: 0.07 },
  bannerTitle: { fontSize: 16, fontWeight: '800', color: C.text, marginBottom: 6 },
  bannerText:  { fontSize: 12, color: 'rgba(255,255,255,0.5)', lineHeight: 18, marginBottom: 12 },

  chipRow: { flexDirection: 'row', gap: 7, flexWrap: 'wrap' },
  diseaseChip:    { flexDirection: 'row', alignItems: 'center', gap: 6, borderWidth: 1, borderRadius: 100, paddingHorizontal: 11, paddingVertical: 5 },
  diseaseChipDot: { width: 6, height: 6, borderRadius: 3 },
  diseaseChipTxt: { fontSize: 11, fontWeight: '700' },

  resultCard: { backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: 20, overflow: 'hidden', marginBottom: 6 },
  resultImageWrap: { width: '100%', height: 260, backgroundColor: '#0a1400', justifyContent: 'center', alignItems: 'center' },
  resultImage: { width: '100%', height: '100%', resizeMode: 'contain' },
  resultImagePlaceholder: { justifyContent: 'center', alignItems: 'center' },
  imageCaption: { fontSize: 10, color: C.muted, textAlign: 'center', padding: 8 },

  warningBox:  { flexDirection: 'row', gap: 9, alignItems: 'flex-start',
                 backgroundColor: C.warnBg, borderWidth: 1, borderColor: C.warnBorder,
                 borderRadius: 12, padding: 12, marginTop: 14, marginBottom: 4 },
  warningIcon: { fontSize: 13, color: C.warn, marginTop: 1 },
  warningTxt:  { flex: 1, fontSize: 11, color: C.warn, lineHeight: 17 },

  treatCard: { backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: 20, padding: 16, marginTop: 14, marginBottom: 16 },
  treatCardTitle: { fontSize: 15, fontWeight: '800', color: C.text, marginBottom: 12 },
  treatH3:   { fontSize: 13, fontWeight: '800', color: C.amber, marginTop: 10, marginBottom: 6 },
  treatBody: { fontSize: 12.5, color: 'rgba(255,255,255,0.75)', lineHeight: 19 },
  treatBold: { fontWeight: '800', color: C.text },
  treatBulletRow: { flexDirection: 'row', gap: 7, marginBottom: 6, alignItems: 'flex-start' },
  treatBulletDot: { fontSize: 12.5, color: C.amber, fontWeight: '800', minWidth: 14 },

  sourcesBox: { marginTop: 14, paddingTop: 12, borderTopWidth: 1, borderTopColor: C.border },
  sourcesTitle: { fontSize: 10, fontWeight: '700', color: C.muted, textTransform: 'uppercase', letterSpacing: 0.7, marginBottom: 6 },
  sourceLine: { fontSize: 10.5, color: C.muted, lineHeight: 16, marginBottom: 3 },

  btnPrimary:    { backgroundColor: C.accent, borderRadius: 14, paddingVertical: 15,
                   flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7 },
  btnPrimaryIcon:{ fontSize: 15 },
  btnPrimaryTxt: { fontSize: 14, fontWeight: '800', color: '#0f0f0f', letterSpacing: 0.3 },
});
