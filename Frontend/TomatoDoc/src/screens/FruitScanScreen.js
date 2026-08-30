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
import { predictFruitDisease } from '../api/fruitScanApi';
import { UIThemeContext } from '../context/UIThemeContext';
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
  danger: '#ff5c5c',
  dangerDim: 'rgba(255,92,92,0.10)',
  dangerBorder: 'rgba(255,92,92,0.22)',
  success: '#4adf6f',
};

const SAMPLES = [
  { key: 'a', src: require('../../assets/images/tomato5.jpeg') },
  { key: 'b', src: require('../../assets/images/tomato8.jpeg') },
  { key: 'c', src: require('../../assets/images/tomato10.jpeg') },
];

const TAGS = [
  { id: 'all', label: 'All types', icon: 'view-grid-outline' },
  { id: 'disease', label: 'Disease', icon: 'virus' },
  { id: 'healthy', label: 'Healthy', icon: 'check-circle-outline' },
  { id: 'blight', label: 'Blight', icon: 'leaf-off' },
];

const FEATURES = [
  { icon: 'microscope', label: 'AI classifier' },
  { icon: 'medical-bag', label: 'Treatment guide' },
  { icon: 'chart-bar', label: 'Scan history' },
];

function ViewfinderFrame() {
  const size = 22;
  const t = 14;
  const corner = (pos) => ({
    position: 'absolute',
    width: size,
    height: size,
    borderColor: C.accent,
    borderStyle: 'solid',
    ...(pos.top !== undefined && { top: pos.top }),
    ...(pos.bottom !== undefined && { bottom: pos.bottom }),
    ...(pos.left !== undefined && { left: pos.left }),
    ...(pos.right !== undefined && { right: pos.right }),
    borderTopWidth: pos.top !== undefined ? 2.5 : 0,
    borderBottomWidth: pos.bottom !== undefined ? 2.5 : 0,
    borderLeftWidth: pos.left !== undefined ? 2.5 : 0,
    borderRightWidth: pos.right !== undefined ? 2.5 : 0,
    borderTopLeftRadius: pos.top !== undefined && pos.left !== undefined ? 5 : 0,
    borderTopRightRadius: pos.top !== undefined && pos.right !== undefined ? 5 : 0,
    borderBottomLeftRadius: pos.bottom !== undefined && pos.left !== undefined ? 5 : 0,
    borderBottomRightRadius: pos.bottom !== undefined && pos.right !== undefined ? 5 : 0,
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
        Animated.timing(anim, { toValue: 1, duration: 2400, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(anim, { toValue: 0, duration: 2400, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ])
    ).start();
  }, [anim]);

  const translateY = anim.interpolate({ inputRange: [0, 1], outputRange: [0, 146] });

  return (
    <Animated.View
      pointerEvents="none"
      style={[styles.scanLine, { transform: [{ translateY }] }]}
    />
  );
}

function FeatureChip({ icon, label }) {
  return (
    <View style={styles.chip}>
      <MaterialCommunityIcons name={icon} size={12} color={C.accent} />
      <Text style={styles.chipTxt}>{label}</Text>
    </View>
  );
}

function FilterTag({ tag, active, onPress }) {
  return (
    <TouchableOpacity
      style={[styles.filterTag, active && styles.filterTagActive]}
      onPress={() => onPress(tag.id)}
      activeOpacity={0.85}
    >
      <MaterialCommunityIcons
        name={tag.icon}
        size={14}
        color={active ? C.accent : C.muted}
      />
      <Text style={[styles.filterTagTxt, active && styles.filterTagTxtActive]}>
        {tag.label}
      </Text>
    </TouchableOpacity>
  );
}

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
          <MaterialCommunityIcons name="check" size={11} color="#0f0f0f" />
        </View>
      )}
    </TouchableOpacity>
  );
}

