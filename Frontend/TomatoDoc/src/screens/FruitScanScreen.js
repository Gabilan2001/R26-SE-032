import React, { useContext, useEffect, useRef, useState } from 'react';
import {
  Alert,
  Animated,
  Easing,
  Image,
  Platform,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { predictFruitDisease } from '../api/fruitScanApi';
import { UIThemeContext } from '../context/UIThemeContext';
import LoadingOverlay from '../components/LoadingOverlay';

// ── Tokens ────────────────────────────────────────────────────────────────────
const C = {
  bg:            '#0f0f0f',
  surface:       '#1a1a1a',
  surface2:      '#222222',
  accent:        '#c8f135',
  accentDim:     'rgba(200,241,53,0.10)',
  accentBorder:  'rgba(200,241,53,0.22)',
  text:          '#f0f0f0',
  muted:         '#555555',
  border:        'rgba(255,255,255,0.07)',
  // Tomato-red accent (distinct from nutrient leaf-green)
  tomato:        '#ff5c5c',
  tomatoDim:     'rgba(255,92,92,0.08)',
  tomatoBorder:  'rgba(255,92,92,0.20)',
  success:       '#4adf6f',
  successDim:    'rgba(74,223,111,0.08)',
};

// ── Sample thumbnails ─────────────────────────────────────────────────────────
const SAMPLES = [
  { key: 'a', src: require('../../assets/images/tomato5.jpeg') },
  { key: 'b', src: require('../../assets/images/tomato8.jpeg') },
  { key: 'c', src: require('../../assets/images/tomato10.jpeg') },
];

// ── Filter tags ───────────────────────────────────────────────────────────────
const TAGS = [
  { id: 'all',     label: 'All Types', emoji: null },
  { id: 'disease', label: 'Disease',   emoji: '🦠'  },
  { id: 'healthy', label: 'Healthy',   emoji: '✅'  },
  { id: 'blight',  label: 'Blight',    emoji: '🍂'  },
];

// ── Animated corner brackets (tomato-red) ─────────────────────────────────────
function ViewfinderFrame() {
  const size = 22, t = 14;
  const corner = (pos) => ({
    position: 'absolute', width: size, height: size,
    borderColor: C.tomato, borderStyle: 'solid',
    ...(pos.top    !== undefined && { top:    pos.top    }),
    ...(pos.bottom !== undefined && { bottom: pos.bottom }),
    ...(pos.left   !== undefined && { left:   pos.left   }),
    ...(pos.right  !== undefined && { right:  pos.right  }),
    borderTopWidth:          (pos.top    !== undefined) ? 2.5 : 0,
    borderBottomWidth:       (pos.bottom !== undefined) ? 2.5 : 0,
    borderLeftWidth:         (pos.left   !== undefined) ? 2.5 : 0,
    borderRightWidth:        (pos.right  !== undefined) ? 2.5 : 0,
    borderTopLeftRadius:     (pos.top    !== undefined && pos.left  !== undefined) ? 5 : 0,
    borderTopRightRadius:    (pos.top    !== undefined && pos.right !== undefined) ? 5 : 0,
    borderBottomLeftRadius:  (pos.bottom !== undefined && pos.left  !== undefined) ? 5 : 0,
    borderBottomRightRadius: (pos.bottom !== undefined && pos.right !== undefined) ? 5 : 0,
  });
  return (
    <>
      <View style={corner({ top: t, left: t })} />
      <View style={corner({ top: t, right: t })} />
      <View style={corner({ bottom: t, left: t })} />
      <View style={corner({ bottom: t, right: t })} />
    </>
  );
}

// ── Animated scan line (tomato-red) ───────────────────────────────────────────
function ScanLine() {
  const anim = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(anim, { toValue: 1, duration: 2400, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(anim, { toValue: 0, duration: 2400, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ])
    ).start();
  }, []);
  const translateY = anim.interpolate({ inputRange: [0, 1], outputRange: [0, 146] });
  return (
    <Animated.View
      pointerEvents="none"
      style={[styles.scanLine, { transform: [{ translateY }] }]}
    />
  );
}

// ── Feature chip ──────────────────────────────────────────────────────────────
function Chip({ emoji, label }) {
  return (
    <View style={styles.chip}>
      <Text style={styles.chipEmoji}>{emoji}</Text>
      <Text style={styles.chipTxt}>{label}</Text>
    </View>
  );
}

