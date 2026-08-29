import React, { useContext, useRef, useEffect } from 'react';
import {
  Animated,
  ImageBackground,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { AuthContext } from '../context/AuthContext';
import { UIThemeContext } from '../context/UIThemeContext';

// ── Design Tokens ─────────────────────────────────────────────────────────────
const C = {
  bg:          '#0f0f0f',
  surface:     '#1a1a1a',
  surface2:    '#222222',
  accent:      '#c8f135',
  accentDim:   'rgba(200,241,53,0.10)',
  accentBorder:'rgba(200,241,53,0.22)',
  text:        '#f0f0f0',
  muted:       '#666666',
  border:      'rgba(255,255,255,0.07)',
  danger:      '#ff5c5c',
  warn:        '#f5a623',
};

// ── Animated option card ──────────────────────────────────────────────────────
function OptionCard({ emoji, thumbStyle, title, subtitle, badge, locked, delay = 0, onPress }) {
  const slideY  = useRef(new Animated.Value(20)).current;
  const opacity = useRef(new Animated.Value(0)).current;
  const scale   = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.spring(slideY,  { toValue: 0, useNativeDriver: true, delay }),
      Animated.timing(opacity, { toValue: 1, duration: 350, delay, useNativeDriver: true }),
    ]).start();
  }, []);

  const onPressIn  = () => !locked && Animated.spring(scale, { toValue: 0.97, useNativeDriver: true }).start();
  const onPressOut = () => !locked && Animated.spring(scale, { toValue: 1,    useNativeDriver: true }).start();

  return (
    <Animated.View style={{ opacity, transform: [{ translateY: slideY }, { scale }] }}>
      <Pressable
        style={[styles.optionCard, locked && styles.optionCardLocked]}
        onPressIn={onPressIn}
        onPressOut={onPressOut}
        onPress={!locked ? onPress : undefined}
      >
        <View style={[styles.optionThumb, thumbStyle]}>
          <Text style={styles.optionEmoji}>{emoji}</Text>
        </View>

        <View style={styles.optionBody}>
          <Text style={styles.optionTitle}>{title}</Text>
          <Text style={styles.optionSub} numberOfLines={1}>{subtitle}</Text>
        </View>

        <View style={styles.optionRight}>
          {locked ? (
            <View style={styles.badgeLock}><Text style={styles.badgeLockTxt}>Locked</Text></View>
          ) : (
            <View style={styles.badgeNew}><Text style={styles.badgeNewTxt}>{badge ?? 'NEW'}</Text></View>
          )}
          <Text style={[styles.chevron, !locked && { color: C.accent }]}>›</Text>
        </View>
      </Pressable>
    </Animated.View>
  );
}

// ── Stat card ─────────────────────────────────────────────────────────────────
function StatCard({ num, label, accent = false }) {
  return (
    <View style={[styles.statCard, accent && styles.statCardAccent]}>
      <Text style={[styles.statNum, accent && { color: '#0f0f0f' }]}>{num}</Text>
      <Text style={[styles.statLabel, accent && { color: 'rgba(0,0,0,0.45)' }]}>{label}</Text>
    </View>
  );
}

