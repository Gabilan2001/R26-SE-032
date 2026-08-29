import React, { useContext, useRef, useState, useEffect } from 'react';
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
import { predictNutrient } from '../api/scanApi';
import { AuthContext } from '../context/AuthContext';
import { UIThemeContext } from '../context/UIThemeContext';
import LoadingOverlay from '../components/LoadingOverlay';

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
};

// ── Sample thumbnails ─────────────────────────────────────────────────────────
const SAMPLES = [
  { key: 'a', src: require('../../assets/images/tomato7.jpeg') },
  { key: 'b', src: require('../../assets/images/tomato9.jpeg') },
  { key: 'c', src: require('../../assets/images/tomato10.jpeg') },
];

// ── Animated corner brackets for the viewfinder ───────────────────────────────
function ViewfinderFrame() {
  const size = 22;
  const t = 14;
  const cornerStyle = (pos) => ({
    position: 'absolute',
    width: size,
    height: size,
    borderColor: C.accent,
    borderStyle: 'solid',
    ...(pos.top    !== undefined && { top:    pos.top }),
    ...(pos.bottom !== undefined && { bottom: pos.bottom }),
    ...(pos.left   !== undefined && { left:   pos.left }),
    ...(pos.right  !== undefined && { right:  pos.right }),
    borderTopWidth:    pos.top    !== undefined ? 2.5 : 0,
    borderBottomWidth: pos.bottom !== undefined ? 2.5 : 0,
    borderLeftWidth:   pos.left   !== undefined ? 2.5 : 0,
    borderRightWidth:  pos.right  !== undefined ? 2.5 : 0,
    borderTopLeftRadius:     (pos.top    !== undefined && pos.left  !== undefined) ? 5 : 0,
    borderTopRightRadius:    (pos.top    !== undefined && pos.right !== undefined) ? 5 : 0,
    borderBottomLeftRadius:  (pos.bottom !== undefined && pos.left  !== undefined) ? 5 : 0,
    borderBottomRightRadius: (pos.bottom !== undefined && pos.right !== undefined) ? 5 : 0,
  });
  return (
    <>
      <View style={cornerStyle({ top: t, left: t })} />
      <View style={cornerStyle({ top: t, right: t })} />
      <View style={cornerStyle({ bottom: t, left: t })} />
      <View style={cornerStyle({ bottom: t, right: t })} />
    </>
  );
}

