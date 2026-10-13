import React, { useContext, useEffect, useRef, useState } from 'react';
import {
  Alert,
  Animated,
  Dimensions,
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
  Modal,
} from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import * as ImagePicker from 'expo-image-picker';
import { predictFruitDisease } from '../api/fruitScanApi';
import { UIThemeContext } from '../context/UIThemeContext';
import LoadingOverlay from '../components/LoadingOverlay';
import { LinearGradient } from 'expo-linear-gradient';

import { palette as P, radius, shadow } from '../theme';
import ScreenHeader, { HeaderBadge } from '../components/ScreenHeader';
const { width, height } = Dimensions.get('window');

const C = {
  bg: P.bg,
  surface: P.surface,
  surface2: P.surface2,
  accent: P.forestMid,
  gradient: [P.leaf, P.lime],
  accentDim: P.surfaceTint,
  accentBorder: '#CFE3B8',
  text: P.text,
  textSecondary: P.textSoft,
  muted: P.muted,
  border: P.border,
  danger: P.danger,
  dangerDim: P.dangerDim,
  success: P.good,
};

// ============= NEW COMPONENTS =============

function AnimatedProgressBar({ progress }) {
  const widthAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(widthAnim, {
      toValue: progress,
      duration: 600,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: false,
    }).start();
  }, [progress]);

  return (
    <View style={styles.progressContainer}>
      <View style={styles.progressTrack}>
        <Animated.View
          style={[
            styles.progressFill,
            { width: widthAnim.interpolate({ inputRange: [0, 1], outputRange: ['0%', '100%'] }) },
          ]}
        >
          <LinearGradient
            colors={C.gradient}
            style={StyleSheet.absoluteFill}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
          />
        </Animated.View>
      </View>
    </View>
  );
}

function ImagePreviewModal({ visible, imageUri, onClose, onAnalyze }) {
  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onClose}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.modalContent}>
          <TouchableOpacity style={styles.modalClose} onPress={onClose}>
            <MaterialCommunityIcons name="close" size={24} color="#ffffff" />
          </TouchableOpacity>
          
          <Image source={{ uri: imageUri }} style={styles.modalImage} />
          
          <View style={styles.modalActions}>
            <TouchableOpacity style={styles.modalBtnSecondary} onPress={onClose}>
              <Text style={styles.modalBtnText}>Retake</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.modalBtnPrimary} onPress={onAnalyze}>
              <MaterialCommunityIcons name="microscope" size={20} color="#FFFFFF" />
              <Text style={styles.modalBtnTextDark}>Analyze</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
}

// ============= EXISTING COMPONENTS (Enhanced) =============

function ViewfinderFrame() {
  const size = 28;
  const t = 16;
  const corner = (pos) => ({
    position: 'absolute',
    width: size,
    height: size,
    borderColor: P.forestMid,
    borderStyle: 'solid',
    ...(pos.top !== undefined && { top: pos.top }),
    ...(pos.bottom !== undefined && { bottom: pos.bottom }),
    ...(pos.left !== undefined && { left: pos.left }),
    ...(pos.right !== undefined && { right: pos.right }),
    borderTopWidth: pos.top !== undefined ? 3 : 0,
    borderBottomWidth: pos.bottom !== undefined ? 3 : 0,
    borderLeftWidth: pos.left !== undefined ? 3 : 0,
    borderRightWidth: pos.right !== undefined ? 3 : 0,
    borderTopLeftRadius: pos.top !== undefined && pos.left !== undefined ? 8 : 0,
    borderTopRightRadius: pos.top !== undefined && pos.right !== undefined ? 8 : 0,
    borderBottomLeftRadius: pos.bottom !== undefined && pos.left !== undefined ? 8 : 0,
    borderBottomRightRadius: pos.bottom !== undefined && pos.right !== undefined ? 8 : 0,
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

function ScanLine() {
  const anim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(anim, { toValue: 1, duration: 2000, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(anim, { toValue: 0, duration: 2000, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ])
    ).start();
  }, [anim]);

  const translateY = anim.interpolate({ inputRange: [0, 1], outputRange: [0, 130] });

  return (
    <Animated.View
      pointerEvents="none"
      style={[styles.scanLine, { transform: [{ translateY }] }]}
    >
      <LinearGradient
        colors={['transparent', P.leaf, P.lime, 'transparent']}
        style={StyleSheet.absoluteFill}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 0 }}
      />
    </Animated.View>
  );
}

