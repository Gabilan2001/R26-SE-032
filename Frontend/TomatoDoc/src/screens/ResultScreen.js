import React, { useContext, useEffect, useRef, useState } from 'react';
import {
  Alert,
  Animated,
  ActivityIndicator,
  Easing,
  Image,
  Modal,
  Pressable,
  ScrollView,
  Share,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import TreatmentAdviceCard from '../components/TreatmentAdviceCard';
import { saveHistory } from '../api/historyApi';
import { exportScanReport } from '../utils/reportExport';
import { AuthContext } from '../context/AuthContext';
import { computeSeverity } from '../utils/severity';

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
  warn: '#f5a623',
  warnDim: 'rgba(245,166,35,0.10)',
  warnBorder: 'rgba(245,166,35,0.22)',
  success: '#4adf6f',
  successDim: 'rgba(74,223,111,0.10)',
  successBorder: 'rgba(74,223,111,0.22)',
  leaf: '#4adf6f',
  leafDim: 'rgba(74,223,111,0.10)',
};

function formatLabel(value) {
  if (!value) return 'Unknown';
  return String(value).replace(/_/g, ' ');
}

function normalizeConfidence(value) {
  const n = Number(value || 0);
  if (n <= 1) return Math.round(n * 100);
  return Math.min(100, Math.round(n));
}

const isHealthy = (cls) => cls === 'Healthy';

function ShareModal({ visible, onClose, onShare, onExport }) {
  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <Pressable style={styles.modalOverlay} onPress={onClose}>
        <Pressable onPress={(e) => e.stopPropagation()}>
          <View style={styles.modalContent}>
            <LinearGradient
              colors={['rgba(255,255,255,0.03)', 'rgba(255,255,255,0.01)']}
              style={StyleSheet.absoluteFill}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
            />
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Share Report</Text>
              <TouchableOpacity onPress={onClose}>
                <MaterialCommunityIcons name="close" size={24} color={C.muted} />
              </TouchableOpacity>
            </View>

            <TouchableOpacity style={styles.modalOption} onPress={onShare}>
              <View style={styles.modalOptionIcon}>
                <MaterialCommunityIcons name="share-variant" size={24} color={C.accent} />
              </View>
              <View style={styles.modalOptionContent}>
                <Text style={styles.modalOptionLabel}>Share</Text>
                <Text style={styles.modalOptionDesc}>Share via messaging or social</Text>
              </View>
            </TouchableOpacity>

            <TouchableOpacity style={styles.modalOption} onPress={onExport}>
              <View style={[styles.modalOptionIcon, { backgroundColor: C.warnDim }]}>
                <MaterialCommunityIcons name="file-export" size={24} color={C.warn} />
              </View>
              <View style={styles.modalOptionContent}>
                <Text style={styles.modalOptionLabel}>Export .txt</Text>
                <Text style={styles.modalOptionDesc}>Save as text file</Text>
              </View>
            </TouchableOpacity>
          </View>
        </Pressable>
      </Pressable>
    </Modal>
  );
}

function RecItem({ text }) {
  return (
    <View style={styles.recItem}>
      <MaterialCommunityIcons name="check-circle-outline" size={16} color={C.accent} />
      <Text style={styles.recTxt}>{text}</Text>
    </View>
  );
}

