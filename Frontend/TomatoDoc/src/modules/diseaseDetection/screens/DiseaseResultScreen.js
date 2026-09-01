import React, { useContext, useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Animated,
  Image,
  Modal,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { UIThemeContext } from '../../../context/UIThemeContext';
import DiseaseChip from '../components/DiseaseChip';
import { CLASS_COLORS } from '../constants/classColors';
import { getTreatment } from '../api/scan';

// ── Tokens -- agricultural theme, matches DiseaseScanScreen ──────────────────
const C = {
  bg:           '#F8F7F2',
  card:         '#FFFFFF',
  cardBorder:   'rgba(36,53,42,0.08)',
  tomato:       '#E34A3B',
  tomatoDark:   '#C9362C',
  tomatoDim:    'rgba(227,74,59,0.08)',
  tomatoBorder: 'rgba(227,74,59,0.28)',
  leaf:         '#3F7D45',
  leafDim:      'rgba(63,125,69,0.08)',
  leafBorder:   'rgba(63,125,69,0.30)',
  softGreen:    '#E8F3E7',
  text:         '#24352A',
  muted:        '#68756B',
  border:       'rgba(36,53,42,0.10)',
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
  const insets = useSafeAreaInsets();
  const { result, imageUri } = route.params;

  const diseasesFound = result.diseases_found || [];
  const onlyHealthy = diseasesFound.length === 1 && diseasesFound[0] === 'Healthy';
  const hasProblem = diseasesFound.some((d) => d !== 'Healthy');
  // Covers blank-image / not-a-leaf / no-detection -- backend sets
  // valid: false and a human-readable `error` string for all of these.
  const isInvalid = result.valid === false;

  // Full-screen tap-to-inspect viewer for the annotated detection image.
  // Note: this is a plain full-screen view (centered image, dark backdrop,
  // close button) -- NOT true pinch-to-zoom/pan. This project has no
  // gesture/zoom library installed, and adding one plus wiring real pinch
  // gestures is a real feature build, not a same-night theme change --
  // worth doing properly later rather than rushed in.
  const [viewerOpen, setViewerOpen] = useState(false);

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
      <StatusBar barStyle="dark-content" backgroundColor={C.bg} />
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={[styles.content, { paddingTop: insets.top + 12, paddingBottom: insets.bottom + 40 }]}
        showsVerticalScrollIndicator={false}
      >
        {/* ── Back row ── */}
        <View style={styles.backRow}>
          <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()}>
            <Text style={styles.backArrow}>←</Text>
          </TouchableOpacity>
          <Text style={styles.screenTitle}>Disease Result</Text>
        </View>

        {/* ── Banner ── */}
        <Animated.View
          style={[
            styles.banner,
            onlyHealthy && styles.bannerHealthy,
            (hasProblem || isInvalid) && styles.bannerAttention,
            { opacity: bannerOp, transform: [{ translateY: bannerY }] },
          ]}
        >
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
          <Text style={styles.resultCardTitle}>🔍 Detection Result</Text>
          <Text style={styles.resultCardSub}>Your leaf has been analyzed</Text>
          <TouchableOpacity
            style={styles.resultImageWrap}
            activeOpacity={result.annotated_image ? 0.9 : 1}
            onPress={() => result.annotated_image && setViewerOpen(true)}
          >
            {displayImage ? (
              <Image source={{ uri: displayImage }} style={styles.resultImage} />
            ) : (
              <View style={[styles.resultImage, styles.resultImagePlaceholder]}>
                <Text style={{ fontSize: 60, opacity: 0.3 }}>🍃</Text>
              </View>
            )}
            {result.annotated_image && (
              <View style={styles.tapHint}>
                <Text style={styles.tapHintTxt}>🔎 Tap to inspect</Text>
              </View>
            )}
          </TouchableOpacity>
          {result.annotated_image && (
            <View style={styles.legendRow}>
              {Object.entries(CLASS_COLORS).map(([name, color]) => (
                <View key={name} style={styles.legendItem}>
                  <View style={[styles.legendDot, { backgroundColor: color }]} />
                  <Text style={styles.legendLabel}>{name.replace('_', ' ')}</Text>
                </View>
              ))}
            </View>
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
                <ActivityIndicator color={C.leaf} />
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
            style={({ pressed }) => [styles.btnSecondary, pressed && styles.btnSecondaryPressed]}
            onPressIn={onPressIn}
            onPressOut={onPressOut}
            // DiseaseResultScreen lives on the outer stack, but DiseaseScan
            // is a tab nested inside the DiseaseModule tab navigator -- a
            // bare navigate('DiseaseScan') doesn't resolve from out here
            // (that route name only exists inside DiseaseModule's own
            // navigator), so the button silently did nothing.
            onPress={() => navigation.navigate('DiseaseModule', { screen: 'DiseaseScan' })}
          >
            <Text style={styles.btnSecondaryIcon}>↩</Text>
            <Text style={styles.btnSecondaryTxt}>Scan Another Leaf</Text>
          </Pressable>
        </Animated.View>
      </ScrollView>

      {/* ── Full-screen image viewer ── */}
      <Modal visible={viewerOpen} transparent animationType="fade" onRequestClose={() => setViewerOpen(false)}>
        <View style={styles.viewerBackdrop}>
          <TouchableOpacity
            style={[styles.viewerClose, { top: insets.top + 14 }]}
            onPress={() => setViewerOpen(false)}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          >
            <Text style={styles.viewerCloseTxt}>✕</Text>
          </TouchableOpacity>
          {displayImage && (
            <Image source={{ uri: displayImage }} style={styles.viewerImage} resizeMode="contain" />
          )}
        </View>
      </Modal>
    </View>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  root:    { flex: 1, backgroundColor: C.bg },
  scroll:  { flex: 1 },
  content: { padding: 18, paddingBottom: 40 },

  backRow:   { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 14, paddingTop: 4 },
  backBtn:   { width: 32, height: 32, backgroundColor: C.card, borderWidth: 1, borderColor: C.border, borderRadius: 16,
               alignItems: 'center', justifyContent: 'center',
               shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 3, shadowOffset: { width: 0, height: 1 }, elevation: 1 },
  backArrow: { fontSize: 15, color: C.text },
  screenTitle: { fontSize: 18, fontWeight: '800', color: C.text },

  banner: {
    backgroundColor: C.card,
    borderWidth: 1, borderColor: C.cardBorder,
    borderRadius: 20, padding: 16, marginBottom: 14,
    shadowColor: '#24352A', shadowOpacity: 0.05, shadowRadius: 8, shadowOffset: { width: 0, height: 3 }, elevation: 2,
  },
  bannerHealthy:   { backgroundColor: C.softGreen, borderColor: C.leafBorder },
  bannerAttention: { backgroundColor: C.tomatoDim, borderColor: C.tomatoBorder },
  bannerTitle: { fontSize: 16, fontWeight: '800', color: C.text, marginBottom: 6 },
  bannerText:  { fontSize: 12, color: C.muted, lineHeight: 18, marginBottom: 12 },

  chipRow: { flexDirection: 'row', gap: 7, flexWrap: 'wrap' },

  resultCard: { backgroundColor: C.card, borderWidth: 1, borderColor: C.cardBorder, borderRadius: 20,
                overflow: 'hidden', marginBottom: 6, padding: 16,
                shadowColor: '#24352A', shadowOpacity: 0.06, shadowRadius: 10, shadowOffset: { width: 0, height: 4 }, elevation: 2 },
  resultCardTitle: { fontSize: 15, fontWeight: '800', color: C.text, marginBottom: 2 },
  resultCardSub:   { fontSize: 11.5, color: C.muted, marginBottom: 12 },
  resultImageWrap: { width: '100%', height: 260, backgroundColor: C.softGreen, borderRadius: 14, overflow: 'hidden',
                      justifyContent: 'center', alignItems: 'center' },
  resultImage: { width: '100%', height: '100%', resizeMode: 'contain' },
  resultImagePlaceholder: { justifyContent: 'center', alignItems: 'center' },
  tapHint:     { position: 'absolute', bottom: 10, right: 10, backgroundColor: 'rgba(36,53,42,0.75)',
                 borderRadius: 100, paddingHorizontal: 10, paddingVertical: 5 },
  tapHintTxt:  { fontSize: 10.5, fontWeight: '700', color: '#fff' },
  legendRow:   { flexDirection: 'row', flexWrap: 'wrap', gap: 12, justifyContent: 'center',
                 paddingHorizontal: 4, paddingTop: 12 },
  legendItem:  { flexDirection: 'row', alignItems: 'center', gap: 6 },
  legendDot:   { width: 9, height: 9, borderRadius: 5 },
  legendLabel: { fontSize: 11, color: C.muted, fontWeight: '600' },

  warningBox:  { flexDirection: 'row', gap: 9, alignItems: 'flex-start',
                 backgroundColor: C.tomatoDim, borderWidth: 1, borderColor: C.tomatoBorder,
                 borderRadius: 12, padding: 12, marginTop: 14, marginBottom: 4 },
  warningIcon: { fontSize: 13, color: C.tomatoDark, marginTop: 1 },
  warningTxt:  { flex: 1, fontSize: 11, color: C.tomatoDark, lineHeight: 17 },

  treatCard: { backgroundColor: C.card, borderWidth: 1, borderColor: C.cardBorder, borderRadius: 20, padding: 16,
               marginTop: 14, marginBottom: 16,
               shadowColor: '#24352A', shadowOpacity: 0.05, shadowRadius: 8, shadowOffset: { width: 0, height: 3 }, elevation: 2 },
  treatCardTitle: { fontSize: 15, fontWeight: '800', color: C.text, marginBottom: 12 },
  treatLoadingRow: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingVertical: 4 },
  treatLoadingTxt: { flex: 1, fontSize: 12, color: C.muted, lineHeight: 17 },
  treatErrorTxt: { fontSize: 12, color: C.muted, lineHeight: 18 },
  treatH3:   { fontSize: 13, fontWeight: '800', color: C.leaf, marginTop: 10, marginBottom: 6 },
  treatBody: { flex: 1, fontSize: 12.5, color: C.text, lineHeight: 20 },
  treatBold: { fontWeight: '800', color: C.text },
  treatBulletRow: { flexDirection: 'row', gap: 7, marginBottom: 7, alignItems: 'flex-start' },
  treatBulletDot: { fontSize: 12.5, color: C.leaf, fontWeight: '800', minWidth: 14 },

  sourcesBox: { marginTop: 14, paddingTop: 12, borderTopWidth: 1, borderTopColor: C.border },
  sourcesTitle: { fontSize: 10, fontWeight: '700', color: C.muted, textTransform: 'uppercase', letterSpacing: 0.7, marginBottom: 6 },
  sourceLine: { fontSize: 10.5, color: C.muted, lineHeight: 16, marginBottom: 3 },

  // Secondary action -- same visual language as the primary Analyze button
  // on the scan screen, but clearly distinct: leaf-green border on white
  // rather than a solid tomato-red fill.
  btnSecondary:        { backgroundColor: C.card, borderRadius: 14, paddingVertical: 15,
                          borderWidth: 1.5, borderColor: C.leafBorder,
                          flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7 },
  btnSecondaryPressed: { backgroundColor: C.leafDim },
  btnSecondaryIcon:    { fontSize: 15, color: C.leaf },
  btnSecondaryTxt:     { fontSize: 14, fontWeight: '800', color: C.leaf, letterSpacing: 0.3 },

  // Full-screen viewer -- plain tap-to-inspect (no pinch/pan yet, see note
  // in the component above).
  viewerBackdrop: { flex: 1, backgroundColor: 'rgba(10,14,10,0.96)', alignItems: 'center', justifyContent: 'center' },
  viewerImage:    { width: '100%', height: '80%' },
  viewerClose:    { position: 'absolute', right: 16, width: 38, height: 38, borderRadius: 19,
                    backgroundColor: 'rgba(255,255,255,0.12)', alignItems: 'center', justifyContent: 'center', zIndex: 1 },
  viewerCloseTxt: { fontSize: 18, color: '#fff', fontWeight: '700' },
});