export default function FruitScanScreen({ navigation }) {
  const { presentationMode } = useContext(UIThemeContext);
  const insets = useSafeAreaInsets();
  const [image, setImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeSample, setActiveSample] = useState(0);
  const [activeTag, setActiveTag] = useState('all');

  const heroOp = useRef(new Animated.Value(0)).current;
  const heroY = useRef(new Animated.Value(24)).current;
  const btnScale = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(heroOp, { toValue: 1, duration: 420, useNativeDriver: true }),
      Animated.spring(heroY, { toValue: 0, useNativeDriver: true }),
    ]).start();
  }, [heroOp, heroY]);

  const onPressIn = () => Animated.spring(btnScale, { toValue: 0.96, useNativeDriver: true }).start();
  const onPressOut = () => Animated.spring(btnScale, { toValue: 1, useNativeDriver: true }).start();

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
      navigation.navigate('FruitResult', { result: res.data, imageUri: image.uri });
    } catch (error) {
      Alert.alert(
        'Analysis failed',
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
        <View style={styles.header}>
          <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()} activeOpacity={0.8}>
            <MaterialCommunityIcons name="arrow-left" size={20} color={C.text} />
          </TouchableOpacity>
          <View style={styles.headerText}>
            <Text style={styles.screenTitle}>Fruit scanner</Text>
            <Text style={styles.screenSub}>Tomato fruit disease detection</Text>
          </View>
          <View style={styles.headerIcon}>
            <MaterialCommunityIcons name="food-apple" size={18} color={C.danger} />
          </View>
        </View>

        <Animated.View style={[styles.heroCard, { opacity: heroOp, transform: [{ translateY: heroY }] }]}>
          <View style={styles.heroTop}>
            <View style={styles.heroBadge}>
              <View style={styles.badgeDot} />
              <Text style={styles.badgeTxt}>Disease classifier</Text>
            </View>
            <View style={styles.heroIconBox}>
              <MaterialCommunityIcons name="food-apple" size={22} color={C.danger} />
            </View>
          </View>

          <Text style={[styles.heroTitle, presentationMode && { fontSize: 24 }]}>
            Capture fruit for{'\n'}
            <Text style={styles.heroTitleAccent}>instant diagnosis</Text>
          </Text>
          <Text style={styles.heroHelper}>
            Photograph the affected area in natural light. Keep the fruit centred and in focus for best results.
          </Text>

          <View style={styles.chipRow}>
            {FEATURES.map((item) => (
              <FeatureChip key={item.label} icon={item.icon} label={item.label} />
            ))}
          </View>
        </Animated.View>

        <View style={styles.viewfinder}>
          <ViewfinderFrame />
          <ScanLine />

          {image ? (
            <Image source={{ uri: image.uri }} style={styles.vfImage} />
          ) : (
            <View style={styles.vfPlaceholder}>
              <View style={styles.vfIconWrap}>
                <MaterialCommunityIcons name="camera-outline" size={32} color={C.muted} />
              </View>
              <Text style={styles.vfPlaceholderTitle}>No image selected</Text>
              <Text style={styles.vfPlaceholderTxt}>
                Place tomato fruit inside the frame{'\n'}or choose from gallery
              </Text>
            </View>
          )}

          {loading && (
            <View style={styles.vfLoadingOverlay}>
              <LoadingOverlay text="Analyzing tomato fruit..." />
            </View>
          )}
        </View>

        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={styles.tagStrip}
          contentContainerStyle={styles.tagStripContent}
        >
          {TAGS.map((tag) => (
            <FilterTag
              key={tag.id}
              tag={tag}
              active={activeTag === tag.id}
              onPress={setActiveTag}
            />
          ))}
        </ScrollView>

        <Text style={styles.sectionLabel}>Reference samples</Text>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={styles.sampleStrip}
          contentContainerStyle={styles.sampleStripContent}
        >
          {SAMPLES.map((sample, index) => (
            <SampleCard
              key={sample.key}
              src={sample.src}
              active={activeSample === index}
              onPress={() => setActiveSample(index)}
            />
          ))}
        </ScrollView>

        <View style={styles.actionRow}>
          <TouchableOpacity
            style={[styles.actionBtn, styles.actionBtnSecondary]}
            onPress={() => pickImage(false)}
            activeOpacity={0.85}
          >
            <MaterialCommunityIcons name="image-outline" size={18} color={C.text} />
            <Text style={styles.actionBtnTxt}>Gallery</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.actionBtn, styles.actionBtnPrimary]}
            onPress={() => pickImage(true)}
            activeOpacity={0.85}
          >
            <MaterialCommunityIcons name="camera-outline" size={18} color="#0f0f0f" />
            <Text style={styles.actionBtnTxtDark}>Camera</Text>
          </TouchableOpacity>
        </View>

        <Animated.View style={{ transform: [{ scale: btnScale }] }}>
          <Pressable
            style={[styles.analyzeBtn, !image && styles.analyzeBtnDisabled]}
            onPressIn={onPressIn}
            onPressOut={onPressOut}
            onPress={analyze}
            disabled={!image || loading}
          >
            <MaterialCommunityIcons name="microscope" size={18} color="#0f0f0f" />
            <Text style={styles.analyzeBtnTxt}>Analyze fruit</Text>
          </Pressable>
        </Animated.View>

        <View style={styles.hintBox}>
          <MaterialCommunityIcons name="information-outline" size={15} color={C.accent} />
          <Text style={styles.analyzeHint}>
            {image ? 'Image ready. Tap analyze to run diagnosis.' : 'Select or capture an image to begin.'}
          </Text>
        </View>
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
    marginBottom: 18,
  },
  backBtn: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerText: { flex: 1 },
  screenTitle: { fontSize: 18, fontWeight: '800', color: C.text },
  screenSub: { fontSize: 12, color: C.muted, marginTop: 2 },
  headerIcon: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: C.dangerDim,
    borderWidth: 1,
    borderColor: C.dangerBorder,
    alignItems: 'center',
    justifyContent: 'center',
  },

  heroCard: {
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 20,
    padding: 18,
    marginBottom: 16,
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
    backgroundColor: C.accentDim,
    borderWidth: 1,
    borderColor: C.accentBorder,
    borderRadius: 100,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  badgeDot: { width: 5, height: 5, borderRadius: 3, backgroundColor: C.accent },
  badgeTxt: { fontSize: 10, color: C.accent, fontWeight: '700', letterSpacing: 0.4 },
  heroIconBox: {
    width: 44,
    height: 44,
    borderRadius: 14,
    backgroundColor: C.dangerDim,
    borderWidth: 1,
    borderColor: C.dangerBorder,
    alignItems: 'center',
    justifyContent: 'center',
  },
  heroTitle: { fontSize: 22, fontWeight: '800', color: C.text, lineHeight: 28, marginBottom: 8 },
  heroTitleAccent: { color: C.accent },
  heroHelper: { fontSize: 13, color: C.muted, lineHeight: 19, marginBottom: 14 },

  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: C.surface2,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 100,
    paddingHorizontal: 11,
    paddingVertical: 6,
  },
  chipTxt: { fontSize: 11, color: C.text, fontWeight: '600' },

  viewfinder: {
    width: '100%',
    height: 220,
    backgroundColor: C.surface2,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: C.accentBorder,
    overflow: 'hidden',
    marginBottom: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  scanLine: {
    position: 'absolute',
    left: 14,
    right: 14,
    height: 1.5,
    backgroundColor: C.accent,
    opacity: 0.65,
  },
  vfImage: { position: 'absolute', width: '100%', height: '100%', resizeMode: 'cover' },
  vfPlaceholder: { alignItems: 'center', gap: 8, paddingHorizontal: 24 },
  vfIconWrap: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  vfPlaceholderTitle: { fontSize: 14, fontWeight: '700', color: C.text },
  vfPlaceholderTxt: { fontSize: 12, color: C.muted, textAlign: 'center', lineHeight: 18 },
  vfLoadingOverlay: {
    position: 'absolute',
    inset: 0,
    backgroundColor: 'rgba(15,15,15,0.88)',
    alignItems: 'center',
    justifyContent: 'center',
  },

  tagStrip: { marginBottom: 16 },
  tagStripContent: { gap: 8, paddingRight: 4 },
  filterTag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 100,
    borderWidth: 1,
    borderColor: C.border,
    backgroundColor: C.surface,
  },
  filterTagActive: { backgroundColor: C.accentDim, borderColor: C.accentBorder },
  filterTagTxt: { fontSize: 12, color: C.muted, fontWeight: '600' },
  filterTagTxtActive: { color: C.accent },

  sectionLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: C.muted,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    marginBottom: 10,
  },
  sampleStrip: { marginBottom: 18 },
  sampleStripContent: { paddingRight: 4 },
  sampleCard: {
    width: 104,
    height: 76,
    borderRadius: 14,
    overflow: 'hidden',
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    marginRight: 10,
  },
  sampleCardActive: { borderColor: C.accent, borderWidth: 2 },
  sampleImg: { width: '100%', height: '100%', resizeMode: 'cover' },
  sampleCheck: {
    position: 'absolute',
    top: 6,
    right: 6,
    backgroundColor: C.accent,
    borderRadius: 10,
    width: 18,
    height: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },

  actionRow: { flexDirection: 'row', gap: 10, marginBottom: 12 },
  actionBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    borderRadius: 14,
    paddingVertical: 14,
  },
  actionBtnSecondary: {
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
  },
  actionBtnPrimary: { backgroundColor: C.accent },
  actionBtnTxt: { fontSize: 14, fontWeight: '700', color: C.text },
  actionBtnTxtDark: { fontSize: 14, fontWeight: '800', color: '#0f0f0f' },

  analyzeBtn: {
    backgroundColor: C.accent,
    borderRadius: 16,
    paddingVertical: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  analyzeBtnDisabled: { opacity: 0.35 },
  analyzeBtnTxt: { fontSize: 15, fontWeight: '800', color: '#0f0f0f', letterSpacing: 0.2 },

  hintBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    marginTop: 14,
    padding: 12,
    borderRadius: 12,
    backgroundColor: C.accentDim,
    borderWidth: 1,
    borderColor: C.accentBorder,
  },
  analyzeHint: { flex: 1, fontSize: 12, color: C.text, lineHeight: 18 },
});