// ============= MAIN SCREEN =============

export default function FruitScanScreen({ navigation }) {
  const { presentationMode } = useContext(UIThemeContext);
  const insets = useSafeAreaInsets();
  const [image, setImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [scanProgress, setScanProgress] = useState(0);

  const heroOp = useRef(new Animated.Value(0)).current;
  const heroY = useRef(new Animated.Value(30)).current;
  const btnScale = useRef(new Animated.Value(1)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const floatAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(heroOp, { toValue: 1, duration: 500, useNativeDriver: true }),
      Animated.spring(heroY, { toValue: 0, useNativeDriver: true }),
    ]).start();

    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 1.05, duration: 1500, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 1, duration: 1500, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ])
    ).start();

    Animated.loop(
      Animated.sequence([
        Animated.timing(floatAnim, { toValue: 1, duration: 3000, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(floatAnim, { toValue: 0, duration: 3000, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ])
    ).start();
  }, [heroOp, heroY, pulseAnim, floatAnim]);

  const onPressIn = () => Animated.spring(btnScale, { toValue: 0.95, useNativeDriver: true }).start();
  const onPressOut = () => Animated.spring(btnScale, { toValue: 1, useNativeDriver: true }).start();

  const pickImage = async (fromCamera = false) => {
    const launcher = fromCamera
      ? ImagePicker.launchCameraAsync
      : ImagePicker.launchImageLibraryAsync;
    const res = await launcher({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.85,
    });
    if (!res.canceled) {
      setImage(res.assets[0]);
      setShowPreview(true);
    }
  };

  const analyze = async () => {
    if (!image) return;
    setShowPreview(false);
    setLoading(true);
    setScanProgress(0);
    
    // Simulate progress
    const progressInterval = setInterval(() => {
      setScanProgress(prev => {
        if (prev >= 0.9) {
          clearInterval(progressInterval);
          return 0.9;
        }
        return prev + 0.1;
      });
    }, 300);

    try {
      const formData = new FormData();
      if (Platform.OS === 'web') {
        const response = await fetch(image.uri);
        const blob = await response.blob();
        const file = new File([blob], 'tomato-fruit.jpg', { type: blob.type || 'image/jpeg' });
        formData.append('image', file);
      } else {
        formData.append('image', {
          uri: image.uri,
          name: image.fileName || `tomato-fruit-${Date.now()}.jpg`,
          type: image.mimeType || 'image/jpeg',
        });
      }
      
      const res = await predictFruitDisease(formData);
      setScanProgress(1);
      setTimeout(() => {
        navigation.navigate('FruitResult', { result: res.data, imageUri: image.uri });
      }, 300);
    } catch (error) {
      Alert.alert(
        'Analysis Failed',
        error?.response?.data?.error || error?.message || 'Could not analyze this image.'
      );
    } finally {
      clearInterval(progressInterval);
      setTimeout(() => {
        setLoading(false);
        setScanProgress(0);
      }, 500);
    }
  };

  const floatY = floatAnim.interpolate({ inputRange: [0, 1], outputRange: [0, -6] });

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" backgroundColor={P.forest} />

      <ImagePreviewModal
        visible={showPreview}
        imageUri={image?.uri}
        onClose={() => setShowPreview(false)}
        onAnalyze={analyze}
      />

      <ScreenHeader
        title="Fruit Scanner"
        subtitle="Tomato fruit disease detection"
        eyebrow="Fruit module"
        onBack={() => navigation.goBack()}
        right={<HeaderBadge label="Ready" />}
      />

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={[styles.content, { paddingTop: 18, paddingBottom: insets.bottom + 110 }]}
        showsVerticalScrollIndicator={false}
      >
        <Animated.View style={{ opacity: heroOp, transform: [{ translateY: heroY }] }}>
          {/* Module strip */}
          <View style={styles.moduleStrip}>
            <Animated.View style={[styles.moduleIcon, { transform: [{ translateY: floatY }] }]}>
              <MaterialCommunityIcons name="food-apple" size={22} color={P.tomato} />
            </Animated.View>
            <View style={styles.moduleBody}>
              <Text style={[styles.moduleTitle, presentationMode && { fontSize: 18 }]}>Detect tomato fruit diseases</Text>
              <Text style={styles.moduleSub}>
                Capture a photo or choose one from your gallery. We will identify the disease and suggest treatment.
              </Text>
            </View>
          </View>

          {/* Scan card */}
          <View style={styles.scanCard}>
            <View style={styles.viewfinder}>
              <ViewfinderFrame />
              {!image && <ScanLine />}

              {image ? (
                <Image source={{ uri: image.uri }} style={styles.vfImage} />
              ) : (
                <View style={styles.vfPlaceholder}>
                  <Animated.View style={[styles.vfIconWrap, { transform: [{ scale: pulseAnim }] }]}>
                    <MaterialCommunityIcons name="camera-outline" size={32} color={C.muted} />
                  </Animated.View>
                  <Text style={styles.vfPlaceholderTitle}>No photo yet</Text>
                  <Text style={styles.vfPlaceholderTxt}>Place the tomato fruit inside the frame</Text>
                </View>
              )}

              <View style={styles.sourceBar}>
                <TouchableOpacity style={styles.sourceBtn} onPress={() => pickImage(false)} activeOpacity={0.8}>
                  <MaterialCommunityIcons name="image-outline" size={18} color={C.text} />
                  <Text style={styles.sourceBtnText}>Gallery</Text>
                </TouchableOpacity>
                <View style={styles.sourceDivider} />
                <TouchableOpacity
                  style={[styles.sourceBtn, styles.sourceBtnPrimary]}
                  onPress={() => pickImage(true)}
                  activeOpacity={0.8}
                >
                  <MaterialCommunityIcons name="camera-outline" size={18} color={P.onDark} />
                  <Text style={styles.sourceBtnTextLight}>Camera</Text>
                </TouchableOpacity>
              </View>

              {loading && (
                <View style={styles.vfLoadingOverlay}>
                  <LoadingOverlay text="Analyzing tomato fruit..." />
                  <AnimatedProgressBar progress={scanProgress} />
                </View>
              )}
            </View>
          </View>

          {/* Photo tips */}
          <View style={styles.tipsSection}>
            <Text style={styles.tipsSectionLabel}>For best results</Text>
            <View style={styles.tipsRow}>
              <View style={styles.tipItem}>
                <View style={styles.tipIconWrap}>
                  <MaterialCommunityIcons name="white-balance-sunny" size={18} color={C.accent} />
                </View>
                <Text style={styles.tipItemText}>Natural{'\n'}light</Text>
              </View>
              <View style={styles.tipItem}>
                <View style={styles.tipIconWrap}>
                  <MaterialCommunityIcons name="crop-free" size={18} color={C.accent} />
                </View>
                <Text style={styles.tipItemText}>Fill the{'\n'}frame</Text>
              </View>
              <View style={styles.tipItem}>
                <View style={[styles.tipIconWrap, { backgroundColor: P.tomatoDim }]}>
                  <MaterialCommunityIcons name="food-apple" size={18} color={P.tomato} />
                </View>
                <Text style={styles.tipItemText}>One fruit{'\n'}only</Text>
              </View>
            </View>
          </View>

          {/* Analyze */}
          <Animated.View style={{ transform: [{ scale: btnScale }] }}>
            <Pressable
              style={[styles.analyzeBtn, image ? styles.analyzeBtnActive : styles.analyzeBtnIdle]}
              onPressIn={onPressIn}
              onPressOut={onPressOut}
              onPress={analyze}
              disabled={!image || loading}
            >
              <MaterialCommunityIcons name="microscope" size={20} color={image ? P.onDark : C.muted} />
              <Text style={[styles.analyzeBtnTxt, !image && styles.analyzeBtnTxtDisabled]}>
                {image ? 'Analyze Fruit' : 'Select an image first'}
              </Text>
            </Pressable>
          </Animated.View>

          {/* Hint */}
          <View style={styles.hintBox}>
            <MaterialCommunityIcons name="information-outline" size={16} color={C.accent} />
            <Text style={styles.analyzeHint}>
              {image ? 'Image ready. Tap Analyze Fruit to continue.' : 'Select or capture an image to begin.'}
            </Text>
          </View>
        </Animated.View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: C.bg },
  scroll: { flex: 1 },
  content: { paddingHorizontal: 18 },

  moduleStrip: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 14,
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: radius.lg,
    padding: 16,
    marginBottom: 16,
    ...shadow.card,
  },
  moduleIcon: {
    width: 46,
    height: 46,
    borderRadius: 14,
    backgroundColor: P.tomatoDim,
    alignItems: 'center',
    justifyContent: 'center',
  },
  moduleBody: { flex: 1 },
  moduleTitle: { fontSize: 15, fontWeight: '800', color: C.text, marginBottom: 4, letterSpacing: -0.2 },
  moduleSub: { fontSize: 13, color: C.textSecondary, lineHeight: 19 },

  scanCard: {
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: radius.lg,
    padding: 14,
    marginBottom: 16,
    ...shadow.card,
  },
  viewfinder: {
    width: '100%',
    height: 280,
    backgroundColor: C.surface2,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: C.accentBorder,
    overflow: 'hidden',
    alignItems: 'center',
    justifyContent: 'center',
  },
  scanLine: { position: 'absolute', left: 24, right: 24, top: 60, height: 2, opacity: 0.7 },
  vfImage: { position: 'absolute', width: '100%', height: '100%', resizeMode: 'cover' },
  vfPlaceholder: { alignItems: 'center', gap: 6, paddingHorizontal: 24, paddingBottom: 56 },
  vfIconWrap: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: C.bg,
    borderWidth: 1,
    borderColor: C.border,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  vfPlaceholderTitle: { fontSize: 15, fontWeight: '700', color: C.text },
  vfPlaceholderTxt: { fontSize: 12, color: C.muted, textAlign: 'center' },
  vfLoadingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(251,250,245,0.94)',
    alignItems: 'center',
    justifyContent: 'center',
  },

  sourceBar: {
    position: 'absolute',
    bottom: 12,
    left: 12,
    right: 12,
    flexDirection: 'row',
    backgroundColor: 'rgba(255,255,255,0.96)',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: C.border,
    overflow: 'hidden',
    ...shadow.card,
  },
  sourceBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 7,
    paddingVertical: 12,
  },
  sourceBtnPrimary: { backgroundColor: C.accent },
  sourceDivider: { width: 1, backgroundColor: C.border },
  sourceBtnText: { fontSize: 13, fontWeight: '700', color: C.text },
  sourceBtnTextLight: { fontSize: 13, fontWeight: '700', color: P.onDark },

  tipsSection: { marginBottom: 16 },
  tipsSectionLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: C.muted,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    marginBottom: 10,
  },
  tipsRow: { flexDirection: 'row', gap: 10 },
  tipItem: {
    flex: 1,
    alignItems: 'center',
    gap: 8,
    backgroundColor: C.surface,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: C.border,
    paddingVertical: 14,
    paddingHorizontal: 6,
  },
  tipIconWrap: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: C.accentDim,
    alignItems: 'center',
    justifyContent: 'center',
  },
  tipItemText: { fontSize: 11, fontWeight: '700', color: C.text, textAlign: 'center', lineHeight: 15 },

  analyzeBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    borderRadius: radius.md,
    paddingVertical: 16,
    marginBottom: 14,
  },
  analyzeBtnActive: { backgroundColor: C.accent, ...shadow.raised },
  analyzeBtnIdle: { backgroundColor: C.surface, borderWidth: 1, borderColor: C.border },
  analyzeBtnTxt: { fontSize: 15, fontWeight: '700', color: P.onDark },
  analyzeBtnTxtDisabled: { color: C.muted },

  hintBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    padding: 14,
    borderRadius: radius.md,
    backgroundColor: C.accentDim,
    borderWidth: 1,
    borderColor: C.accentBorder,
  },
  analyzeHint: { flex: 1, fontSize: 12, color: C.textSecondary, lineHeight: 18 },

  progressContainer: { width: '80%', marginTop: 16 },
  progressTrack: { height: 6, borderRadius: 3, backgroundColor: P.border, overflow: 'hidden' },
  progressFill: { height: '100%', borderRadius: 3, overflow: 'hidden' },

  modalOverlay: { flex: 1, backgroundColor: 'rgba(14,51,38,0.88)', justifyContent: 'center', padding: 20 },
  modalContent: { alignItems: 'center' },
  modalClose: {
    alignSelf: 'flex-end',
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.14)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 14,
  },
  modalImage: { width: '100%', height: 360, borderRadius: radius.lg, resizeMode: 'cover' },
  modalActions: { flexDirection: 'row', gap: 12, marginTop: 18, width: '100%' },
  modalBtnSecondary: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.3)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  modalBtnPrimary: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: radius.md,
    backgroundColor: P.forestMid,
    flexDirection: 'row',
    gap: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  modalBtnText: { color: '#FFFFFF', fontWeight: '700', fontSize: 14 },
  modalBtnTextDark: { color: '#FFFFFF', fontWeight: '800', fontSize: 14 },
});
