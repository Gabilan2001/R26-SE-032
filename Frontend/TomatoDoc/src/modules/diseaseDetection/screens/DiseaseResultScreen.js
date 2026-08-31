import React, { useContext, useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
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
import { UIThemeContext } from '../../../context/UIThemeContext';
import DiseaseChip from '../components/DiseaseChip';
import { getTreatment } from '../api/scan';

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

// ── Main Screen ───────────────────────────────────────────────────────────────
export default function DiseaseResultScreen({ route, navigation }) {
  const { presentationMode } = useContext(UIThemeContext);
  const { result, imageUri } = route.params;

  const diseasesFound = result.diseases_found || [];
  const onlyHealthy = diseasesFound.length === 1 && diseasesFound[0] === 'Healthy';
  const hasProblem = diseasesFound.some((d) => d !== 'Healthy');
  // Covers blank-image / not-a-leaf / no-detection -- backend sets
  // valid: false and a human-readable `error` string for all of these.
  const isInvalid = result.valid === false;

  // Treatment arrives separately (see api/scan.js's getTreatment) so this
  // screen can show the detection the instant /predict returns instead of
  // waiting up to ~90s for the RAG/Gemini call too. Still fires for
  // Healthy-only results (so the scan gets recorded in history), just
  // without showing a loading spinner for it -- there's nothing to wait
  // for from the user's point of view in that case.
  const [treatment, setTreatment] = useState(result.treatment || null);
  const [treatmentLoading, setTreatmentLoading] = useState(!!result.valid);
  useEffect(() => {
    // Only for an actual successful detection -- result.valid is false for
    // the blank-image/not-a-leaf/no-detection error cases, which never had
    // a history record saved before either (the backend's old single-call
    // /predict returned before reaching save_scan_history for those).
    // Calling /treatment unconditionally here would start saving junk
    // history entries for them now that saving lives in that endpoint.
    if (!result.valid) return;
    let cancelled = false;
    getTreatment(result.detections, diseasesFound, result.co_occurrence)
      .then((res) => {
        if (!cancelled) setTreatment(res.data.treatment);
      })
      .catch(() => {
        if (!cancelled) setTreatment(null);
      })
      .finally(() => {
        if (!cancelled) setTreatmentLoading(false);
      });
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
        <Animated.View style={[styles.banner, isInvalid && styles.bannerInvalid, { opacity: bannerOp, transform: [{ translateY: bannerY }] }]}>
          <View style={[styles.bannerBlob, isInvalid && styles.bannerBlobInvalid]} pointerEvents="none" />
          <Text style={[styles.bannerTitle, presentationMode && { fontSize: 17 }]}>
            {isInvalid ? '⚠️ Could Not Analyze' : onlyHealthy ? '✅ Leaf looks healthy' : hasProblem ? '🦠 Issue(s) Detected' : 'Scan Complete'}
          </Text>
          <Text style={styles.bannerText}>
            {isInvalid
              ? (result.error || 'Please upload a clear photo of a tomato leaf.')
              : onlyHealthy
              ? 'No disease or pest symptoms found on this leaf.'
              : `${diseasesFound.length} class${diseasesFound.length !== 1 ? 'es' : ''} detected across ${result.total_boxes || 0} region(s).`}
          </Text>
          {!isInvalid && (
            <View style={styles.chipRow}>
              {diseasesFound.map((d) => <DiseaseChip key={d} name={d} />)}
            </View>
          )}
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
        {hasProblem && (
          <View style={styles.treatCard}>
            <Text style={styles.treatCardTitle}>💊 Treatment Guidance</Text>
            {treatmentLoading ? (
              <View style={styles.treatLoadingRow}>
                <ActivityIndicator color={C.amber} />
                <Text style={styles.treatLoadingTxt}>Fetching treatment advice… (can take up to a minute)</Text>
              </View>
            ) : treatment?.answer ? (
              <>
                <TreatmentText text={treatment.answer} />
                {Array.isArray(treatment.sources) && treatment.sources.length > 0 && (
                  <View style={styles.sourcesBox}>
                    <Text style={styles.sourcesTitle}>Sources</Text>
                    {treatment.sources.map((s, i) => (
                      <Text key={i} style={styles.sourceLine}>• {s}</Text>
                    ))}
                  </View>
                )}
              </>
            ) : (
              <Text style={styles.treatErrorTxt}>Couldn't load treatment advice right now.</Text>
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
  bannerInvalid: { backgroundColor: '#1a0d0d', borderColor: C.warnBorder },
  bannerBlob:  { position: 'absolute', top: -30, right: -30, width: 100, height: 100, borderRadius: 50, backgroundColor: C.amber, opacity: 0.07 },
  bannerBlobInvalid: { backgroundColor: C.warn },
  bannerTitle: { fontSize: 16, fontWeight: '800', color: C.text, marginBottom: 6 },
  bannerText:  { fontSize: 12, color: 'rgba(255,255,255,0.5)', lineHeight: 18, marginBottom: 12 },

  chipRow: { flexDirection: 'row', gap: 7, flexWrap: 'wrap' },

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
  treatLoadingRow: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingVertical: 4 },
  treatLoadingTxt: { flex: 1, fontSize: 12, color: 'rgba(255,255,255,0.6)', lineHeight: 17 },
  treatErrorTxt: { fontSize: 12, color: C.muted, lineHeight: 18 },
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
