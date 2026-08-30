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

const { width, height } = Dimensions.get('window');

const C = {
  bg: '#0a0a0f',
  surface: 'rgba(255,255,255,0.06)',
  surface2: 'rgba(255,255,255,0.03)',
  accent: '#7EE8FA',
  accent2: '#EEC0C6',
  gradient: ['#7EE8FA', '#EEC0C6'],
  accentDim: 'rgba(126,232,250,0.10)',
  accentBorder: 'rgba(126,232,250,0.20)',
  text: '#ffffff',
  textSecondary: 'rgba(255,255,255,0.7)',
  muted: 'rgba(255,255,255,0.4)',
  border: 'rgba(255,255,255,0.06)',
  danger: '#ff6b8a',
  dangerDim: 'rgba(255,107,138,0.12)',
  dangerBorder: 'rgba(255,107,138,0.20)',
  success: '#4ade80',
  glass: 'rgba(255,255,255,0.04)',
  glassBorder: 'rgba(255,255,255,0.08)',
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

function QuickActionCard({ icon, label, description, onPress, gradient }) {
  return (
    <TouchableOpacity style={styles.quickAction} onPress={onPress} activeOpacity={0.7}>
      <LinearGradient
        colors={gradient || ['rgba(255,255,255,0.04)', 'rgba(255,255,255,0.01)']}
        style={StyleSheet.absoluteFill}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      />
      <View style={styles.quickActionIcon}>
        <MaterialCommunityIcons name={icon} size={24} color={C.accent} />
      </View>
      <Text style={styles.quickActionLabel}>{label}</Text>
      <Text style={styles.quickActionDesc}>{description}</Text>
    </TouchableOpacity>
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
              <LinearGradient
                colors={C.gradient}
                style={StyleSheet.absoluteFill}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              />
              <MaterialCommunityIcons name="microscope" size={20} color="#0a0a0f" />
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
    borderColor: '#7EE8FA',
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
        colors={['transparent', '#7EE8FA', '#EEC0C6', 'transparent']}
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

  const floatY = floatAnim.interpolate({ inputRange: [0, 1], outputRange: [0, -8] });

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" backgroundColor="#0a0a0f" />
      <LinearGradient
        colors={['#0a0a0f', '#14141e']}
        style={StyleSheet.absoluteFill}
      />

      <ImagePreviewModal
        visible={showPreview}
        imageUri={image?.uri}
        onClose={() => setShowPreview(false)}
        onAnalyze={analyze}
      />

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={[
          styles.content,
          { paddingTop: insets.top + 16, paddingBottom: insets.bottom + 100 },
        ]}
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()} activeOpacity={0.7}>
            <MaterialCommunityIcons name="arrow-left" size={22} color="#ffffff" />
          </TouchableOpacity>
          <View style={styles.headerText}>
            <Text style={styles.screenTitle}>Fruit Scanner</Text>
            <Text style={styles.screenSub}>Tomato Disease Detection</Text>
          </View>
          <LinearGradient
            colors={['#ff6b8a', '#ee5a6f']}
            style={styles.headerIcon}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
          >
            <MaterialCommunityIcons name="food-apple" size={18} color="#ffffff" />
          </LinearGradient>
        </View>

        {/* Hero Card */}
        <Animated.View style={[styles.heroCard, { opacity: heroOp, transform: [{ translateY: heroY }] }]}>
          <LinearGradient
            colors={['rgba(126,232,250,0.08)', 'rgba(238,192,198,0.05)']}
            style={StyleSheet.absoluteFill}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
          />
          <View style={styles.heroTop}>
            <View style={styles.heroBadge}>
              <View style={styles.badgeDot} />
              <Text style={styles.badgeTxt}>AI Disease Classifier</Text>
            </View>
            <Animated.View style={{ transform: [{ translateY: floatY }] }}>
              <View style={styles.heroIconBox}>
                <MaterialCommunityIcons name="food-apple" size={22} color="#ff6b8a" />
              </View>
            </Animated.View>
          </View>

          <Text style={[styles.heroTitle, presentationMode && { fontSize: 24 }]}>
            Detect Tomato{'\n'}
            <Text style={styles.heroTitleAccent}>Diseases Instantly</Text>
          </Text>
          <Text style={styles.heroHelper}>
            Capture a photo or upload from gallery. Our AI will analyze and provide treatment recommendations.
          </Text>

          {/* Quick Actions */}
          <View style={styles.quickActionsRow}>
            <QuickActionCard
              icon="camera-outline"
              label="Camera"
              description="Take a photo"
              onPress={() => pickImage(true)}
              gradient={['rgba(126,232,250,0.08)', 'rgba(126,232,250,0.02)']}
            />
            <QuickActionCard
              icon="image-outline"
              label="Gallery"
              description="Choose from library"
              onPress={() => pickImage(false)}
              gradient={['rgba(238,192,198,0.08)', 'rgba(238,192,198,0.02)']}
            />
          </View>
        </Animated.View>

        {/* Viewfinder */}
        <View style={styles.viewfinder}>
          <LinearGradient
            colors={['rgba(126,232,250,0.05)', 'rgba(238,192,198,0.02)']}
            style={StyleSheet.absoluteFill}
          />
          <ViewfinderFrame />
          <ScanLine />

          {image ? (
            <Image source={{ uri: image.uri }} style={styles.vfImage} />
          ) : (
            <View style={styles.vfPlaceholder}>
              <Animated.View style={[styles.vfIconWrap, { transform: [{ scale: pulseAnim }] }]}>
                <LinearGradient
                  colors={['rgba(126,232,250,0.15)', 'rgba(238,192,198,0.10)']}
                  style={StyleSheet.absoluteFill}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                />
                <MaterialCommunityIcons name="camera-outline" size={36} color="rgba(255,255,255,0.4)" />
              </Animated.View>
              <Text style={styles.vfPlaceholderTitle}>No Image Selected</Text>
              <Text style={styles.vfPlaceholderTxt}>
                Place tomato fruit inside the frame{'\n'}or choose from gallery
              </Text>
            </View>
          )}

          {loading && (
            <View style={styles.vfLoadingOverlay}>
              <LoadingOverlay text="Analyzing tomato fruit..." />
              <AnimatedProgressBar progress={scanProgress} />
            </View>
          )}
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
                <MaterialCommunityIcons name="food-apple" size={18} color={C.danger} />
              </View>
              <Text style={styles.tipItemText}>One fruit{'\n'}only</Text>
            </View>
          </View>
        </View>

        {/* Action Buttons */}
        <View style={styles.actionRow}>
          <TouchableOpacity
            style={[styles.actionBtn, styles.actionBtnSecondary]}
            onPress={() => pickImage(false)}
            activeOpacity={0.7}
          >
            <MaterialCommunityIcons name="image-outline" size={20} color="#ffffff" />
            <Text style={styles.actionBtnTxt}>Gallery</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.actionBtn, styles.actionBtnPrimary]}
            onPress={() => pickImage(true)}
            activeOpacity={0.7}
          >
            <LinearGradient
              colors={C.gradient}
              style={StyleSheet.absoluteFill}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
            />
            <MaterialCommunityIcons name="camera-outline" size={20} color="#0a0a0f" />
            <Text style={styles.actionBtnTxtDark}>Camera</Text>
          </TouchableOpacity>
        </View>

        {/* Analyze Button */}
        <Animated.View style={{ transform: [{ scale: btnScale }] }}>
          <Pressable
            style={[styles.analyzeBtn, !image && styles.analyzeBtnDisabled]}
            onPressIn={onPressIn}
            onPressOut={onPressOut}
            onPress={analyze}
            disabled={!image || loading}
          >
            <LinearGradient
              colors={image ? ['#7EE8FA', '#EEC0C6'] : ['rgba(255,255,255,0.05)', 'rgba(255,255,255,0.02)']}
              style={StyleSheet.absoluteFill}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
            />
            <MaterialCommunityIcons name="microscope" size={20} color={image ? '#0a0a0f' : 'rgba(255,255,255,0.3)'} />
            <Text style={[styles.analyzeBtnTxt, !image && styles.analyzeBtnTxtDisabled]}>
              {image ? 'Analyze Fruit' : 'Select an Image First'}
            </Text>
          </Pressable>
        </Animated.View>

        {/* Hint */}
        <View style={styles.hintBox}>
          <MaterialCommunityIcons name="information-outline" size={16} color="#7EE8FA" />
          <Text style={styles.analyzeHint}>
            {image ? 'Image ready. Tap Analyze Fruit to continue.' : 'Select or capture an image to begin.'}
          </Text>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  scroll: { flex: 1 },
  content: { paddingHorizontal: 20 },

  // ===== Header =====
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    marginBottom: 20,
  },
  backBtn: {
    width: 44,
    height: 44,
    borderRadius: 14,
    backgroundColor: 'rgba(255,255,255,0.06)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.06)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerText: { flex: 1 },
  screenTitle: { fontSize: 20, fontWeight: '800', color: '#ffffff' },
  screenSub: { fontSize: 12, color: 'rgba(255,255,255,0.4)', marginTop: 2 },
  headerIcon: {
    width: 44,
    height: 44,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },

  // ===== Hero Card =====
  heroCard: {
    backgroundColor: 'rgba(255,255,255,0.04)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.06)',
    borderRadius: 24,
    padding: 20,
    marginBottom: 18,
    overflow: 'hidden',
  },
  heroTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 14,
  },
  heroBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: 'rgba(126,232,250,0.10)',
    borderWidth: 1,
    borderColor: 'rgba(126,232,250,0.15)',
    borderRadius: 100,
    paddingHorizontal: 12,
    paddingVertical: 5,
  },
  badgeDot: { width: 5, height: 5, borderRadius: 3, backgroundColor: '#7EE8FA' },
  badgeTxt: { fontSize: 10, color: '#7EE8FA', fontWeight: '700', letterSpacing: 0.5 },
  heroIconBox: {
    width: 48,
    height: 48,
    borderRadius: 16,
    backgroundColor: 'rgba(255,107,138,0.12)',
    borderWidth: 1,
    borderColor: 'rgba(255,107,138,0.20)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  heroTitle: { fontSize: 24, fontWeight: '800', color: '#ffffff', lineHeight: 30, marginBottom: 10 },
  heroTitleAccent: { color: '#7EE8FA' },
  heroHelper: { fontSize: 13, color: 'rgba(255,255,255,0.6)', lineHeight: 20, marginBottom: 16 },

  // ===== Quick Actions =====
  quickActionsRow: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 4,
  },
  quickAction: {
    flex: 1,
    padding: 14,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.06)',
    overflow: 'hidden',
    alignItems: 'center',
  },
  quickActionIcon: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: 'rgba(126,232,250,0.08)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  quickActionLabel: {
    fontSize: 14,
    fontWeight: '700',
    color: '#ffffff',
    marginBottom: 2,
  },
  quickActionDesc: {
    fontSize: 10,
    color: 'rgba(255,255,255,0.4)',
  },

  // ===== Viewfinder =====
  viewfinder: {
    width: '100%',
    height: 220,
    backgroundColor: 'rgba(255,255,255,0.02)',
    borderRadius: 20,
    borderWidth: 1,
    borderColor: 'rgba(126,232,250,0.15)',
    overflow: 'hidden',
    marginBottom: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  scanLine: {
    position: 'absolute',
    left: 20,
    right: 20,
    height: 2,
    opacity: 0.8,
  },
  vfImage: { position: 'absolute', width: '100%', height: '100%', resizeMode: 'cover' },
  vfPlaceholder: { alignItems: 'center', gap: 8, paddingHorizontal: 24 },
  vfIconWrap: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: 'rgba(255,255,255,0.03)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.06)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 6,
    overflow: 'hidden',
  },
  vfPlaceholderTitle: { fontSize: 15, fontWeight: '700', color: '#ffffff' },
  vfPlaceholderTxt: { fontSize: 12, color: 'rgba(255,255,255,0.4)', textAlign: 'center', lineHeight: 18 },
  vfLoadingOverlay: {
    position: 'absolute',
    inset: 0,
    backgroundColor: 'rgba(10,10,15,0.92)',
    alignItems: 'center',
    justifyContent: 'center',
  },

  // ===== Progress Bar =====
  progressContainer: {
    width: '80%',
    marginTop: 12,
  },
  progressTrack: {
    height: 4,
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 2,
  },

  // ===== Photo tips =====
  tipsSection: {
    marginBottom: 18,
  },
  tipsSectionLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: 'rgba(255,255,255,0.45)',
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    marginBottom: 10,
  },
  tipsRow: {
    flexDirection: 'row',
    gap: 10,
  },
  tipItem: {
    flex: 1,
    alignItems: 'center',
    gap: 8,
    backgroundColor: 'rgba(255,255,255,0.03)',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.06)',
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
    color: 'rgba(255,255,255,0.75)',
    textAlign: 'center',
    lineHeight: 15,
  },

  // ===== Action Buttons =====
  actionRow: { flexDirection: 'row', gap: 12, marginBottom: 14 },
  actionBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    borderRadius: 16,
    paddingVertical: 15,
    overflow: 'hidden',
  },
  actionBtnSecondary: {
    backgroundColor: 'rgba(255,255,255,0.04)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.06)',
  },
  actionBtnPrimary: {
    overflow: 'hidden',
  },
  actionBtnTxt: { fontSize: 14, fontWeight: '700', color: '#ffffff' },
  actionBtnTxtDark: { fontSize: 14, fontWeight: '800', color: '#0a0a0f' },

  // ===== Analyze Button =====
  analyzeBtn: {
    borderRadius: 18,
    paddingVertical: 17,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.06)',
  },
  analyzeBtnDisabled: { opacity: 0.5 },
  analyzeBtnTxt: { fontSize: 16, fontWeight: '800', color: '#0a0a0f', letterSpacing: 0.3 },
  analyzeBtnTxtDisabled: { color: 'rgba(255,255,255,0.3)' },

  // ===== Hint =====
  hintBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginTop: 16,
    padding: 14,
    borderRadius: 14,
    backgroundColor: 'rgba(126,232,250,0.06)',
    borderWidth: 1,
    borderColor: 'rgba(126,232,250,0.10)',
  },
  analyzeHint: { flex: 1, fontSize: 12, color: 'rgba(255,255,255,0.7)', lineHeight: 18 },

  // ===== Modal =====
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.85)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    width: width * 0.9,
    maxHeight: height * 0.8,
    backgroundColor: '#14141e',
    borderRadius: 24,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.06)',
  },
  modalClose: {
    position: 'absolute',
    top: 12,
    right: 12,
    zIndex: 10,
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(0,0,0,0.5)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  modalImage: {
    width: '100%',
    height: 300,
    resizeMode: 'cover',
  },
  modalActions: {
    flexDirection: 'row',
    gap: 12,
    padding: 16,
  },
  modalBtnSecondary: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 14,
    backgroundColor: 'rgba(255,255,255,0.06)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.06)',
    alignItems: 'center',
  },
  modalBtnPrimary: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 14,
    overflow: 'hidden',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  modalBtnText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#ffffff',
  },
  modalBtnTextDark: {
    fontSize: 14,
    fontWeight: '800',
    color: '#0a0a0f',
  },
});