// ── Animated scan line ────────────────────────────────────────────────────────
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
  const translateY = anim.interpolate({ inputRange: [0, 1], outputRange: [0, 140] });
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
export default function ScanScreen({ navigation }) {
  const { token }              = useContext(AuthContext);
  const { presentationMode }   = useContext(UIThemeContext);
  const [image, setImage]      = useState(null);
  const [loading, setLoading]  = useState(false);
  const [activeSample, setActiveSample] = useState(0);

  // Hero entrance
  const heroOp = useRef(new Animated.Value(0)).current;
  const heroY  = useRef(new Animated.Value(24)).current;
  useEffect(() => {
    Animated.parallel([
      Animated.timing(heroOp, { toValue: 1, duration: 400, useNativeDriver: true }),
      Animated.spring(heroY,  { toValue: 0, useNativeDriver: true }),
    ]).start();
  }, []);

  // Analyze button scale
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
        const file     = new File([blob], 'leaf.jpg', { type: blob.type || 'image/jpeg' });
        formData.append('image', file);
      } else {
        formData.append('image', {
          uri:  image.uri,
          name: image.fileName || `leaf-${Date.now()}.jpg`,
          type: image.mimeType || 'image/jpeg',
        });
      }
      const res = await predictNutrient(formData, token);
      navigation.navigate('Result', { result: res.data, imageUri: image.uri });
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
          <Text style={styles.screenTitle}>Leaf Scanner</Text>
        </View>

        {/* ── Hero card ── */}
        <Animated.View style={[styles.heroCard, { opacity: heroOp, transform: [{ translateY: heroY }] }]}>
          {/* Corner accent icon */}
          <View style={styles.heroCornerIcon}>
            <Text style={{ fontSize: 20 }}>🍃</Text>
          </View>

          <View style={styles.heroBadge}>
            <View style={styles.badgeDot} />
            <Text style={styles.badgeTxt}>AI Powered</Text>
          </View>

          <Text style={[styles.heroTitle, presentationMode && { fontSize: 26 }]}>
            {'Nutrient Deficiency\nScan'}
          </Text>
          <Text style={styles.heroHelper}>
            Take a clear photo of a single tomato leaf for instant diagnosis.
          </Text>

          <View style={styles.chipRow}>
            <Chip emoji="🧠" label="AI Insight" />
            <Chip emoji="🧪" label="Fertilizer Plan" />
            <Chip emoji="📋" label="History" />
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
              <Text style={{ fontSize: 48, opacity: 0.3 }}>🍃</Text>
              <Text style={styles.vfPlaceholderTxt}>Place leaf inside the frame</Text>
            </View>
          )}

          {/* Loading overlay inside viewfinder */}
          {loading && (
            <View style={styles.vfLoadingOverlay}>
              <LoadingOverlay text="Analyzing leaf…" />
            </View>
          )}
        </View>

        {/* ── Reference samples ── */}
        <Text style={styles.sectionLabel}>Reference Quality Samples</Text>
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

        {/* ── Image source buttons ── */}
        <View style={styles.actionRow}>
          <TouchableOpacity
            style={[styles.actionBtn, styles.actionBtnGallery]}
            onPress={() => pickImage(false)}
            activeOpacity={0.85}
          >
            <Text style={styles.actionBtnIcon}>🖼</Text>
            <Text style={styles.actionBtnTxtDark}>Gallery</Text>
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
            <Text style={styles.analyzeBtnTxt}>Analyze Leaf</Text>
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

  // Back row
  backRow:  { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 14, paddingTop: 4 },
  backBtn:  { width: 32, height: 32, backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: 16, alignItems: 'center', justifyContent: 'center' },
  backArrow:{ fontSize: 16, color: C.text },
  screenTitle: { fontSize: 18, fontWeight: '800', color: C.text },

  // Hero
  heroCard: {
    backgroundColor: '#0f1a00',
    borderRadius: 22,
    borderWidth: 1,
    borderColor: C.accentBorder,
    padding: 18,
    marginBottom: 14,
    overflow: 'hidden',
  },
  heroCornerIcon: {
    position: 'absolute', top: 14, right: 14,
    width: 44, height: 44, borderRadius: 12,
    backgroundColor: C.accentDim,
    borderWidth: 1, borderColor: C.accentBorder,
    alignItems: 'center', justifyContent: 'center',
  },
  heroBadge:  { flexDirection: 'row', alignItems: 'center', gap: 5, alignSelf: 'flex-start',
                backgroundColor: 'rgba(200,241,53,0.12)', borderWidth: 1, borderColor: C.accentBorder,
                borderRadius: 100, paddingHorizontal: 10, paddingVertical: 3, marginBottom: 12 },
  badgeDot:   { width: 5, height: 5, borderRadius: 3, backgroundColor: C.accent },
  badgeTxt:   { fontSize: 10, color: C.accent, fontWeight: '700', letterSpacing: 0.4 },
  heroTitle:  { fontSize: 22, fontWeight: '800', color: '#fff', lineHeight: 28, marginBottom: 8 },
  heroHelper: { fontSize: 12, color: 'rgba(255,255,255,0.5)', lineHeight: 18, marginBottom: 14 },

  // Chips
  chipRow: { flexDirection: 'row', gap: 7, flexWrap: 'wrap' },
  chip:    { flexDirection: 'row', alignItems: 'center', gap: 5,
             backgroundColor: 'rgba(255,255,255,0.07)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.10)',
             borderRadius: 100, paddingHorizontal: 11, paddingVertical: 5 },
  chipEmoji:{ fontSize: 11 },
  chipTxt:  { fontSize: 11, color: 'rgba(255,255,255,0.7)', fontWeight: '500' },

  // Viewfinder
  viewfinder: {
    width: '100%', height: 200,
    backgroundColor: '#0a1400',
    borderRadius: 18,
    borderWidth: 1.5, borderColor: C.accentBorder,
    overflow: 'hidden',
    marginBottom: 14,
    alignItems: 'center', justifyContent: 'center',
  },
  scanLine:        { position: 'absolute', left: 14, right: 14, height: 1.5, backgroundColor: C.accent, opacity: 0.75 },
  vfImage:         { position: 'absolute', width: '100%', height: '100%', resizeMode: 'cover' },
  vfPlaceholder:   { alignItems: 'center', gap: 8 },
  vfPlaceholderTxt:{ fontSize: 11, color: C.muted, textAlign: 'center', lineHeight: 16 },
  vfLoadingOverlay:{ position: 'absolute', inset: 0, backgroundColor: 'rgba(10,20,0,0.85)',
                     alignItems: 'center', justifyContent: 'center' },

  // Section
  sectionLabel: { fontSize: 10, fontWeight: '700', color: C.muted, textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 10, marginLeft: 2 },

  // Sample strip
  sampleStrip:      { marginBottom: 16 },
  sampleCard:       { width: 100, height: 72, borderRadius: 12, overflow: 'hidden',
                      backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, marginRight: 9 },
  sampleCardActive: { borderColor: C.accent, borderWidth: 1.5 },
  sampleImg:        { width: '100%', height: '100%', resizeMode: 'cover' },
  sampleCheck:      { position: 'absolute', top: 5, right: 6, backgroundColor: C.accent,
                      borderRadius: 10, width: 16, height: 16, alignItems: 'center', justifyContent: 'center' },
  sampleCheckTxt:   { fontSize: 9, color: '#0f0f0f', fontWeight: '800' },

  // Action buttons
  actionRow:       { flexDirection: 'row', gap: 10, marginBottom: 12 },
  actionBtn:       { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7, borderRadius: 14, paddingVertical: 14 },
  actionBtnGallery:{ backgroundColor: C.accent },
  actionBtnCamera: { backgroundColor: C.surface, borderWidth: 1.5, borderColor: C.border },
  actionBtnIcon:   { fontSize: 16 },
  actionBtnTxtDark:{ fontSize: 13, fontWeight: '700', color: '#0f0f0f' },
  actionBtnTxt:    { fontSize: 13, fontWeight: '600', color: C.text },
  // Analyze
  analyzeBtn:         { backgroundColor: C.accent, borderRadius: 16, paddingVertical: 16,
                         flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8 },
  analyzeBtnDisabled: { opacity: 0.3 },
  analyzeBtnIcon:     { fontSize: 16 },
  analyzeBtnTxt:      { fontSize: 15, fontWeight: '800', color: '#0f0f0f', letterSpacing: 0.3 },
  analyzeHint:        { fontSize: 11, color: C.muted, textAlign: 'center', marginTop: 10 },
});
