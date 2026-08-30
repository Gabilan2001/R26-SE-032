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
import { saveFruitHistory } from '../api/fruitHistoryApi';
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
  tomato: '#ff5c5c',
  tomatoDim: 'rgba(255,92,92,0.10)',
  tomatoBorder: 'rgba(255,92,92,0.22)',
  warn: '#f5a623',
  warnDim: 'rgba(245,166,35,0.10)',
  success: '#4adf6f',
  successDim: 'rgba(74,223,111,0.10)',
  successBorder: 'rgba(74,223,111,0.22)',
};

const SEVERITY_MAP = {
  low: { label: 'Low', color: C.success, dim: C.successDim, pct: '28%', icon: 'leaf' },
  medium: { label: 'Moderate', color: C.warn, dim: C.warnDim, pct: '62%', icon: 'alert' },
  high: { label: 'High', color: C.tomato, dim: C.tomatoDim, pct: '90%', icon: 'alert-circle' },
};

const isHealthy = (cls) => cls === 'Healthy_Tomato' || cls === 'Healthy';

function formatLabel(value) {
  if (!value) return 'Unknown';
  return String(value).replace(/_/g, ' ');
}

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
              <View style={[styles.modalOptionIcon, { backgroundColor: C.tomatoDim }]}>
                <MaterialCommunityIcons name="file-export" size={24} color={C.tomato} />
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

export default function FruitResultScreen({ route, navigation }) {
  const { token } = useContext(AuthContext);
  const insets = useSafeAreaInsets();
  const { result, imageUri } = route.params;
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);

  const severity = computeSeverity(result, 'fruit');
  const healthy = isHealthy(result.class);
  const sevMeta = SEVERITY_MAP[severity] ?? SEVERITY_MAP.medium;
  const confidencePct = Math.round(Number(result.confidence || 0));
  const displayName = formatLabel(result.class);
  const statusColor = healthy ? C.success : C.tomato;

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
      await saveFruitHistory(token, {
        class: result.class,
        confidence: result.confidence,
        warning: result.warning || '',
        description: result.description || '',
        symptoms: result.symptoms || '',
        solution: result.solution || '',
        treatment: result.treatment || '',
        image_uri: imageUri || null,
      });
      setSaved(true);
      Alert.alert('Saved', 'This scan was added to your fruit disease history.');
    } catch (e) {
      const message =
        e?.response?.data?.message ||
        e?.response?.data?.msg ||
        e?.response?.data?.error ||
        e?.message ||
        'Could not save to history.';
      Alert.alert('Save failed', message);
    } finally {
      setSaving(false);
    }
  };

  const onExport = async () => {
    try {
      const fileUri = await exportScanReport({
        moduleName: 'Fruit Disease',
        result,
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
        `Fruit Disease Report\n\n` +
        `Disease: ${displayName}\n` +
        `Confidence: ${confidencePct}%\n` +
        `Severity: ${sevMeta.label}\n` +
        `Status: ${healthy ? 'Healthy' : 'Disease Detected'}\n\n` +
        `Analyzed by TomatoDoc Fruit Scanner`;

      await Share.share({
        message: shareMessage,
        title: 'Fruit Disease Report',
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
            <Text style={styles.screenSub}>Fruit Disease Report</Text>
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
          <View style={[styles.statusAlert, healthy ? styles.statusAlertHealthy : styles.statusAlertDisease]}>
            <LinearGradient
              colors={
                healthy
                  ? ['rgba(74,223,111,0.08)', 'rgba(74,223,111,0.02)']
                  : ['rgba(255,92,92,0.08)', 'rgba(255,92,92,0.02)']
              }
              style={StyleSheet.absoluteFill}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
            />
            <View style={styles.statusAlertIcon}>
              <MaterialCommunityIcons
                name={healthy ? 'check-circle' : 'alert-circle'}
                size={24}
                color={statusColor}
              />
            </View>
            <View style={styles.statusAlertContent}>
              <Text style={[styles.statusAlertTitle, { color: statusColor }]}>
                {healthy ? 'Healthy Fruit Detected' : 'Disease Detected'}
              </Text>
              <Text style={styles.statusAlertDesc}>
                {healthy
                  ? 'No treatment needed. Continue regular monitoring.'
                  : 'Immediate action recommended. Review treatment guide below.'}
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
                  <MaterialCommunityIcons name="food-apple" size={60} color="rgba(255,255,255,0.05)" />
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
                  {healthy ? 'Healthy' : 'Disease'}
                </Text>
              </View>

              <View style={styles.heroOverlay}>
                <Text style={styles.heroName}>{displayName}</Text>
              </View>
            </View>
          </Animated.View>

          <TreatmentAdviceCard predictedClass={result.class} variant="dark" />

          {!healthy && (
            <View style={styles.warningBox}>
              <MaterialCommunityIcons name="alert" size={20} color={C.tomato} />
              <View style={styles.warningContent}>
                <Text style={styles.warningTitle}>Action Required</Text>
                <Text style={styles.warningText}>
                  Treat affected fruit promptly to prevent spread to healthy plants.
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
            onPress={() => navigation.navigate('FruitModule', { screen: 'FruitScan' })}
            activeOpacity={0.7}
          >
            <MaterialCommunityIcons name="camera-retake-outline" size={16} color={C.accent} />
            <Text style={styles.footerBtnTxt}>Scan Another Fruit</Text>
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
  statusAlertDisease: {
    backgroundColor: C.tomatoDim,
    borderColor: C.tomatoBorder,
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
    backgroundColor: C.tomatoDim,
    alignItems: 'center',
    justifyContent: 'center',
  },
  pulseDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: C.tomato,
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
    borderColor: C.tomatoBorder,
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
  },

  warningBox: {
    flexDirection: 'row',
    gap: 12,
    backgroundColor: C.tomatoDim,
    borderWidth: 1,
    borderColor: C.tomatoBorder,
    borderRadius: 14,
    padding: 14,
    marginTop: 16,
    marginBottom: 16,
  },
  warningContent: {
    flex: 1,
    gap: 2,
  },
  warningTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: C.tomato,
  },
  warningText: {
    fontSize: 12,
    color: C.muted,
    lineHeight: 18,
  },

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
  btnSecondarySaved: {
    opacity: 0.4,
  },
  btnSecondaryTxt: {
    fontSize: 13,
    fontWeight: '600',
    color: C.text,
  },

  footerBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 16,
  },
  footerBtnTxt: {
    fontSize: 13,
    fontWeight: '600',
    color: C.accent,
  },

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
  modalTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: C.text,
  },
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
  modalOptionContent: {
    flex: 1,
  },
  modalOptionLabel: {
    fontSize: 15,
    fontWeight: '700',
    color: C.text,
  },
  modalOptionDesc: {
    fontSize: 12,
    color: C.muted,
    marginTop: 2,
  },
});
