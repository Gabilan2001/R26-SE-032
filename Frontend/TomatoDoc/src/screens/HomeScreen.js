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
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { AuthContext } from '../context/AuthContext';
import { palette as P, gradients, radius, shadow, type } from '../theme';

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
      activeOpacity={locked ? 1 : 0.8}
    >
      <View style={[styles.moduleIcon, { backgroundColor: iconBg }]}>
        <MaterialCommunityIcons name={icon} size={24} color={iconColor} />
      </View>
      <View style={styles.moduleBody}>
        <View style={styles.moduleTitleRow}>
          <Text style={[styles.moduleTitle, locked && styles.moduleTitleLocked]} numberOfLines={1}>{title}</Text>
          {!locked && badge ? (
            <View style={styles.readyBadge}>
              <View style={styles.readyDot} />
              <Text style={styles.readyText}>{badge}</Text>
            </View>
          ) : null}
        </View>
        <Text style={styles.moduleSub} numberOfLines={2}>{subtitle}</Text>
        {!locked && <Text style={styles.moduleAction}>Open module</Text>}
      </View>
      {locked ? (
        <View style={styles.soonBadge}>
          <Text style={styles.soonText}>Soon</Text>
        </View>
      ) : (
        <View style={styles.chevronWrap}>
          <MaterialCommunityIcons name="arrow-right" size={18} color={P.lime} />
        </View>
      )}
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
      <StatusBar barStyle="light-content" backgroundColor={P.forest} />

      <ScrollView contentContainerStyle={{ paddingBottom: 130 }} showsVerticalScrollIndicator={false}>
        {/* Hero */}
        <LinearGradient
          colors={gradients.hero}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={[styles.hero, { paddingTop: insets.top + 14 }]}
        >
          <View style={styles.header}>
            <View style={styles.headerLeft}>
              <TouchableOpacity
                style={styles.avatar}
                onPress={() => navigation.navigate('User')}
                activeOpacity={0.8}
              >
                <Text style={styles.avatarText}>{initial}</Text>
              </TouchableOpacity>
              <View style={{ flex: 1 }}>
                <Text style={styles.greeting}>{greeting}</Text>
                <Text style={styles.userName} numberOfLines={1}>{displayName}</Text>
              </View>
            </View>
            <TouchableOpacity style={styles.iconBtn} onPress={logout} activeOpacity={0.7}>
              <MaterialCommunityIcons name="logout" size={18} color={P.lime} />
            </TouchableOpacity>
          </View>

          <View style={styles.eyebrowRow}>
            <View style={styles.eyebrowLine} />
            <Text style={styles.heroEyebrow}>Precision tomato farming</Text>
          </View>
          <Text style={styles.heroTitle}>
            TomatoDoc<Text style={styles.heroDot}>.</Text>
          </Text>
          <Text style={styles.heroSub}>
            Scan your crop, understand the problem and get treatment advice in one place.
          </Text>

          <View style={styles.pillRow}>
            {['Scan', 'Diagnose', 'Treat', 'Track'].map((w) => (
              <View key={w} style={styles.pill}>
                <Text style={styles.pillText}>{w}</Text>
              </View>
            ))}
          </View>
        </LinearGradient>

        <View style={styles.body}>
          {/* Banner */}
          <ImageBackground
            source={require('../../assets/images/tomato1.jpg')}
            imageStyle={styles.bannerImage}
            style={styles.banner}
          >
            <LinearGradient
              colors={['rgba(14,51,38,0.15)', 'rgba(14,51,38,0.88)']}
              style={styles.bannerOverlay}
            >
              <View style={styles.bannerBadge}>
                <MaterialCommunityIcons name="shield-check-outline" size={12} color={P.lime} />
                <Text style={styles.bannerBadgeText}>Crop intelligence</Text>
              </View>
              <Text style={styles.bannerTitle}>Field diagnostics and treatment guidance</Text>
              <Text style={styles.bannerDesc}>
                Built for farmers, field trials, and data-driven crop decisions.
              </Text>
            </LinearGradient>
          </ImageBackground>

          {/* Modules */}
          <Text style={[type.eyebrow, styles.sectionEyebrow]}>Diagnostic tools</Text>
          <Text style={styles.sectionTitle}>What would you like to do?</Text>

          <ModuleCard
            icon="chart-line"
            iconColor={P.warn}
            iconBg={P.warnDim}
            title="Price forecasting"
            subtitle="Market trend analytics and selling recommendations"
            badge="Ready"
            onPress={() => navigation.navigate('PricePrediction')}
          />
          <ModuleCard
            icon="leaf"
            iconColor={P.leaf}
            iconBg={P.surfaceTint}
            title="Nutrient deficiency"
            subtitle="Leaf scan with fertilizer and treatment recommendations"
            badge="Ready"
            onPress={() => navigation.navigate('NutrientModule', { screen: 'Scan' })}
          />
          <ModuleCard
            icon="chart-timeline-variant"
            iconColor={P.info}
            iconBg={P.infoDim}
            title="Disease monitoring"
            subtitle="Track severity and recovery over multiple observations"
            badge="Ready"
            onPress={() => navigation.navigate('MonitoringModule')}
          />
          <ModuleCard
            icon="virus"
            iconColor={P.forestMid}
            iconBg={P.goodDim}
            title="Disease in leaf"
            subtitle="Pathology diagnostics and leaf disease scan"
            badge="Ready"
            onPress={() => navigation.navigate('DiseaseModule', { screen: 'DiseaseScan' })}
          />
          <ModuleCard
            icon="food-apple"
            iconColor={P.tomato}
            iconBg={P.tomatoDim}
            title="Fruit disease detection"
            subtitle="Identify fruit diseases and view treatment guidance"
            badge="Ready"
            onPress={() => navigation.navigate('FruitModule', { screen: 'FruitScan' })}
          />

          <View style={styles.tipBox}>
            <View style={styles.tipIcon}>
              <MaterialCommunityIcons name="white-balance-sunny" size={16} color={P.forest} />
            </View>
            <Text style={styles.tipText}>
              For best results, capture photos in natural daylight with the subject filling most of the frame.
            </Text>
          </View>

          <TouchableOpacity style={styles.logoutBtn} onPress={logout} activeOpacity={0.85}>
            <MaterialCommunityIcons name="logout" size={18} color={P.muted} />
            <Text style={styles.logoutText}>Log out</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: P.bg },

  hero: {
    paddingHorizontal: 20,
    paddingBottom: 34,
    borderBottomLeftRadius: radius.xl,
    borderBottomRightRadius: radius.xl,
  },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 26 },
  headerLeft: { flexDirection: 'row', alignItems: 'center', gap: 12, flex: 1 },
  avatar: {
    width: 46,
    height: 46,
    borderRadius: 23,
    backgroundColor: P.lime,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: { fontSize: 19, fontWeight: '800', color: P.forest },
  greeting: { fontSize: 12, color: P.onDarkSoft, fontWeight: '600' },
  userName: { fontSize: 18, fontWeight: '800', color: P.onDark, marginTop: 1, letterSpacing: -0.3 },
  iconBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.10)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.16)',
    alignItems: 'center',
    justifyContent: 'center',
  },

  eyebrowRow: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 6 },
  eyebrowLine: { width: 26, height: 1.5, backgroundColor: P.lime },
  heroEyebrow: { ...type.eyebrow, color: P.lime, fontSize: 10 },
  heroTitle: { fontSize: 42, fontWeight: '800', letterSpacing: -1.6, color: P.onDark },
  heroDot: { color: P.lime },
  heroSub: { fontSize: 14, lineHeight: 21, color: P.onDarkSoft, marginTop: 6, maxWidth: 330 },
  pillRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 18 },
  pill: {
    backgroundColor: 'rgba(255,255,255,0.10)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.18)',
    borderRadius: radius.pill,
    paddingHorizontal: 14,
    paddingVertical: 7,
  },
  pillText: { fontSize: 12, fontWeight: '700', color: P.lime },

  body: { paddingHorizontal: 18, marginTop: 18 },

  banner: { borderRadius: radius.lg, overflow: 'hidden', marginBottom: 24, minHeight: 150, ...shadow.card },
  bannerImage: { borderRadius: radius.lg },
  bannerOverlay: { flex: 1, padding: 16, justifyContent: 'flex-end', minHeight: 150 },
  bannerBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    alignSelf: 'flex-start',
    backgroundColor: 'rgba(214,239,117,0.16)',
    borderWidth: 1,
    borderColor: 'rgba(214,239,117,0.35)',
    borderRadius: radius.pill,
    paddingHorizontal: 10,
    paddingVertical: 4,
    marginBottom: 8,
  },
  bannerBadgeText: { fontSize: 10, fontWeight: '700', color: P.lime, letterSpacing: 0.4 },
  bannerTitle: { fontSize: 17, fontWeight: '800', color: '#fff', marginBottom: 4, lineHeight: 23, letterSpacing: -0.3 },
  bannerDesc: { fontSize: 12, color: 'rgba(255,255,255,0.75)', lineHeight: 17 },

  sectionEyebrow: { marginBottom: 4 },
  sectionTitle: { ...type.h2, fontSize: 21, marginBottom: 14 },

  moduleCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: P.surface,
    borderWidth: 1,
    borderColor: P.border,
    borderRadius: radius.lg,
    padding: 14,
    marginBottom: 12,
    gap: 14,
    ...shadow.card,
  },
  moduleCardLocked: { opacity: 0.55 },
  moduleIcon: { width: 52, height: 52, borderRadius: 16, alignItems: 'center', justifyContent: 'center' },
  moduleBody: { flex: 1 },
  moduleTitleRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 3 },
  moduleTitle: { fontSize: 15, fontWeight: '800', color: P.text, letterSpacing: -0.2, flexShrink: 1 },
  moduleTitleLocked: { color: P.muted },
  moduleSub: { fontSize: 12, color: P.textSoft, lineHeight: 17 },
  moduleAction: { fontSize: 11, fontWeight: '800', color: P.forestMid, marginTop: 6, letterSpacing: 0.2 },
  readyBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: P.goodDim,
    paddingHorizontal: 7,
    paddingVertical: 2,
    borderRadius: radius.pill,
  },
  readyDot: { width: 5, height: 5, borderRadius: 3, backgroundColor: P.good },
  readyText: { fontSize: 9, fontWeight: '800', color: P.good, letterSpacing: 0.3 },
  soonBadge: {
    backgroundColor: P.surface2,
    borderWidth: 1,
    borderColor: P.border,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  soonText: { fontSize: 9, fontWeight: '700', color: P.muted },
  chevronWrap: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: P.forest,
    alignItems: 'center',
    justifyContent: 'center',
  },

  tipBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: P.surfaceTint,
    borderWidth: 1,
    borderColor: '#D5E7BD',
    borderRadius: radius.md,
    padding: 14,
    marginTop: 6,
  },
  tipIcon: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: P.lime,
    alignItems: 'center',
    justifyContent: 'center',
  },
  tipText: { flex: 1, fontSize: 12, color: P.textSoft, lineHeight: 18 },

  logoutBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginTop: 16,
    paddingVertical: 14,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: P.border,
    backgroundColor: P.surface,
  },
  logoutText: { fontSize: 14, fontWeight: '700', color: P.muted },
});
