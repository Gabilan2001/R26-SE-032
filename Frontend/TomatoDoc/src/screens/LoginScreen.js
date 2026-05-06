import React, { useContext, useState, useRef, useEffect } from 'react';
import {
  StyleSheet,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  Pressable,
  Animated,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StatusBar,
} from 'react-native';
import { AuthContext } from '../context/AuthContext';

// ── Tokens (matches your dark + acid-yellow palette) ──────────────────────────
const C = {
  bg:         '#0f0f0f',
  surface:    '#1a1a1a',
  surface2:   '#222222',
  accent:     '#c8f135',       // yellow-green
  accentDim:  'rgba(200,241,53,0.10)',
  text:       '#f0f0f0',
  muted:      '#666666',
  border:     'rgba(255,255,255,0.07)',
  danger:     '#ff5c5c',
  dangerDim:  'rgba(255,92,92,0.12)',
};

// ── Reusable animated card strip (Scan / Analyse / Treat + accuracy stat) ─────
function PlantStrip() {
  const scale = useRef(new Animated.Value(0.9)).current;
  const opacity = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    Animated.parallel([
      Animated.spring(scale,   { toValue: 1, useNativeDriver: true, delay: 150 }),
      Animated.timing(opacity, { toValue: 1, duration: 400, delay: 150, useNativeDriver: true }),
    ]).start();
  }, []);
  const cards = [
    { emoji: '🌿', label: 'Scan',    active: true },
    { emoji: '🔬', label: 'Analyse', active: false },
    { emoji: '💊', label: 'Treat',   active: false },
  ];
  return (
    <Animated.View style={[styles.strip, { opacity, transform: [{ scale }] }]}>
      {cards.map(c => (
        <View key={c.label} style={[styles.stripCard, c.active && styles.stripCardActive]}>
          <Text style={styles.stripEmoji}>{c.emoji}</Text>
          <Text style={[styles.stripLabel, c.active && { color: C.accent }]}>{c.label}</Text>
          {c.active && <View style={styles.stripUnderline} />}
        </View>
      ))}
      <View style={styles.statCard}>
        <Text style={styles.statNum}>85%</Text>
        <Text style={styles.statLabel}>Accuracy</Text>
      </View>
    </Animated.View>
  );
}

