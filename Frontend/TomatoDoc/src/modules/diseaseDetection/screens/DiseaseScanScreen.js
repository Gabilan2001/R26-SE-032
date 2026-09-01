import React, { useContext, useEffect, useRef, useState } from 'react';
import {
  Alert,
  Animated,
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
import * as ImageManipulator from 'expo-image-manipulator';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { predictDisease } from '../api/scan';
import { UIThemeContext } from '../../../context/UIThemeContext';
import LoadingOverlay from '../../../components/LoadingOverlay';

// ── Tokens -- agricultural theme: warm cream background, tomato red as the
// primary action color, leaf green as the supporting/secondary color. Same
// structure/screen flow as before; this is a visual-only relight. ───────────
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

// ── Main Screen ───────────────────────────────────────────────────────────────
export default function DiseaseScanScreen({ navigation }) {
  const { presentationMode } = useContext(UIThemeContext);
  const insets = useSafeAreaInsets();
  const [image, setImage] = useState(null);
  const [loading, setLoading] = useState(false);

  const heroOp = useRef(new Animated.Value(0)).current;
  const heroY  = useRef(new Animated.Value(24)).current;
  useEffect(() => {
    Animated.parallel([
      Animated.timing(heroOp, { toValue: 1, duration: 400, useNativeDriver: true }),
      Animated.spring(heroY,  { toValue: 0, useNativeDriver: true }),
    ]).start();
  }, []);

  const btnScale = useRef(new Animated.Value(1)).current;
  const onPressIn  = () => Animated.spring(btnScale, { toValue: 0.96, useNativeDriver: true }).start();
  const onPressOut = () => Animated.spring(btnScale, { toValue: 1,    useNativeDriver: true }).start();

  const pickImage = async (fromCamera = false) => {
    const launcher = fromCamera ? ImagePicker.launchCameraAsync : ImagePicker.launchImageLibraryAsync;
    const res = await launcher({ mediaTypes: ImagePicker.MediaTypeOptions.Images, quality: 0.8 });
    if (res.canceled) return;
    const picked = res.assets[0];
    // Phone camera photos are often 3000-4000px / several MB -- quality:0.8
    // above only re-encodes, it doesn't shrink dimensions. On a slow/cellular
    // upload link that's enough to blow past the API's timeout even though
    // the backend itself responds instantly. The model runs at native 640px
    // input, so downscaling to 1280px on the long edge loses nothing
    // detection-wise while cutting the upload size ~5-10x.
    try {
      const resized = await ImageManipulator.manipulateAsync(
        picked.uri,
        [{ resize: { width: 1280 } }],
        { compress: 0.8, format: ImageManipulator.SaveFormat.JPEG }
      );
      setImage({ uri: resized.uri, fileName: `leaf-${Date.now()}.jpg`, mimeType: 'image/jpeg' });
    } catch {
      // If resizing fails for any reason, fall back to the original picked image.
      setImage(picked);
    }
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
      const res = await predictDisease(formData);
      navigation.navigate('DiseaseResult', { result: res.data, imageUri: image.uri });
    } catch (error) {
      Alert.alert(
        'Analysis Failed',
        error?.response?.data?.error || error?.message || 'Could not analyze this image. Check that the backend is reachable.'
      );
    } finally {
      setLoading(false);
    }
  };

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
          <Text style={styles.screenTitle}>Disease Scanner</Text>
          <View style={{ flex: 1 }} />
          <TouchableOpacity
            style={styles.settingsBtn}
            onPress={() => navigation.navigate('DiseaseSettings')}
            hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
          >
            <Text style={styles.settingsIcon}>⚙</Text>
          </TouchableOpacity>
        </View>

        {/* ── Hero card ── */}
        <Animated.View style={[styles.heroCard, { opacity: heroOp, transform: [{ translateY: heroY }] }]}>
          <View style={styles.heroIconCircle}>
            <Text style={{ fontSize: 20 }}>🍅</Text>
          </View>
          <Text style={[styles.heroTitle, presentationMode && { fontSize: 26 }]}>
            {'Leaf Disease\n'}<Text style={styles.heroTitleAccent}>& Pest Scan</Text>
          </Text>
          <Text style={styles.heroHelper}>
            Take a clear photo of a tomato leaf to check for Early Blight, Late Blight, Leaf Miner,
            or a Healthy leaf — with treatment advice.
          </Text>
        </Animated.View>

        {/* ── Upload area ── */}
        <View style={[styles.uploadArea, image && styles.uploadAreaFilled]}>
          {image ? (
            <>
              <Image source={{ uri: image.uri }} style={styles.uploadedImage} />
              <View style={styles.imageBadge}>
                <Text style={styles.imageBadgeTxt}>✓ Leaf photo selected</Text>
              </View>
            </>
          ) : (
            <View style={styles.uploadPlaceholder}>
              <View style={styles.uploadIconCircle}>
                <Text style={{ fontSize: 26 }}>📷</Text>
              </View>
              <Text style={styles.uploadPlaceholderTitle}>Upload or capture a leaf image</Text>
              <Text style={styles.uploadPlaceholderSub}>A clear, well-lit photo of a single tomato leaf works best</Text>
            </View>
          )}
          {loading && (
            <View style={styles.uploadLoadingOverlay}>
              <LoadingOverlay text={'Analyzing leaf…'} />
            </View>
          )}
        </View>

        {/* ── Image source buttons ── */}
        <View style={styles.actionRow}>
          <TouchableOpacity style={styles.actionBtn} onPress={() => pickImage(false)} activeOpacity={0.8}>
            <Text style={styles.actionBtnIcon}>🖼</Text>
            <Text style={styles.actionBtnTxt}>Gallery</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionBtn} onPress={() => pickImage(true)} activeOpacity={0.8}>
            <Text style={styles.actionBtnIcon}>📷</Text>
            <Text style={styles.actionBtnTxt}>Camera</Text>
          </TouchableOpacity>
        </View>

        {/* ── Analyze CTA ── */}
        <Animated.View style={{ transform: [{ scale: btnScale }] }}>
          <Pressable
            style={({ pressed }) => [
              styles.analyzeBtn,
              !image && styles.analyzeBtnDisabled,
              pressed && !!image && styles.analyzeBtnPressed,
            ]}
            onPressIn={onPressIn}
            onPressOut={onPressOut}
            onPress={analyze}
            disabled={!image || loading}
          >
            <Text style={styles.analyzeBtnIcon}>🔬</Text>
            <Text style={styles.analyzeBtnTxt}>{loading ? 'Analyzing…' : 'Analyze Leaf'}</Text>
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

  backRow:  { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 14, paddingTop: 4 },
  backBtn:  { width: 32, height: 32, backgroundColor: C.card, borderWidth: 1, borderColor: C.border, borderRadius: 16,
              alignItems: 'center', justifyContent: 'center',
              shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 3, shadowOffset: { width: 0, height: 1 }, elevation: 1 },
  backArrow:{ fontSize: 16, color: C.text },
  screenTitle: { fontSize: 18, fontWeight: '800', color: C.text },
  // Deliberately small and low-contrast -- a dev/testing entry point, not
  // meant to draw attention during a normal demo.
  settingsBtn:  { width: 26, height: 26, alignItems: 'center', justifyContent: 'center' },
  settingsIcon: { fontSize: 15, color: C.muted },

  heroCard: {
    backgroundColor: C.card,
    borderRadius: 22, borderWidth: 1, borderColor: C.cardBorder,
    padding: 18, marginBottom: 14, overflow: 'hidden',
    shadowColor: '#24352A', shadowOpacity: 0.06, shadowRadius: 10, shadowOffset: { width: 0, height: 4 }, elevation: 2,
  },
  heroIconCircle: {
    width: 44, height: 44, borderRadius: 22,
    backgroundColor: C.tomatoDim, borderWidth: 1, borderColor: C.tomatoBorder,
    alignItems: 'center', justifyContent: 'center', marginBottom: 12,
  },
  heroTitle:  { fontSize: 22, fontWeight: '800', color: C.text, lineHeight: 28, marginBottom: 8 },
  heroTitleAccent: { color: C.tomato },
  heroHelper: { fontSize: 12.5, color: C.muted, lineHeight: 19 },

  uploadArea: {
    width: '100%', minHeight: 200,
    backgroundColor: C.softGreen,
    borderRadius: 18, borderWidth: 1.5, borderColor: C.leafBorder, borderStyle: 'dashed',
    overflow: 'hidden', marginBottom: 14,
    alignItems: 'center', justifyContent: 'center',
  },
  // Once an image is selected, the image itself should be the focus --
  // plain white container, no dashed border competing for attention.
  uploadAreaFilled: { backgroundColor: C.card, borderStyle: 'solid', borderColor: C.cardBorder, borderWidth: 1 },
  uploadPlaceholder:    { alignItems: 'center', gap: 6, paddingVertical: 30, paddingHorizontal: 24 },
  uploadIconCircle:     { width: 60, height: 60, borderRadius: 30, backgroundColor: C.card, borderWidth: 1, borderColor: C.leafBorder,
                          alignItems: 'center', justifyContent: 'center', marginBottom: 6 },
  uploadPlaceholderTitle:{ fontSize: 14, fontWeight: '700', color: C.text, textAlign: 'center' },
  uploadPlaceholderSub:  { fontSize: 11.5, color: C.muted, textAlign: 'center', lineHeight: 16, maxWidth: 220 },
  // 'contain' (not 'cover') -- cover was cropping the top/bottom off
  // portrait leaf photos to fill this fixed-height box; contain always
  // shows the full uploaded image, just letterboxed if the aspect ratio
  // doesn't match.
  uploadedImage:        { width: '100%', height: 220, resizeMode: 'contain' },
  imageBadge:           { position: 'absolute', bottom: 10, alignSelf: 'center',
                          backgroundColor: 'rgba(63,125,69,0.92)', borderRadius: 100,
                          paddingHorizontal: 12, paddingVertical: 5 },
  imageBadgeTxt:        { fontSize: 11, fontWeight: '700', color: '#fff' },
  uploadLoadingOverlay: { position: 'absolute', inset: 0, backgroundColor: 'rgba(248,247,242,0.9)', alignItems: 'center', justifyContent: 'center' },

  actionRow:       { flexDirection: 'row', gap: 10, marginBottom: 12 },
  actionBtn:       { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7, borderRadius: 14,
                     paddingVertical: 14, backgroundColor: C.card, borderWidth: 1.5, borderColor: C.leafBorder },
  actionBtnIcon:   { fontSize: 16 },
  actionBtnTxt:    { fontSize: 13, fontWeight: '700', color: C.leaf },

  analyzeBtn:         { backgroundColor: C.tomato, borderRadius: 16, paddingVertical: 17,
                        flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8,
                        shadowColor: C.tomatoDark, shadowOpacity: 0.28, shadowRadius: 10, shadowOffset: { width: 0, height: 5 }, elevation: 4 },
  analyzeBtnPressed: { backgroundColor: C.tomatoDark },
  analyzeBtnDisabled: { backgroundColor: '#d9a6a1', shadowOpacity: 0 },
  analyzeBtnIcon:     { fontSize: 16 },
  analyzeBtnTxt:      { fontSize: 15, fontWeight: '800', color: '#fff', letterSpacing: 0.3 },
  analyzeHint:        { fontSize: 11, color: C.muted, textAlign: 'center', marginTop: 10 },
});
