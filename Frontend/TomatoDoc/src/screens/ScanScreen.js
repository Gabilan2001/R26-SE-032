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
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import * as ImagePicker from 'expo-image-picker';
import { predictNutrient } from '../api/scanApi';
import { AuthContext } from '../context/AuthContext';
import LoadingOverlay from '../components/LoadingOverlay';

const C = {
  bg: '#0f0f0f',
  surface: '#1a1a1a',
  surface2: '#222222',
  accent: '#c8f135',
  accentDim: 'rgba(200,241,53,0.10)',
  accentBorder: 'rgba(200,241,53,0.22)',
  text: '#f0f0f0',
  muted: '#666666',
  border: 'rgba(255,255,255,0.07)',
  leaf: '#4adf6f',
  leafDim: 'rgba(74,223,111,0.10)',
};

function ViewfinderFrame() {
  const size = 24;
  const t = 18;
  const corner = (pos) => ({
    position: 'absolute',
    width: size,
    height: size,
    borderColor: C.accent,
    ...(pos.top !== undefined && { top: pos.top }),
    ...(pos.bottom !== undefined && { bottom: pos.bottom }),
    ...(pos.left !== undefined && { left: pos.left }),
    ...(pos.right !== undefined && { right: pos.right }),
    borderTopWidth: pos.top !== undefined ? 2.5 : 0,
    borderBottomWidth: pos.bottom !== undefined ? 2.5 : 0,
    borderLeftWidth: pos.left !== undefined ? 2.5 : 0,
    borderRightWidth: pos.right !== undefined ? 2.5 : 0,
    borderTopLeftRadius: pos.top !== undefined && pos.left !== undefined ? 6 : 0,
    borderTopRightRadius: pos.top !== undefined && pos.right !== undefined ? 6 : 0,
    borderBottomLeftRadius: pos.bottom !== undefined && pos.left !== undefined ? 6 : 0,
    borderBottomRightRadius: pos.bottom !== undefined && pos.right !== undefined ? 6 : 0,
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
        Animated.timing(anim, { toValue: 1, duration: 2200, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(anim, { toValue: 0, duration: 2200, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ])
    ).start();
  }, [anim]);

  const translateY = anim.interpolate({ inputRange: [0, 1], outputRange: [0, 200] });

  return (
    <Animated.View
      pointerEvents="none"
      style={[styles.scanLine, { transform: [{ translateY }] }]}
    />
  );
}

export default function ScanScreen({ navigation }) {
  const { token } = useContext(AuthContext);
  const insets = useSafeAreaInsets();
  const [image, setImage] = useState(null);
  const [loading, setLoading] = useState(false);

  const fadeIn = useRef(new Animated.Value(0)).current;
  const slideUp = useRef(new Animated.Value(16)).current;
  const btnScale = useRef(new Animated.Value(1)).current;
  const pulse = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeIn, { toValue: 1, duration: 400, useNativeDriver: true }),
      Animated.spring(slideUp, { toValue: 0, useNativeDriver: true }),
    ]).start();

    Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, { toValue: 1.04, duration: 1400, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(pulse, { toValue: 1, duration: 1400, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ])
    ).start();
  }, [fadeIn, slideUp, pulse]);

  const onPressIn = () => Animated.spring(btnScale, { toValue: 0.97, useNativeDriver: true }).start();
  const onPressOut = () => Animated.spring(btnScale, { toValue: 1, useNativeDriver: true }).start();

  const pickImage = async (fromCamera = false) => {
    const launcher = fromCamera
      ? ImagePicker.launchCameraAsync
      : ImagePicker.launchImageLibraryAsync;
    const res = await launcher({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.85,
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
        const blob = await response.blob();
        const file = new File([blob], 'leaf.jpg', { type: blob.type || 'image/jpeg' });
        formData.append('image', file);
      } else {
        formData.append('image', {
          uri: image.uri,
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
        contentContainerStyle={[
          styles.content,
          { paddingTop: insets.top + 12, paddingBottom: insets.bottom + 100 },
        ]}
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()} activeOpacity={0.75}>
            <MaterialCommunityIcons name="arrow-left" size={20} color={C.text} />
          </TouchableOpacity>
          <View style={styles.headerText}>
            <Text style={styles.screenTitle}>Leaf Scanner</Text>
            <Text style={styles.screenSub}>Nutrient deficiency detection</Text>
          </View>
          <View style={styles.readyBadge}>
            <View style={styles.readyDot} />
            <Text style={styles.readyText}>Ready</Text>
          </View>
        </View>

        <Animated.View style={{ opacity: fadeIn, transform: [{ translateY: slideUp }] }}>
          {/* Module strip */}
          <View style={styles.moduleStrip}>
            <View style={styles.moduleIcon}>
              <MaterialCommunityIcons name="leaf" size={22} color={C.leaf} />
            </View>
            <View style={styles.moduleBody}>
              <Text style={styles.moduleTitle}>Scan a tomato leaf</Text>
              <Text style={styles.moduleSub}>
                Photograph one clear leaf — we will detect nutrient issues and suggest fertilizer.
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
                <View style={styles.vfEmpty}>
                  <Animated.View style={[styles.vfIconWrap, { transform: [{ scale: pulse }] }]}>
                    <MaterialCommunityIcons name="camera-outline" size={32} color={C.muted} />
                  </Animated.View>
                  <Text style={styles.vfEmptyTitle}>No photo yet</Text>
                  <Text style={styles.vfEmptySub}>Center the leaf in the frame below</Text>
                </View>
              )}

              {image && (
                <View style={styles.capturedBar}>
                  <View style={styles.capturedLeft}>
                    <MaterialCommunityIcons name="check-circle" size={16} color={C.accent} />
                    <Text style={styles.capturedText}>Image captured</Text>
                  </View>
                  <TouchableOpacity onPress={() => setImage(null)} activeOpacity={0.75}>
                    <Text style={styles.retakeText}>Retake</Text>
                  </TouchableOpacity>
                </View>
              )}

              <View style={styles.sourceBar}>
                <TouchableOpacity
                  style={styles.sourceBtn}
                  onPress={() => pickImage(false)}
                  activeOpacity={0.8}
                >
                  <MaterialCommunityIcons name="image-outline" size={18} color={C.text} />
                  <Text style={styles.sourceBtnText}>Gallery</Text>
                </TouchableOpacity>
                <View style={styles.sourceDivider} />
                <TouchableOpacity
                  style={[styles.sourceBtn, styles.sourceBtnPrimary]}
                  onPress={() => pickImage(true)}
                  activeOpacity={0.8}
                >
                  <MaterialCommunityIcons name="camera-outline" size={18} color="#0f0f0f" />
                  <Text style={styles.sourceBtnTextDark}>Camera</Text>
                </TouchableOpacity>
              </View>

              {loading && (
                <View style={styles.vfLoading}>
                  <LoadingOverlay text="Analyzing leaf..." />
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
                <View style={styles.tipIconWrap}>
                  <MaterialCommunityIcons name="leaf" size={18} color={C.leaf} />
                </View>
                <Text style={styles.tipItemText}>One leaf{'\n'}only</Text>
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
              <MaterialCommunityIcons
                name="magnify-scan"
                size={20}
                color={image ? '#0f0f0f' : C.muted}
              />
              <Text style={[styles.analyzeBtnText, !image && styles.analyzeBtnTextIdle]}>
                Run analysis
              </Text>
            </Pressable>
          </Animated.View>

          {/* Tip */}
          <View style={styles.tipBox}>
            <MaterialCommunityIcons name="information-outline" size={16} color={C.accent} />
            <Text style={styles.tipText}>
              {image
                ? 'Photo looks good. Tap Run analysis to get your diagnosis.'
                : 'Use natural daylight and fill the frame with one leaf for best accuracy.'}
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

  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 20,
  },
  backBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerText: { flex: 1 },
  screenTitle: { fontSize: 20, fontWeight: '700', color: C.text },
  screenSub: { fontSize: 12, color: C.muted, marginTop: 2 },
  readyBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: C.accentDim,
    borderWidth: 1,
    borderColor: C.accentBorder,
    borderRadius: 100,
    paddingHorizontal: 10,
    paddingVertical: 5,
  },
  readyDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: C.accent },
  readyText: { fontSize: 11, fontWeight: '700', color: C.accent },

  moduleStrip: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 14,
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
  },
  moduleIcon: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: C.leafDim,
    alignItems: 'center',
    justifyContent: 'center',
  },
  moduleBody: { flex: 1 },
  moduleTitle: { fontSize: 15, fontWeight: '700', color: C.text, marginBottom: 4 },
  moduleSub: { fontSize: 13, color: C.muted, lineHeight: 19 },

  scanCard: {
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 18,
    padding: 14,
    marginBottom: 16,
  },
  viewfinder: {
    width: '100%',
    height: 260,
    backgroundColor: C.surface2,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: C.accentBorder,
    overflow: 'hidden',
    alignItems: 'center',
    justifyContent: 'center',
  },
  scanLine: {
    position: 'absolute',
    left: 24,
    right: 24,
    height: 1.5,
    backgroundColor: C.accent,
    opacity: 0.45,
  },
  vfImage: { position: 'absolute', width: '100%', height: '100%', resizeMode: 'cover' },
  vfEmpty: { alignItems: 'center', gap: 6, paddingHorizontal: 24, paddingBottom: 56 },
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
  vfEmptyTitle: { fontSize: 15, fontWeight: '600', color: C.text },
  vfEmptySub: { fontSize: 12, color: C.muted, textAlign: 'center' },

  capturedBar: {
    position: 'absolute',
    top: 12,
    left: 12,
    right: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: 'rgba(15,15,15,0.85)',
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: C.border,
  },
  capturedLeft: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  capturedText: { fontSize: 12, fontWeight: '600', color: C.text },
  retakeText: { fontSize: 12, fontWeight: '700', color: C.accent },

  sourceBar: {
    position: 'absolute',
    bottom: 12,
    left: 12,
    right: 12,
    flexDirection: 'row',
    backgroundColor: 'rgba(15,15,15,0.90)',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: C.border,
    overflow: 'hidden',
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
  sourceBtnText: { fontSize: 13, fontWeight: '600', color: C.text },
  sourceBtnTextDark: { fontSize: 13, fontWeight: '700', color: '#0f0f0f' },

  vfLoading: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(15,15,15,0.92)',
    alignItems: 'center',
    justifyContent: 'center',
  },

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
    borderRadius: 14,
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
  tipItemText: {
    fontSize: 11,
    fontWeight: '600',
    color: C.text,
    textAlign: 'center',
    lineHeight: 15,
    opacity: 0.85,
  },

  analyzeBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    borderRadius: 14,
    paddingVertical: 16,
    marginBottom: 14,
  },
  analyzeBtnActive: { backgroundColor: C.accent },
  analyzeBtnIdle: {
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
  },
  analyzeBtnText: { fontSize: 15, fontWeight: '700', color: '#0f0f0f' },
  analyzeBtnTextIdle: { color: C.muted },

  tipBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    padding: 14,
    borderRadius: 14,
    backgroundColor: C.accentDim,
    borderWidth: 1,
    borderColor: C.accentBorder,
  },
  tipText: { flex: 1, fontSize: 12, color: C.text, lineHeight: 18, opacity: 0.85 },
});