export default function ResultScreen({ route, navigation }) {
  const { token } = useContext(AuthContext);
  const insets = useSafeAreaInsets();
  const { result, imageUri } = route.params;
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);

  const severity = computeSeverity(result, 'nutrient');
  const healthy = isHealthy(result.class);
  const confidencePct = normalizeConfidence(result.confidence);
  const displayName = formatLabel(result.class);
  const statusColor = healthy ? C.success : C.warn;

  const fadeIn = useRef(new Animated.Value(0)).current;
  const slideUp = useRef(new Animated.Value(30)).current;
  const cardScale = useRef(new Animated.Value(0.95)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeIn, { toValue: 1, duration: 500, useNativeDriver: true }),
      Animated.spring(slideUp, { toValue: 0, useNativeDriver: true }),
      Animated.spring(cardScale, { toValue: 1, useNativeDriver: true }),
    ]).start();

    if (!healthy) {
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.08,
            duration: 1000,
            easing: Easing.inOut(Easing.ease),
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 1000,
            easing: Easing.inOut(Easing.ease),
            useNativeDriver: true,
          }),
        ])
      ).start();
    }
  }, [fadeIn, slideUp, cardScale, pulseAnim, healthy]);

  const onSave = async () => {
    if (!token) {
      Alert.alert('Login required', 'Please log in to save scan results to your history.');
      return;
    }
    if (saving || saved) return;

    setSaving(true);
    try {
      await saveHistory(token, {
        class: result.class,
        confidence: confidencePct,
        description: result.description || '',
        symptoms: result.symptoms || '',
        solution: result.solution || '',
        fertilizer: result.fertilizer || '',
        image_uri: imageUri || null,
      });
      setSaved(true);
      Alert.alert('Saved', 'This scan was added to your nutrient history.');
    } catch (e) {
      Alert.alert(
        'Save failed',
        e?.response?.data?.message ||
          e?.response?.data?.msg ||
          e?.message ||
          'Could not save to history.'
      );
    } finally {
      setSaving(false);
    }
  };

  const onExport = async () => {
    try {
      const fileUri = await exportScanReport({
        moduleName: 'Nutrient Deficiency',
        result: { ...result, confidence: confidencePct },
        imageUri,
        severity,
      });
      Alert.alert('Report Exported', `Saved at:\n${fileUri}`);
      setShowShareModal(false);
    } catch (e) {
      Alert.alert('Export failed', e?.message || 'Could not export report.');
    }
  };

  const onShare = async () => {
    try {
      const shareMessage =
        `Nutrient Deficiency Report\n\n` +
        `Result: ${displayName}\n` +
        `Confidence: ${confidencePct}%\n` +
        `Status: ${healthy ? 'Healthy' : 'Deficiency Detected'}\n\n` +
        `Analyzed by TomatoDoc Leaf Scanner`;

      await Share.share({
        message: shareMessage,
        title: 'Nutrient Scan Report',
      });
      setShowShareModal(false);
    } catch (e) {
      Alert.alert('Share failed', e?.message || 'Could not share report.');
    }
  };

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" backgroundColor={C.bg} />

      <ShareModal
        visible={showShareModal}
        onClose={() => setShowShareModal(false)}
        onShare={onShare}
        onExport={onExport}
      />

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={[
          styles.content,
          { paddingTop: insets.top + 16, paddingBottom: insets.bottom + 60 },
        ]}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <TouchableOpacity
            style={styles.backBtn}
            onPress={() => navigation.goBack()}
            activeOpacity={0.7}
          >
            <MaterialCommunityIcons name="arrow-left" size={22} color={C.text} />
          </TouchableOpacity>
          <View style={styles.headerText}>
            <Text style={styles.screenTitle}>Analysis Result</Text>
            <Text style={styles.screenSub}>Nutrient Deficiency Report</Text>
          </View>
          <TouchableOpacity
            style={styles.shareBtn}
            onPress={() => setShowShareModal(true)}
            activeOpacity={0.7}
          >
            <MaterialCommunityIcons name="share-variant" size={20} color={C.accent} />
          </TouchableOpacity>
        </View>

        <Animated.View style={{ opacity: fadeIn, transform: [{ translateY: slideUp }] }}>
          <View style={[styles.statusAlert, healthy ? styles.statusAlertHealthy : styles.statusAlertWarn]}>
            <LinearGradient
              colors={
                healthy
                  ? ['rgba(74,223,111,0.08)', 'rgba(74,223,111,0.02)']
                  : ['rgba(245,166,35,0.08)', 'rgba(245,166,35,0.02)']
              }
              style={StyleSheet.absoluteFill}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
            />
            <View style={styles.statusAlertIcon}>
              <MaterialCommunityIcons
                name={healthy ? 'check-circle' : 'leaf-off'}
                size={24}
                color={statusColor}
              />
            </View>
            <View style={styles.statusAlertContent}>
              <Text style={[styles.statusAlertTitle, { color: statusColor }]}>
                {healthy ? 'Healthy Leaf Detected' : 'Deficiency Detected'}
              </Text>
              <Text style={styles.statusAlertDesc}>
                {healthy
                  ? 'No deficiency found. Continue regular monitoring.'
                  : 'Review the treatment plan below and adjust fertilizer as needed.'}
              </Text>
            </View>
            {!healthy && (
              <Animated.View style={[styles.pulseBadge, { transform: [{ scale: pulseAnim }] }]}>
                <View style={styles.pulseDot} />
              </Animated.View>
            )}
          </View>

          <Animated.View style={[styles.heroCard, { transform: [{ scale: cardScale }] }]}>
            <LinearGradient
              colors={['rgba(255,255,255,0.04)', 'rgba(255,255,255,0.01)']}
              style={StyleSheet.absoluteFill}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
            />
            <View style={styles.heroImageWrap}>
              {imageUri ? (
                <Image source={{ uri: imageUri }} style={styles.heroImage} />
              ) : (
                <View style={[styles.heroImage, styles.heroPlaceholder]}>
                  <MaterialCommunityIcons name="leaf" size={60} color="rgba(255,255,255,0.05)" />
                </View>
              )}
              <LinearGradient
                colors={['transparent', 'rgba(15,15,15,0.9)']}
                style={styles.imageGradient}
                start={{ x: 0, y: 0.3 }}
                end={{ x: 0, y: 1 }}
              />

              <View style={[styles.statusChip, healthy && styles.statusChipHealthy]}>
                <View style={[styles.statusChipDot, { backgroundColor: statusColor }]} />
                <Text style={[styles.statusChipText, { color: statusColor }]}>
                  {healthy ? 'Healthy' : 'Deficiency'}
                </Text>
              </View>

              <View style={styles.heroOverlay}>
                <Text style={styles.heroName}>{displayName}</Text>
                <Text style={styles.heroConfidence}>{confidencePct}% confidence</Text>
              </View>
            </View>
          </Animated.View>

          <TreatmentAdviceCard predictedClass={result.class} variant="dark" />

          {result.recommendations?.length > 0 && (
            <View style={styles.recsCard}>
              <Text style={styles.recsTitle}>Quick recommendations</Text>
              {result.recommendations.map((r, i) => (
                <RecItem key={i} text={r} />
              ))}
            </View>
          )}

          {!healthy && (
            <View style={styles.warningBox}>
              <MaterialCommunityIcons name="alert-outline" size={20} color={C.warn} />
              <View style={styles.warningContent}>
                <Text style={styles.warningTitle}>Action recommended</Text>
                <Text style={styles.warningText}>
                  Apply the suggested fertilizer plan and re-scan in 1–2 weeks to track improvement.
                </Text>
              </View>
            </View>
          )}

          <View style={styles.actionRow}>
            <TouchableOpacity
              style={[styles.btnSecondary, (saved || saving) && styles.btnSecondarySaved]}
              onPress={onSave}
              disabled={saved || saving}
              activeOpacity={0.7}
            >
              {saving ? (
                <ActivityIndicator size="small" color={C.text} />
              ) : (
                <MaterialCommunityIcons
                  name={saved ? 'check' : 'content-save-outline'}
                  size={18}
                  color={saved ? C.muted : C.text}
                />
              )}
              <Text style={[styles.btnSecondaryTxt, saved && { color: C.muted }]}>
                {saved ? 'Saved' : saving ? 'Saving…' : 'Save Result'}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.btnSecondary}
              onPress={() => setShowShareModal(true)}
              activeOpacity={0.7}
            >
              <MaterialCommunityIcons name="share-outline" size={18} color={C.text} />
              <Text style={styles.btnSecondaryTxt}>Share</Text>
            </TouchableOpacity>
          </View>

          <TouchableOpacity
            style={styles.footerBtn}
            onPress={() => navigation.navigate('NutrientModule', { screen: 'Scan' })}
            activeOpacity={0.7}
          >
            <MaterialCommunityIcons name="camera-retake-outline" size={16} color={C.accent} />
            <Text style={styles.footerBtnTxt}>Scan Another Leaf</Text>
          </TouchableOpacity>
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
    gap: 14,
    marginBottom: 20,
  },
  backBtn: {
    width: 44,
    height: 44,
    borderRadius: 14,
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  shareBtn: {
    width: 44,
    height: 44,
    borderRadius: 14,
    backgroundColor: C.accentDim,
    borderWidth: 1,
    borderColor: C.accentBorder,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerText: { flex: 1 },
  screenTitle: { fontSize: 20, fontWeight: '800', color: C.text },
  screenSub: { fontSize: 12, color: C.muted, marginTop: 2 },

  statusAlert: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    borderRadius: 16,
    borderWidth: 1,
    padding: 14,
    marginBottom: 16,
    overflow: 'hidden',
  },
  statusAlertHealthy: {
    backgroundColor: C.successDim,
    borderColor: C.successBorder,
  },
  statusAlertWarn: {
    backgroundColor: C.warnDim,
    borderColor: C.warnBorder,
  },
  statusAlertIcon: {
    width: 40,
    height: 40,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  statusAlertContent: { flex: 1 },
  statusAlertTitle: { fontSize: 14, fontWeight: '700', marginBottom: 2 },
  statusAlertDesc: { fontSize: 12, color: C.muted, lineHeight: 18 },
  pulseBadge: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: C.warnDim,
    alignItems: 'center',
    justifyContent: 'center',
  },
  pulseDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: C.warn,
  },

  heroCard: {
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 20,
    overflow: 'hidden',
    marginBottom: 16,
  },
  heroImageWrap: {
    width: '100%',
    height: 220,
    backgroundColor: C.surface2,
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
  },
  heroImage: {
    position: 'absolute',
    width: '100%',
    height: '100%',
    resizeMode: 'cover',
  },
  heroPlaceholder: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  imageGradient: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    height: 120,
  },
  statusChip: {
    position: 'absolute',
    top: 12,
    left: 12,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: 'rgba(15,15,15,0.85)',
    borderWidth: 1,
    borderColor: C.warnBorder,
    borderRadius: 100,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  statusChipHealthy: {
    borderColor: C.successBorder,
  },
  statusChipDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  statusChipText: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.3,
  },
  heroOverlay: {
    position: 'absolute',
    left: 16,
    right: 16,
    bottom: 16,
  },
  heroName: {
    fontSize: 22,
    fontWeight: '800',
    color: C.text,
    marginBottom: 4,
  },
  heroConfidence: {
    fontSize: 13,
    fontWeight: '600',
    color: C.accent,
  },

  recsCard: {
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 14,
    padding: 14,
    marginTop: 16,
    gap: 8,
  },
  recsTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: C.muted,
    textTransform: 'uppercase',
    letterSpacing: 0.6,
    marginBottom: 4,
  },
  recItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
  },
  recTxt: {
    flex: 1,
    fontSize: 13,
    color: C.text,
    lineHeight: 19,
    opacity: 0.85,
  },

  warningBox: {
    flexDirection: 'row',
    gap: 12,
    backgroundColor: C.warnDim,
    borderWidth: 1,
    borderColor: C.warnBorder,
    borderRadius: 14,
    padding: 14,
    marginTop: 16,
    marginBottom: 4,
  },
  warningContent: { flex: 1, gap: 2 },
  warningTitle: { fontSize: 14, fontWeight: '700', color: C.warn },
  warningText: { fontSize: 12, color: C.muted, lineHeight: 18 },

  actionRow: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 16,
    marginBottom: 10,
  },
  btnSecondary: {
    flex: 1,
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 14,
    paddingVertical: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 7,
  },
  btnSecondarySaved: { opacity: 0.4 },
  btnSecondaryTxt: { fontSize: 13, fontWeight: '600', color: C.text },

  footerBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 16,
  },
  footerBtnTxt: { fontSize: 13, fontWeight: '600', color: C.accent },

  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: C.surface,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 20,
    paddingBottom: 40,
    borderWidth: 1,
    borderColor: C.border,
    overflow: 'hidden',
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  modalTitle: { fontSize: 18, fontWeight: '800', color: C.text },
  modalOption: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: C.border,
  },
  modalOptionIcon: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: C.accentDim,
    alignItems: 'center',
    justifyContent: 'center',
  },
  modalOptionContent: { flex: 1 },
  modalOptionLabel: { fontSize: 15, fontWeight: '700', color: C.text },
  modalOptionDesc: { fontSize: 12, color: C.muted, marginTop: 2 },
});
