import React, { useEffect, useRef, useState } from 'react';
import {
  Alert,
  Animated,
  Image,
  Linking,
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
import LoadingOverlay from '../../../components/LoadingOverlay';
import ScreenHeader, { HeaderBadge } from '../../../components/ScreenHeader';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { palette as P, radius, shadow } from '../../../theme';

// ── Tokens: shared TomatoDoc theme (see src/theme) ──────────────────────────────
const C = {
  bg:           P.bg,
  card:         P.surface,
  cardBorder:   P.border,
  tomato:       P.tomato,
  tomatoDark:   '#C9362C',
  tomatoDim:    P.tomatoDim,
  tomatoBorder: '#F5C5BF',
  leaf:         P.forestMid,
  leafDim:      P.surfaceTint,
  leafBorder:   '#CFE3B8',
  softGreen:    P.surface2,
  text:         P.text,
  muted:        P.muted,
  border:       P.border,
};

// ── Main Screen ───────────────────────────────────────────────────────────────
export default function DiseaseScanScreen({ navigation }) {
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
    let res;
    try {
      if (fromCamera && Platform.OS !== 'web') {
        // Ask explicitly so a refusal is explained instead of the button silently doing nothing.
        const perm = await ImagePicker.requestCameraPermissionsAsync();
        if (!perm.granted) {
          Alert.alert(
            'Camera permission needed',
            'Allow camera access for TomatoDoc (or Expo Go) in your phone settings to take a leaf photo.',
            [
              { text: 'Cancel', style: 'cancel' },
              { text: 'Open Settings', onPress: () => Linking.openSettings() },
            ]
          );
          return;
        }
      }
      res = await launcher({ mediaTypes: ['images'], quality: 0.8 });
    } catch (error) {
      Alert.alert(
        fromCamera ? 'Camera unavailable' : 'Gallery unavailable',
        error?.message || 'Could not open the picker on this device.'
      );
      return;
    }
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
      <StatusBar barStyle="light-content" backgroundColor={P.forest} />

      <ScreenHeader
        title="Disease Scanner"
        subtitle="Leaf disease and pest detection"
        eyebrow="Disease module"
        onBack={() => navigation.goBack()}
        right={
          <TouchableOpacity
            style={styles.settingsBtn}
            onPress={() => navigation.navigate('DiseaseSettings')}
            hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
          >
            <MaterialCommunityIcons name="cog-outline" size={18} color={P.onDarkSoft} />
          </TouchableOpacity>
        }
      />

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={[styles.content, { paddingTop: 18, paddingBottom: insets.bottom + 110 }]}
        showsVerticalScrollIndicator={false}
      >
        <Animated.View style={{ opacity: heroOp, transform: [{ translateY: heroY }] }}>
          {/* ── Module strip ── */}
          <View style={styles.moduleStrip}>
            <View style={styles.moduleIcon}>
              <MaterialCommunityIcons name="virus-outline" size={22} color={P.tomato} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.moduleTitle}>Leaf disease and pest scan</Text>
              <Text style={styles.moduleSub}>
                Take a clear photo of a tomato leaf to check for Early Blight, Late Blight, Leaf Miner,
                or a Healthy leaf, with treatment advice.
              </Text>
            </View>
          </View>

          {/* ── Scan card ── */}
          <View style={styles.scanCard}>
            <View style={[styles.uploadArea, image && styles.uploadAreaFilled]}>
              {image ? (
                <>
                  <Image source={{ uri: image.uri }} style={styles.uploadedImage} />
                  <View style={styles.imageBadge}>
                    <MaterialCommunityIcons name="check-circle" size={13} color="#FFFFFF" />
                    <Text style={styles.imageBadgeTxt}>Leaf photo selected</Text>
                  </View>
                </>
              ) : (
                <View style={styles.uploadPlaceholder}>
                  <View style={styles.uploadIconCircle}>
                    <MaterialCommunityIcons name="camera-outline" size={30} color={C.muted} />
                  </View>
                  <Text style={styles.uploadPlaceholderTitle}>Upload or capture a leaf image</Text>
                  <Text style={styles.uploadPlaceholderSub}>A clear, well-lit photo of a single tomato leaf works best</Text>
                </View>
              )}

              <View style={styles.sourceBar}>
                <TouchableOpacity style={styles.sourceBtn} onPress={() => pickImage(false)} activeOpacity={0.8}>
                  <MaterialCommunityIcons name="image-outline" size={18} color={C.text} />
                  <Text style={styles.sourceBtnText}>Gallery</Text>
                </TouchableOpacity>
                <View style={styles.sourceDivider} />
                <TouchableOpacity style={[styles.sourceBtn, styles.sourceBtnPrimary]} onPress={() => pickImage(true)} activeOpacity={0.8}>
                  <MaterialCommunityIcons name="camera-outline" size={18} color={P.onDark} />
                  <Text style={styles.sourceBtnTextLight}>Camera</Text>
                </TouchableOpacity>
              </View>

              {loading && (
                <View style={styles.uploadLoadingOverlay}>
                  <LoadingOverlay text={'Analyzing leaf…'} />
                </View>
              )}
            </View>
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
              <MaterialCommunityIcons name="magnify-scan" size={20} color={image ? P.onDark : C.muted} />
              <Text style={[styles.analyzeBtnTxt, !image && styles.analyzeBtnTxtDisabled]}>
                {loading ? 'Analyzing…' : 'Analyze Leaf'}
              </Text>
            </Pressable>
          </Animated.View>

          <View style={styles.hintBox}>
            <MaterialCommunityIcons name="information-outline" size={16} color={C.leaf} />
            <Text style={styles.analyzeHint}>
              {image ? 'Image ready. Tap Analyze Leaf to continue.' : 'Select or capture an image to begin.'}
            </Text>
          </View>
        </Animated.View>
      </ScrollView>
    </View>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  root:    { flex: 1, backgroundColor: C.bg },
  scroll:  { flex: 1 },
  content: { paddingHorizontal: 18 },

  // Deliberately small and low-contrast: a dev/testing entry point, not meant
  // to draw attention during a normal demo.
  settingsBtn: { width: 34, height: 34, borderRadius: 12, alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(255,255,255,0.08)' },

  moduleStrip: {
    flexDirection: 'row', alignItems: 'flex-start', gap: 14,
    backgroundColor: C.card, borderWidth: 1, borderColor: C.cardBorder,
    borderRadius: radius.lg, padding: 16, marginBottom: 16, ...shadow.card,
  },
  moduleIcon: { width: 46, height: 46, borderRadius: 14, backgroundColor: C.tomatoDim, alignItems: 'center', justifyContent: 'center' },
  moduleTitle: { fontSize: 15, fontWeight: '800', color: C.text, marginBottom: 4, letterSpacing: -0.2 },
  moduleSub: { fontSize: 13, color: P.textSoft, lineHeight: 19 },

  scanCard: {
    backgroundColor: C.card, borderWidth: 1, borderColor: C.cardBorder,
    borderRadius: radius.lg, padding: 14, marginBottom: 16, ...shadow.card,
  },
  uploadArea: {
    width: '100%', height: 280,
    backgroundColor: C.softGreen,
    borderRadius: 14, borderWidth: 1.5, borderColor: C.leafBorder, borderStyle: 'dashed',
    overflow: 'hidden',
    alignItems: 'center', justifyContent: 'center',
  },
  // Once an image is selected, the image itself is the focus.
  uploadAreaFilled: { backgroundColor: C.card, borderStyle: 'solid', borderColor: C.cardBorder, borderWidth: 1 },
  uploadPlaceholder:    { alignItems: 'center', gap: 6, paddingHorizontal: 24, paddingBottom: 56 },
  uploadIconCircle:     { width: 64, height: 64, borderRadius: 32, backgroundColor: C.card, borderWidth: 1, borderColor: C.border,
                          alignItems: 'center', justifyContent: 'center', marginBottom: 6 },
  uploadPlaceholderTitle:{ fontSize: 15, fontWeight: '700', color: C.text, textAlign: 'center' },
  uploadPlaceholderSub:  { fontSize: 12, color: C.muted, textAlign: 'center', lineHeight: 17, maxWidth: 230 },
  // 'contain' shows the full uploaded image, letterboxed if the ratio differs.
  uploadedImage:        { width: '100%', height: '100%', resizeMode: 'contain' },
  imageBadge:           { position: 'absolute', top: 12, alignSelf: 'center', flexDirection: 'row', alignItems: 'center', gap: 5,
                          backgroundColor: 'rgba(31,96,68,0.94)', borderRadius: 100,
                          paddingHorizontal: 12, paddingVertical: 6 },
  imageBadgeTxt:        { fontSize: 11, fontWeight: '700', color: '#fff' },
  uploadLoadingOverlay: { position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(251,250,245,0.94)', alignItems: 'center', justifyContent: 'center' },

  sourceBar: {
    position: 'absolute', bottom: 12, left: 12, right: 12, flexDirection: 'row',
    backgroundColor: 'rgba(255,255,255,0.96)', borderRadius: 14, borderWidth: 1, borderColor: C.border,
    overflow: 'hidden', ...shadow.card,
  },
  sourceBtn: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7, paddingVertical: 12 },
  sourceBtnPrimary: { backgroundColor: C.leaf },
  sourceDivider: { width: 1, backgroundColor: C.border },
  sourceBtnText: { fontSize: 13, fontWeight: '700', color: C.text },
  sourceBtnTextLight: { fontSize: 13, fontWeight: '700', color: P.onDark },

  analyzeBtn: {
    backgroundColor: C.leaf, borderRadius: radius.md, paddingVertical: 16, marginBottom: 14,
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, ...shadow.raised,
  },
  analyzeBtnPressed: { backgroundColor: P.forest },
  analyzeBtnDisabled: { backgroundColor: C.card, borderWidth: 1, borderColor: C.border, shadowOpacity: 0, elevation: 0, boxShadow: 'none' },
  analyzeBtnTxt:      { fontSize: 15, fontWeight: '700', color: '#fff', letterSpacing: 0.2 },
  analyzeBtnTxtDisabled: { color: C.muted },

  hintBox: {
    flexDirection: 'row', alignItems: 'flex-start', gap: 10, padding: 14,
    borderRadius: radius.md, backgroundColor: P.surfaceTint, borderWidth: 1, borderColor: '#D5E7BD',
  },
  analyzeHint: { flex: 1, fontSize: 12, color: P.textSoft, lineHeight: 18 },
});