// ── HomeScreen ────────────────────────────────────────────────────────────────
export default function HomeScreen({ navigation }) {
  const { logout }                                                        = useContext(AuthContext);
  const { isDark, toggleTheme, presentationMode, togglePresentationMode } = useContext(UIThemeContext);

  const heroScale = useRef(new Animated.Value(0.96)).current;
  const heroOp    = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.spring(heroScale, { toValue: 1, useNativeDriver: true }),
      Animated.timing(heroOp,    { toValue: 1, duration: 400, useNativeDriver: true }),
    ]).start();
  }, []);

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" backgroundColor={C.bg} />

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        {/* ── Hero card ── */}
        <Animated.View style={[styles.heroCard, { opacity: heroOp, transform: [{ scale: heroScale }] }]}>
          {/* Decorative blob */}
          <View style={styles.heroBlob} pointerEvents="none" />

          <View style={styles.heroTop}>
            <View style={styles.heroBrand}>
              <View style={styles.brandIcon}><Text style={styles.brandEmoji}>🍅</Text></View>
              <Text style={styles.brandName}>TomatoDoc</Text>
            </View>

            <View style={styles.heroActions}>
              <TouchableOpacity style={styles.pillBtn} onPress={toggleTheme}>
                <Text style={styles.pillBtnTxt}>{isDark ? 'Light' : 'Dark'}</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.pillBtn, presentationMode && styles.pillBtnActive]}
                onPress={togglePresentationMode}
              >
                <Text style={[styles.pillBtnTxt, presentationMode && { color: C.accent }]}>Demo</Text>
              </TouchableOpacity>
              <View style={styles.bellBtn}><Text>🔔</Text></View>
            </View>
          </View>

          <Text style={styles.heroSub}>AI-powered assistant for precision tomato farming</Text>
          <Text style={styles.heroTag}>Smart Scan · Fast Diagnosis · Better Harvest</Text>
        </Animated.View>

        {/* ── Stats row ── */}
        <View style={styles.statsRow}>
          <StatCard num="100" label="Total Scans" />
          <StatCard num="85%" label="Avg Accuracy" accent />
        </View>

        {/* ── Cover card ── */}
        <ImageBackground
          source={require('../../assets/images/tomato1.jpg')}
          imageStyle={styles.coverImg}
          style={styles.coverCard}
        >
          <View style={styles.coverOverlay}>
            <View style={styles.coverBadge}>
              <View style={styles.coverDot} />
              <Text style={styles.coverBadgeTxt}>Pro Intelligence</Text>
            </View>
            <Text style={[styles.coverTitle, presentationMode && { fontSize: 20 }]}>
              Professional Crop Intelligence Panel
            </Text>
            <Text style={styles.coverDesc}>
              Designed for project demos, field trials & precision recommendations.
            </Text>
          </View>
        </ImageBackground>

        {/* ── Section label ── */}
        <Text style={styles.sectionLabel}>Diagnostic Tools</Text>

        {/* ── Option cards ── */}
        <OptionCard
          emoji="📈"
          thumbStyle={styles.thumbOrange}
          title="Price Forecasting"
          subtitle="Market trend analytics"
          locked
          delay={0}
        />
        <OptionCard
          emoji="🍃"
          thumbStyle={styles.thumbGreen}
          title="Nutrient Deficiency"
          subtitle="Leaf scan + fertilizer recommendation"
          delay={60}
          onPress={() => navigation.navigate('NutrientModule', { screen: 'Scan' })}
        />
        <OptionCard
          emoji="🦠"
          thumbStyle={styles.thumbRed}
          title="Disease Monitoring"
          subtitle="Severity & recovery tracking over time"
          delay={120}
          onPress={() => navigation.navigate('MonitoringModule')}
        />
        <OptionCard
          emoji="🍃"
          thumbStyle={styles.thumbGreen}
          title="Disease in Leaf"
          subtitle="Pathology diagnostics"
          delay={150}
          onPress={() => navigation.navigate('DiseaseModule', { screen: 'DiseaseScan' })}
        />
        <OptionCard
          emoji="🍅"
          thumbStyle={styles.thumbAccent}
          title="Disease in Tomato"
          subtitle="Fruit disease detection + treatment"
          delay={180}
          onPress={() => navigation.navigate('FruitModule', { screen: 'FruitScan' })}
        />

        {/* ── Logout ── */}
        <TouchableOpacity style={styles.logoutBtn} onPress={logout}>
          <Text style={styles.logoutTxt}>Logout</Text>
        </TouchableOpacity>
      </ScrollView>
    </View>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  root:    { flex: 1, backgroundColor: C.bg },
  scroll:  { flex: 1 },
  content: { padding: 18, paddingBottom: 130 },

  // Hero
  heroCard: {
    backgroundColor: C.surface,
    borderRadius: 22,
    borderWidth: 1,
    borderColor: C.border,
    padding: 16,
    marginBottom: 14,
    overflow: 'hidden',
  },
  heroBlob: {
    position: 'absolute',
    top: -50, right: -50,
    width: 150, height: 150,
    borderRadius: 75,
    backgroundColor: C.accent,
    opacity: 0.05,
  },
  heroTop:    { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 },
  heroBrand:  { flexDirection: 'row', alignItems: 'center', gap: 8 },
  brandIcon:  { width: 36, height: 36, backgroundColor: C.accent, borderRadius: 10, alignItems: 'center', justifyContent: 'center' },
  brandEmoji: { fontSize: 18 },
  brandName:  { fontSize: 22, fontWeight: '800', color: C.text },
  heroActions:{ flexDirection: 'row', alignItems: 'center', gap: 6 },

  pillBtn:       { backgroundColor: C.surface2, borderWidth: 1, borderColor: C.border, borderRadius: 100, paddingHorizontal: 11, paddingVertical: 5 },
  pillBtnActive: { backgroundColor: C.accentDim, borderColor: C.accentBorder },
  pillBtnTxt:    { fontSize: 11, color: C.muted, fontWeight: '600' },
  bellBtn:       { width: 30, height: 30, backgroundColor: C.surface2, borderWidth: 1, borderColor: C.border, borderRadius: 15, alignItems: 'center', justifyContent: 'center' },

  heroSub: { fontSize: 12.5, color: C.muted, lineHeight: 19, marginBottom: 4 },
  heroTag: { fontSize: 12, fontWeight: '700', color: C.accent },

  // Stats
  statsRow: { flexDirection: 'row', gap: 10, marginBottom: 14 },
  statCard: {
    flex: 1,
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 16,
    padding: 14,
  },
  statCardAccent: { backgroundColor: C.accent, borderColor: C.accent },
  statNum:        { fontSize: 28, fontWeight: '800', color: C.accent, lineHeight: 32 },
  statLabel:      { fontSize: 10, color: C.muted, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.5, marginTop: 4 },

  // Cover card
  coverCard:    { borderRadius: 20, overflow: 'hidden', marginBottom: 14, minHeight: 148 },
  coverImg:     { borderRadius: 20 },
  coverOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.52)', padding: 16, justifyContent: 'flex-end', minHeight: 148 },
  coverBadge:   { flexDirection: 'row', alignItems: 'center', gap: 5, alignSelf: 'flex-start',
                  backgroundColor: 'rgba(200,241,53,0.15)', borderWidth: 1, borderColor: C.accentBorder,
                  borderRadius: 100, paddingHorizontal: 10, paddingVertical: 3, marginBottom: 8 },
  coverDot:     { width: 5, height: 5, borderRadius: 3, backgroundColor: C.accent },
  coverBadgeTxt:{ fontSize: 10, color: C.accent, fontWeight: '700', letterSpacing: 0.4 },
  coverTitle:   { fontSize: 17, fontWeight: '800', color: '#fff', marginBottom: 4 },
  coverDesc:    { fontSize: 11, color: 'rgba(255,255,255,0.55)', lineHeight: 15 },

  // Section
  sectionLabel: { fontSize: 10, fontWeight: '700', color: C.muted, textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 10, marginLeft: 2 },

  // Option card
  optionCard:       {
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 18,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    padding: 14,
    marginBottom: 10,
  },
  optionCardLocked: { opacity: 0.5 },
  optionThumb:      { width: 52, height: 52, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
  optionEmoji:      { fontSize: 26 },

  thumbGreen:  { backgroundColor: C.accentDim,              borderWidth: 1, borderColor: C.accentBorder },
  thumbOrange: { backgroundColor: 'rgba(245,166,35,0.12)',   borderWidth: 1, borderColor: 'rgba(245,166,35,0.22)' },
  thumbRed:    { backgroundColor: 'rgba(255,92,92,0.10)',    borderWidth: 1, borderColor: 'rgba(255,92,92,0.18)' },
  thumbAccent: { backgroundColor: 'rgba(200,241,53,0.08)',   borderWidth: 1, borderColor: C.accentBorder },

  optionBody:  { flex: 1, minWidth: 0 },
  optionTitle: { fontSize: 14, fontWeight: '800', color: C.text, marginBottom: 2 },
  optionSub:   { fontSize: 11, color: C.muted },
  optionRight: { alignItems: 'flex-end', gap: 5 },

  badgeNew:    { backgroundColor: C.accent, borderRadius: 100, paddingHorizontal: 7, paddingVertical: 2 },
  badgeNewTxt: { fontSize: 9, fontWeight: '800', color: '#0f0f0f', letterSpacing: 0.3 },
  badgeLock:   { backgroundColor: C.surface2, borderWidth: 1, borderColor: C.border, borderRadius: 100, paddingHorizontal: 7, paddingVertical: 2 },
  badgeLockTxt:{ fontSize: 9, fontWeight: '700', color: C.muted },
  chevron:     { fontSize: 18, color: C.muted },

  // Logout
  logoutBtn: {
    borderWidth: 1.5,
    borderColor: C.border,
    borderRadius: 14,
    padding: 14,
    alignItems: 'center',
    marginTop: 8,
    marginBottom: 8,
  },
  logoutTxt: { fontSize: 13, fontWeight: '600', color: C.muted },
});