// ── Filter tag ────────────────────────────────────────────────────────────────
function FilterTag({ tag, active, onPress }) {
  const scale = useRef(new Animated.Value(1)).current;
  const press = () => {
    Animated.sequence([
      Animated.timing(scale, { toValue: 0.93, duration: 80, useNativeDriver: true }),
      Animated.spring(scale, { toValue: 1,    useNativeDriver: true }),
    ]).start();
    onPress(tag.id);
  };
  return (
    <Animated.View style={{ transform: [{ scale }] }}>
      <TouchableOpacity
        style={[styles.filterTag, active && styles.filterTagActive]}
        onPress={press}
        activeOpacity={0.85}
      >
        {tag.emoji && <Text style={styles.filterTagEmoji}>{tag.emoji}</Text>}
        <Text style={[styles.filterTagTxt, active && styles.filterTagTxtActive]}>
          {tag.label}
        </Text>
      </TouchableOpacity>
    </Animated.View>
  );
}

// ── Sample card ───────────────────────────────────────────────────────────────
function SampleCard({ src, active, onPress }) {
  return (
    <TouchableOpacity
      style={[styles.sampleCard, active && styles.sampleCardActive]}
      onPress={onPress}
      activeOpacity={0.8}
    >
      <Image source={src} style={styles.sampleImg} />
      {active && (
        <View style={styles.sampleCheck}>
          <Text style={styles.sampleCheckTxt}>✓</Text>
        </View>
      )}
    </TouchableOpacity>
  );
}

