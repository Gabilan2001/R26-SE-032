import React, { useContext, useMemo } from 'react';
import {
  ImageBackground,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { AuthContext } from '../context/AuthContext';
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
  warn: '#f5a623',
  success: '#4adf6f',
};

function getGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 17) return 'Good afternoon';
  return 'Good evening';
}

function ModuleCard({ icon, iconColor, iconBg, title, subtitle, onPress, locked, badge }) {
  return (
    <TouchableOpacity
      style={[styles.moduleCard, locked && styles.moduleCardLocked]}
      onPress={locked ? undefined : onPress}
      activeOpacity={locked ? 1 : 0.75}
    >
      <View style={[styles.moduleIcon, { backgroundColor: iconBg }]}>
        <MaterialCommunityIcons name={icon} size={22} color={iconColor} />
      </View>
      <View style={styles.moduleBody}>
        <Text style={[styles.moduleTitle, locked && styles.moduleTitleLocked]}>{title}</Text>
        <Text style={styles.moduleSub} numberOfLines={2}>{subtitle}</Text>
        {!locked && <Text style={styles.moduleAction}>Open module</Text>}
      </View>
      <View style={styles.moduleRight}>
        {locked ? (
          <View style={styles.soonBadge}>
            <Text style={styles.soonText}>Soon</Text>
          </View>
        ) : (
          <>
            {badge ? (
              <View style={styles.readyBadge}>
                <View style={styles.readyDot} />
                <Text style={styles.readyText}>{badge}</Text>
              </View>
            ) : null}
            <View style={styles.chevronWrap}>
              <MaterialCommunityIcons name="chevron-right" size={18} color={C.accent} />
            </View>
          </>
        )}
      </View>
    </TouchableOpacity>
  );
}