// ── Main Screen ───────────────────────────────────────────────────────────────
export default function LoginScreen({ navigation }) {
  const { login } = useContext(AuthContext);
  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [error, setError]       = useState('');
  const [loading, setLoading]   = useState(false);

  // Slide-in animation for the form card
  const slideY  = useRef(new Animated.Value(40)).current;
  const opacity = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    Animated.parallel([
      Animated.spring(slideY,  { toValue: 0, useNativeDriver: true, delay: 250 }),
      Animated.timing(opacity, { toValue: 1, duration: 450, delay: 250, useNativeDriver: true }),
    ]).start();
  }, []);

  // Button press scale
  const btnScale = useRef(new Animated.Value(1)).current;
  const onPressIn  = () => Animated.spring(btnScale, { toValue: 0.96, useNativeDriver: true }).start();
  const onPressOut = () => Animated.spring(btnScale, { toValue: 1,    useNativeDriver: true }).start();

  const onLogin = async () => {
    if (!email || !password) { setError('Please fill in all fields.'); return; }
    try {
      setError('');
      setLoading(true);
      await login(email, password);
    } catch (e) {
      setError(e?.response?.data?.message || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.root}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <StatusBar barStyle="light-content" backgroundColor={C.bg} />
      <ScrollView
        contentContainerStyle={styles.scroll}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        {/* ── Hero ── */}
        <View style={styles.hero}>
          {/* Live badge */}
          <View style={styles.badge}>
            <View style={styles.badgeDot} />
            <Text style={styles.badgeText}>Plant Health AI</Text>
          </View>

          <Text style={styles.heroTitle}>
            Welcome to{'\n'}
            <Text style={styles.heroAccent}>TomatoDoc</Text>
          </Text>
          <Text style={styles.heroSub}>
            Scan, diagnose, and treat your plants with AI precision.
          </Text>
        </View>

        {/* ── Plant strip ── */}
        <PlantStrip />

        {/* ── Form card ── */}
        <Animated.View style={[styles.formCard, { opacity, transform: [{ translateY: slideY }] }]}>

          {/* Email */}
          <Text style={styles.label}>Email</Text>
          <View style={styles.inputWrap}>
            <Text style={styles.inputIcon}>✉</Text>
            <TextInput
              style={styles.input}
              placeholder="you@example.com"
              placeholderTextColor={C.muted}
              value={email}
              onChangeText={setEmail}
              autoCapitalize="none"
              keyboardType="email-address"
              selectionColor={C.accent}
            />
          </View>

          {/* Password */}
          <Text style={[styles.label, { marginTop: 16 }]}>Password</Text>
          <View style={styles.inputWrap}>
            <Text style={styles.inputIcon}>🔒</Text>
            <TextInput
              style={[styles.input, { paddingRight: 44 }]}
              placeholder="••••••••"
              placeholderTextColor={C.muted}
              value={password}
              onChangeText={setPassword}
              secureTextEntry={!showPass}
              selectionColor={C.accent}
            />
            <TouchableOpacity
              style={styles.eyeBtn}
              onPress={() => setShowPass(p => !p)}
              hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
            >
              <Text style={styles.eyeIcon}>{showPass ? '🙈' : '👁'}</Text>
            </TouchableOpacity>
          </View>

          <TouchableOpacity style={styles.forgotRow}>
            <Text style={styles.forgotText}>Forgot password?</Text>
          </TouchableOpacity>

          {/* Error */}
          {!!error && (
            <View style={styles.errorBox}>
              <Text style={styles.errorIcon}>⚠</Text>
              <Text style={styles.errorText}>{error}</Text>
            </View>
          )}

          {/* Login CTA */}
          <Animated.View style={{ transform: [{ scale: btnScale }] }}>
            <Pressable
              style={[styles.btnPrimary, loading && styles.btnLoading]}
              onPressIn={onPressIn}
              onPressOut={onPressOut}
              onPress={onLogin}
              disabled={loading}
            >
              <Text style={styles.btnPrimaryText}>
                {loading ? 'Logging in…' : 'Login'}
              </Text>
            </Pressable>
          </Animated.View>

          {/* Divider */}
          <View style={styles.divider}>
            <View style={styles.dividerLine} />
            <Text style={styles.dividerText}>or continue with</Text>
            <View style={styles.dividerLine} />
          </View>

          {/* Google */}
          <TouchableOpacity style={styles.btnSecondary}>
            <Text style={styles.googleG}>G</Text>
            <Text style={styles.btnSecondaryText}>Continue with Google</Text>
          </TouchableOpacity>

          {/* Register */}
          <View style={styles.registerRow}>
            <Text style={styles.registerText}>Don't have an account? </Text>
            <TouchableOpacity onPress={() => navigation.navigate('Register')}>
              <Text style={styles.registerLink}>Create account</Text>
            </TouchableOpacity>
          </View>
        </Animated.View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  root:  { flex: 1, backgroundColor: C.bg },
  scroll: { flexGrow: 1, paddingHorizontal: 24, paddingTop: 60, paddingBottom: 40 },

  // Hero
  hero:       { marginBottom: 24 },
  badge:      { flexDirection: 'row', alignItems: 'center', alignSelf: 'flex-start',
                backgroundColor: C.accentDim, borderWidth: 1, borderColor: 'rgba(200,241,53,0.2)',
                borderRadius: 100, paddingHorizontal: 12, paddingVertical: 5, marginBottom: 20 },
  badgeDot:   { width: 6, height: 6, borderRadius: 3, backgroundColor: C.accent, marginRight: 6 },
  badgeText:  { fontSize: 11, fontWeight: '600', color: C.accent, letterSpacing: 0.5 },
  heroTitle:  { fontSize: 32, fontWeight: '800', color: C.text, lineHeight: 38, marginBottom: 8 },
  heroAccent: { color: C.accent },
  heroSub:    { fontSize: 13, color: C.muted, lineHeight: 20 },

  // Strip
  strip:          { flexDirection: 'row', gap: 10, marginBottom: 28 },
  stripCard:      { flex: 1, backgroundColor: C.surface, borderWidth: 1, borderColor: C.border,
                    borderRadius: 14, paddingVertical: 10, paddingHorizontal: 8,
                    alignItems: 'center', gap: 4, position: 'relative', overflow: 'hidden' },
  stripCardActive:{ borderColor: 'rgba(200,241,53,0.3)', backgroundColor: 'rgba(200,241,53,0.06)' },
  stripUnderline: { position: 'absolute', bottom: 0, left: 0, right: 0, height: 2, backgroundColor: C.accent },
  stripEmoji:     { fontSize: 22 },
  stripLabel:     { fontSize: 9, color: C.muted, fontWeight: '600', letterSpacing: 0.3, textTransform: 'uppercase' },
  statCard:       { backgroundColor: C.accent, borderRadius: 12, paddingHorizontal: 12, paddingVertical: 8,
                    alignItems: 'center', justifyContent: 'center', minWidth: 64 },
  statNum:        { fontSize: 18, fontWeight: '800', color: '#0f0f0f', lineHeight: 22 },
  statLabel:      { fontSize: 8, fontWeight: '700', color: 'rgba(0,0,0,0.45)', textTransform: 'uppercase', letterSpacing: 0.4 },

  // Form card
  formCard: {
    backgroundColor: C.surface,
    borderRadius: 24,
    borderWidth: 1,
    borderColor: C.border,
    padding: 20,
  },

  label:    { fontSize: 11, fontWeight: '700', color: C.muted, textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 8 },
  inputWrap:{ flexDirection: 'row', alignItems: 'center', backgroundColor: C.surface2,
              borderWidth: 1.5, borderColor: C.border, borderRadius: 12 },
  inputIcon:{ paddingLeft: 14, fontSize: 14, color: C.muted },
  input:    { flex: 1, padding: 14, paddingLeft: 10, color: C.text, fontSize: 14 },
  eyeBtn:   { paddingRight: 14 },
  eyeIcon:  { fontSize: 14 },

  forgotRow:   { alignSelf: 'flex-end', marginTop: 8, marginBottom: 4 },
  forgotText:  { fontSize: 11, color: C.accent, fontWeight: '600' },

  // Error
  errorBox:  { flexDirection: 'row', alignItems: 'center', gap: 8,
               backgroundColor: C.dangerDim, borderWidth: 1, borderColor: 'rgba(255,92,92,0.2)',
               borderRadius: 10, padding: 10, marginTop: 12 },
  errorIcon: { fontSize: 13, color: C.danger },
  errorText: { flex: 1, fontSize: 12, color: C.danger },

  // Buttons
  btnPrimary:      { backgroundColor: C.accent, borderRadius: 14, paddingVertical: 16,
                     alignItems: 'center', marginTop: 20 },
  btnLoading:      { opacity: 0.7 },
  btnPrimaryText:  { fontSize: 15, fontWeight: '700', color: '#0f0f0f', letterSpacing: 0.3 },

  divider:     { flexDirection: 'row', alignItems: 'center', marginVertical: 20, gap: 12 },
  dividerLine: { flex: 1, height: 1, backgroundColor: C.border },
  dividerText: { fontSize: 11, color: C.muted },

  btnSecondary:     { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8,
                      backgroundColor: C.surface2, borderWidth: 1.5, borderColor: C.border,
                      borderRadius: 14, paddingVertical: 14 },
  googleG:          { fontSize: 15, fontWeight: '800', color: '#4285F4' },
  btnSecondaryText: { fontSize: 13, fontWeight: '500', color: C.text },

  registerRow:  { flexDirection: 'row', justifyContent: 'center', marginTop: 20, alignItems: 'center' },
  registerText: { fontSize: 12, color: C.muted },
  registerLink: { fontSize: 12, fontWeight: '700', color: C.accent },
});