// ── Main Screen ───────────────────────────────────────────────────────────────
export default function FruitScanScreen({ navigation }) {
  const { presentationMode } = useContext(UIThemeContext);
  const [image,        setImage]        = useState(null);
  const [loading,      setLoading]      = useState(false);
  const [activeSample, setActiveSample] = useState(0);
  const [activeTag,    setActiveTag]    = useState('all');

  // Hero entrance
  const heroOp = useRef(new Animated.Value(0)).current;
  const heroY  = useRef(new Animated.Value(24)).current;
  useEffect(() => {
    Animated.parallel([
      Animated.timing(heroOp, { toValue: 1, duration: 420, useNativeDriver: true }),
      Animated.spring(heroY,  { toValue: 0, useNativeDriver: true }),
    ]).start();
  }, []);

  // Button scale
  const btnScale = useRef(new Animated.Value(1)).current;
  const onPressIn  = () => Animated.spring(btnScale, { toValue: 0.96, useNativeDriver: true }).start();
  const onPressOut = () => Animated.spring(btnScale, { toValue: 1,    useNativeDriver: true }).start();

  const pickImage = async (fromCamera = false) => {
    const launcher = fromCamera
      ? ImagePicker.launchCameraAsync
      : ImagePicker.launchImageLibraryAsync;
    const res = await launcher({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.8,
    });
    if (!res.canceled) setImage(res.assets[0]);
  };

  const analyze = async () => {
    if (!image) return;
    setLoading(true);
    try {
      const formData = new FormData();
      if (Platform.OS === 'web') {
        const response = await fetch(image.uri);
        const blob     = await response.blob();
        const file     = new File([blob], 'tomato-fruit.jpg', { type: blob.type || 'image/jpeg' });
        formData.append('image', file);
      } else {
        formData.append('image', {
          uri:  image.uri,
          name: image.fileName || `tomato-fruit-${Date.now()}.jpg`,
          type: image.mimeType || 'image/jpeg',
        });
      }
      const res = await predictFruitDisease(formData);
      navigation.navigate('FruitResult', { result: res.data, imageUri: image.uri });
    } catch (error) {
      Alert.alert(
        'Analysis Failed',
        error?.response?.data?.error || error?.message || 'Could not analyze this image.'
      );
    } finally {
      setLoading(false);
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
          <Text style={styles.screenTitle}>Fruit Scanner</Text>
        </View>

        {/* ── Hero card (tomato-red tint) ── */}
        <Animated.View style={[styles.heroCard, { opacity: heroOp, transform: [{ translateY: heroY }] }]}>
          <View style={styles.heroCornerIcon}>
            <Text style={{ fontSize: 20 }}>🍅</Text>
          </View>

          <View style={styles.heroBadge}>
            <View style={styles.badgeDot} />
            <Text style={styles.badgeTxt}>Disease Classifier</Text>
          </View>

          <Text style={[styles.heroTitle, presentationMode && { fontSize: 24 }]}>
            {'Tomato Fruit\n'}<Text style={styles.heroTitleAccent}>Disease Scan</Text>
          </Text>
          <Text style={styles.heroHelper}>
            Take a clear photo of the affected fruit area for instant AI diagnosis.
          </Text>

          <View style={styles.chipRow}>
            <Chip emoji="🔬" label="Disease Classifier" />
            <Chip emoji="💊" label="Treatment Guide"    />
            <Chip emoji="📊" label="Stats Ready"        />
          </View>
        </Animated.View>

        {/* ── Viewfinder ── */}
        <View style={styles.viewfinder}>
          <ViewfinderFrame />
          <ScanLine />

          {image ? (
            <Image source={{ uri: image.uri }} style={styles.vfImage} />
          ) : (
            <View style={styles.vfPlaceholder}>
              <Text style={{ fontSize: 48, opacity: 0.35 }}>🍅</Text>
              <Text style={styles.vfPlaceholderTxt}>Place tomato fruit{'\n'}inside the frame</Text>
            </View>
          )}

          {loading && (
            <View style={styles.vfLoadingOverlay}>
              <LoadingOverlay text="Analyzing tomato fruit…" />
            </View>
          )}
        </View>

        {/* ── Filter tags ── */}
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={styles.tagStrip}
          contentContainerStyle={{ gap: 7, paddingRight: 4 }}
        >
          {TAGS.map(tag => (
            <FilterTag
              key={tag.id}
              tag={tag}
              active={activeTag === tag.id}
              onPress={setActiveTag}
            />
          ))}
        </ScrollView>

        {/* ── Reference samples ── */}
        <Text style={styles.sectionLabel}>Reference Tomato Samples</Text>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={styles.sampleStrip}
          contentContainerStyle={{ paddingRight: 4 }}
        >
          {SAMPLES.map((s, i) => (
            <SampleCard
              key={s.key}
              src={s.src}
              active={activeSample === i}
              onPress={() => setActiveSample(i)}
            />
          ))}
        </ScrollView>

        {/* ── Action buttons ── */}
        <View style={styles.actionRow}>
          <TouchableOpacity
            style={[styles.actionBtn, styles.actionBtnGallery]}
            onPress={() => pickImage(false)}
            activeOpacity={0.85}
          >
            <Text style={styles.actionBtnIcon}>🖼</Text>
            <Text style={styles.actionBtnTxtLight}>Gallery</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.actionBtn, styles.actionBtnCamera]}
            onPress={() => pickImage(true)}
            activeOpacity={0.85}
          >
            <Text style={styles.actionBtnIcon}>📷</Text>
            <Text style={styles.actionBtnTxt}>Camera</Text>
          </TouchableOpacity>
        </View>

        {/* ── Analyze CTA ── */}
        <Animated.View style={{ transform: [{ scale: btnScale }] }}>
          <Pressable
            style={[styles.analyzeBtn, !image && styles.analyzeBtnDisabled]}
            onPressIn={onPressIn}
            onPressOut={onPressOut}
            onPress={analyze}
            disabled={!image || loading}
          >
            <Text style={styles.analyzeBtnIcon}>🔬</Text>
            <Text style={styles.analyzeBtnTxt}>Analyze Fruit</Text>
          </Pressable>
        </Animated.View>

        <Text style={styles.analyzeHint}>
          {image ? 'Image ready · tap to analyze' : 'Select or capture an image to begin'}
        </Text>
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
  backRow:     { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 14, paddingTop: 4 },
  backBtn:     { width: 32, height: 32, backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: 16, alignItems: 'center', justifyContent: 'center' },
  backArrow:   { fontSize: 16, color: C.text },
  screenTitle: { fontSize: 18, fontWeight: '800', color: C.text },

  // Hero — tomato dark red base
  heroCard: {
    backgroundColor: '#1a0500',
    borderWidth: 1, borderColor: C.tomatoBorder,
    borderRadius: 22, padding: 18, marginBottom: 14, overflow: 'hidden',
  },
  heroCornerIcon: {
    position: 'absolute', top: 14, right: 14,
    width: 44, height: 44, borderRadius: 12,
    backgroundColor: C.tomatoDim, borderWidth: 1, borderColor: C.tomatoBorder,
    alignItems: 'center', justifyContent: 'center',
  },
  heroBadge:  { flexDirection: 'row', alignItems: 'center', gap: 5, alignSelf: 'flex-start',
                backgroundColor: 'rgba(255,92,92,0.12)', borderWidth: 1, borderColor: 'rgba(255,92,92,0.25)',
                borderRadius: 100, paddingHorizontal: 10, paddingVertical: 3, marginBottom: 12 },
  badgeDot:   { width: 5, height: 5, borderRadius: 3, backgroundColor: C.tomato },
  badgeTxt:   { fontSize: 10, color: C.tomato, fontWeight: '700', letterSpacing: 0.4 },
  heroTitle:  { fontSize: 22, fontWeight: '800', color: '#fff', lineHeight: 28, marginBottom: 8 },
  heroTitleAccent: { color: C.tomato },
  heroHelper: { fontSize: 12, color: 'rgba(255,255,255,0.45)', lineHeight: 18, marginBottom: 14 },

  // Chips
  chipRow:   { flexDirection: 'row', gap: 7, flexWrap: 'wrap' },
  chip:      { flexDirection: 'row', alignItems: 'center', gap: 5,
               backgroundColor: 'rgba(255,255,255,0.06)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.10)',
               borderRadius: 100, paddingHorizontal: 11, paddingVertical: 5 },
  chipEmoji: { fontSize: 11 },
  chipTxt:   { fontSize: 11, color: 'rgba(255,255,255,0.65)', fontWeight: '500' },

  // Viewfinder — tomato-red tint
  viewfinder: {
    width: '100%', height: 200,
    backgroundColor: '#1a0500',
    borderRadius: 18, borderWidth: 1.5, borderColor: C.tomatoBorder,
    overflow: 'hidden', marginBottom: 14,
    alignItems: 'center', justifyContent: 'center',
  },
  scanLine:        { position: 'absolute', left: 14, right: 14, height: 1.5, backgroundColor: C.tomato, opacity: 0.70 },
  vfImage:         { position: 'absolute', width: '100%', height: '100%', resizeMode: 'cover' },
  vfPlaceholder:   { alignItems: 'center', gap: 8 },
  vfPlaceholderTxt:{ fontSize: 11, color: C.muted, textAlign: 'center', lineHeight: 16 },
  vfLoadingOverlay:{ position: 'absolute', inset: 0, backgroundColor: 'rgba(26,5,0,0.88)', alignItems: 'center', justifyContent: 'center' },

  // Filter tags
  tagStrip: { marginBottom: 14 },
  filterTag:       { flexDirection: 'row', alignItems: 'center', gap: 5,
                     paddingHorizontal: 12, paddingVertical: 7,
                     borderRadius: 100, borderWidth: 1, borderColor: C.border,
                     backgroundColor: C.surface },
  filterTagActive: { backgroundColor: 'rgba(255,92,92,0.08)', borderColor: 'rgba(255,92,92,0.28)' },
  filterTagEmoji:  { fontSize: 11 },
  filterTagTxt:    { fontSize: 11, color: C.muted, fontWeight: '600' },
  filterTagTxtActive: { color: C.tomato },

  // Section
  sectionLabel: { fontSize: 10, fontWeight: '700', color: C.muted, textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 10, marginLeft: 2 },

  // Samples
  sampleStrip:      { marginBottom: 16 },
  sampleCard:       { width: 100, height: 72, borderRadius: 12, overflow: 'hidden',
                      backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, marginRight: 9 },
  sampleCardActive: { borderColor: C.tomato, borderWidth: 1.5 },
  sampleImg:        { width: '100%', height: '100%', resizeMode: 'cover' },
  sampleCheck:      { position: 'absolute', top: 5, right: 6, backgroundColor: C.tomato,
                      borderRadius: 10, width: 16, height: 16, alignItems: 'center', justifyContent: 'center' },
  sampleCheckTxt:   { fontSize: 9, color: '#fff', fontWeight: '800' },

  // Action buttons
  actionRow:       { flexDirection: 'row', gap: 10, marginBottom: 12 },
  actionBtn:       { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7, borderRadius: 14, paddingVertical: 14 },
  actionBtnGallery:{ backgroundColor: C.tomato },
  actionBtnCamera: { backgroundColor: C.surface, borderWidth: 1.5, borderColor: C.border },
  actionBtnIcon:   { fontSize: 16 },
  actionBtnTxtLight:{ fontSize: 13, fontWeight: '700', color: '#fff' },
  actionBtnTxt:    { fontSize: 13, fontWeight: '600', color: C.text },

  // Analyze CTA
  analyzeBtn:         { backgroundColor: C.accent, borderRadius: 16, paddingVertical: 16,
                        flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8 },
  analyzeBtnDisabled: { opacity: 0.3 },
  analyzeBtnIcon:     { fontSize: 16 },
  analyzeBtnTxt:      { fontSize: 15, fontWeight: '800', color: '#0f0f0f', letterSpacing: 0.3 },
  analyzeHint:        { fontSize: 11, color: C.muted, textAlign: 'center', marginTop: 10 },
});