export default function HomeScreen({ navigation }) {
  const { user, logout } = useContext(AuthContext);
  const insets = useSafeAreaInsets();
  const greeting = useMemo(() => getGreeting(), []);
  const displayName = user?.name?.trim() || 'Farmer';
  const initial = displayName.charAt(0).toUpperCase();

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" backgroundColor={C.bg} />

      <ScrollView
        contentContainerStyle={[
          styles.scroll,
          { paddingTop: insets.top + 12, paddingBottom: 130 },
        ]}
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.headerLeft}>
            <TouchableOpacity
              style={styles.avatar}
              onPress={() => navigation.navigate('User')}
              activeOpacity={0.8}
            >
              <Text style={styles.avatarText}>{initial}</Text>
            </TouchableOpacity>
            <View>
              <Text style={styles.greeting}>{greeting}</Text>
              <Text style={styles.userName} numberOfLines={1}>{displayName}</Text>
            </View>
          </View>
          <View style={styles.headerActions}>
            <TouchableOpacity style={styles.iconBtn} onPress={logout} activeOpacity={0.7}>
              <MaterialCommunityIcons name="logout" size={18} color={C.accent} />
            </TouchableOpacity>
          </View>
        </View>

        {/* Brand strip */}
        <View style={styles.brandCard}>
          <View style={styles.brandRow}>
            <View style={styles.logoBox}>
              <MaterialCommunityIcons name="sprout" size={22} color="#0f0f0f" />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.brandName}>TomatoDoc</Text>
              <Text style={styles.brandSub}>Precision tomato farming assistant</Text>
            </View>
          </View>
          <Text style={styles.brandTag}>Scan · Diagnose · Treat · Track</Text>
        </View>

        {/* Banner */}
        <ImageBackground
          source={require('../../assets/images/tomato1.jpg')}
          imageStyle={styles.bannerImage}
          style={styles.banner}
        >
          <View style={styles.bannerOverlay}>
            <View style={styles.bannerBadge}>
              <MaterialCommunityIcons name="shield-check-outline" size={12} color={C.accent} />
              <Text style={styles.bannerBadgeText}>Crop intelligence</Text>
            </View>
            <Text style={styles.bannerTitle}>
              Field diagnostics and treatment guidance
            </Text>
            <Text style={styles.bannerDesc}>
              Built for farmers, field trials, and data-driven crop decisions.
            </Text>
          </View>
        </ImageBackground>

        {/* Modules */}
        <Text style={styles.sectionTitle}>Diagnostic tools</Text>
        <Text style={styles.sectionHint}>Select a module to get started</Text>

        <ModuleCard
          icon="chart-line"
          iconColor={C.muted}
          iconBg={C.surface2}
          title="Price forecasting"
          subtitle="Market trend analytics and selling recommendations"
          locked
        />
        <ModuleCard
          icon="leaf"
          iconColor={C.accent}
          iconBg={C.accentDim}
          title="Nutrient deficiency"
          subtitle="Leaf scan with fertilizer and treatment recommendations"
          badge="Ready"
          onPress={() => navigation.navigate('NutrientModule', { screen: 'Scan' })}
        />
        <ModuleCard
          icon="chart-timeline-variant"
          iconColor={C.success}
          iconBg="rgba(74,223,111,0.10)"
          title="Disease monitoring"
          subtitle="Track severity and recovery over multiple observations"
          badge="Ready"
          onPress={() => navigation.navigate('MonitoringModule')}
        />
        <ModuleCard
          icon="virus"
          iconColor={C.accent}
          iconBg={C.accentDim}
          title="Disease in leaf"
          subtitle="Pathology diagnostics and leaf disease scan"
          badge="Ready"
          onPress={() => navigation.navigate('DiseaseModule', { screen: 'DiseaseScan' })}
        />
        <ModuleCard
          icon="food-apple"
          iconColor={C.danger}
          iconBg="rgba(255,92,92,0.10)"
          title="Fruit disease detection"
          subtitle="Identify fruit diseases and view treatment guidance"
          badge="Ready"
          onPress={() => navigation.navigate('FruitModule', { screen: 'FruitScan' })}
        />

        <View style={styles.tipBox}>
          <MaterialCommunityIcons name="information-outline" size={16} color={C.accent} />
          <Text style={styles.tipText}>
            For best results, capture photos in natural daylight with the subject filling most of the frame.
          </Text>
        </View>

        <TouchableOpacity style={styles.logoutBtn} onPress={logout} activeOpacity={0.85}>
          <MaterialCommunityIcons name="logout" size={18} color={C.muted} />
          <Text style={styles.logoutText}>Log out</Text>
        </TouchableOpacity>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: C.bg },
  scroll: { paddingHorizontal: 18 },

  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 18,
  },
  headerLeft: { flexDirection: 'row', alignItems: 'center', gap: 12, flex: 1 },
  avatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: C.accent,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: { fontSize: 18, fontWeight: '800', color: '#0f0f0f' },
  greeting: { fontSize: 13, color: C.muted, fontWeight: '500' },
  userName: { fontSize: 18, fontWeight: '700', color: C.text, marginTop: 1 },
  headerActions: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  iconBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    alignItems: 'center',
    justifyContent: 'center',
  },

  brandCard: {
    backgroundColor: C.surface,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: C.border,
    padding: 16,
    marginBottom: 14,
    overflow: 'hidden',
  },
  brandRow: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 10 },
  logoBox: {
    width: 42,
    height: 42,
    borderRadius: 12,
    backgroundColor: C.accent,
    alignItems: 'center',
    justifyContent: 'center',
  },
  brandName: { fontSize: 18, fontWeight: '800', color: C.text },
  brandSub: { fontSize: 12, color: C.muted, marginTop: 2 },
  brandTag: { fontSize: 12, fontWeight: '700', color: C.accent },

  banner: { borderRadius: 16, overflow: 'hidden', marginBottom: 16, minHeight: 130 },
  bannerImage: { borderRadius: 16 },
  bannerOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.62)',
    padding: 16,
    justifyContent: 'flex-end',
    minHeight: 130,
  },
  bannerBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    alignSelf: 'flex-start',
    backgroundColor: C.accentDim,
    borderWidth: 1,
    borderColor: C.accentBorder,
    borderRadius: 20,
    paddingHorizontal: 10,
    paddingVertical: 4,
    marginBottom: 8,
  },
  bannerBadgeText: { fontSize: 10, fontWeight: '700', color: C.accent, letterSpacing: 0.3 },
  bannerTitle: { fontSize: 16, fontWeight: '700', color: '#fff', marginBottom: 4, lineHeight: 22 },
  bannerDesc: { fontSize: 11, color: 'rgba(255,255,255,0.65)', lineHeight: 16 },

  sectionTitle: { fontSize: 15, fontWeight: '700', color: C.text, marginBottom: 4 },
  sectionHint: { fontSize: 12, color: C.muted, marginBottom: 12 },

  moduleCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 14,
    padding: 14,
    marginBottom: 10,
    gap: 12,
  },
  moduleCardLocked: { opacity: 0.55 },
  moduleIcon: {
    width: 46,
    height: 46,
    borderRadius: 11,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: C.border,
  },
  moduleBody: { flex: 1 },
  moduleTitle: { fontSize: 14, fontWeight: '700', color: C.text, marginBottom: 2 },
  moduleTitleLocked: { color: C.muted },
  moduleSub: { fontSize: 11, color: C.muted, lineHeight: 16 },
  moduleAction: { fontSize: 11, fontWeight: '600', color: C.accent, marginTop: 5 },
  moduleRight: { alignItems: 'flex-end', gap: 6 },
  readyBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: 'rgba(74,223,111,0.12)',
    paddingHorizontal: 7,
    paddingVertical: 3,
    borderRadius: 20,
  },
  readyDot: { width: 5, height: 5, borderRadius: 3, backgroundColor: C.success },
  readyText: { fontSize: 9, fontWeight: '700', color: C.success },
  soonBadge: {
    backgroundColor: C.surface2,
    borderWidth: 1,
    borderColor: C.border,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  soonText: { fontSize: 9, fontWeight: '600', color: C.muted },
  chevronWrap: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: C.accentDim,
    alignItems: 'center',
    justifyContent: 'center',
  },

  tipBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    backgroundColor: C.accentDim,
    borderWidth: 1,
    borderColor: C.accentBorder,
    borderRadius: 12,
    padding: 12,
    marginTop: 4,
  },
  tipText: { flex: 1, fontSize: 12, color: C.muted, lineHeight: 17 },

  logoutBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginTop: 16,
    paddingVertical: 14,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: C.border,
    backgroundColor: C.surface,
  },
  logoutText: { fontSize: 14, fontWeight: '600', color: C.muted },
});
