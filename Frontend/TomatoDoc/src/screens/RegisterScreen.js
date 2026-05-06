import React, { useContext, useRef, useState, useEffect } from 'react';
import {
  Animated,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { AuthContext } from '../context/AuthContext';

// ── Tokens ────────────────────────────────────────────────────────────────────
const C = {
  bg:           '#0f0f0f',
  surface:      '#1a1a1a',
  surface2:     '#222222',
  accent:       '#c8f135',
  accentDim:    'rgba(200,241,53,0.10)',
  accentBorder: 'rgba(200,241,53,0.22)',
  text:         '#f0f0f0',
  muted:        '#555555',
  border:       'rgba(255,255,255,0.07)',
  danger:       '#ff5c5c',
  dangerDim:    'rgba(255,92,92,0.10)',
  success:      '#4adf6f',
};

// ── Password strength ─────────────────────────────────────────────────────────
function getStrength(pass) {
  if (!pass) return 0;
  let s = 0;
  if (pass.length >= 8)                  s++;
  if (/[A-Z]/.test(pass) || /\d/.test(pass)) s++;
  if (/[^A-Za-z0-9]/.test(pass))        s++;
  return s; // 0–3
}

const STRENGTH_META = [
  null,
  { label: 'Weak',   color: C.danger  },
  { label: 'Fair',   color: C.accent  },
  { label: 'Strong', color: C.success },
];

// ── Strength bar row ──────────────────────────────────────────────────────────
function StrengthBars({ password }) {
  const str = getStrength(password);
  if (!password) return null;
  const meta = STRENGTH_META[str];
  return (
    <View>
      <View style={styles.strengthRow}>
        {[0, 1, 2].map(i => (
          <View
            key={i}
            style={[
              styles.strengthBar,
              i < str && { backgroundColor: meta?.color ?? C.border },
            ]}
          />
        ))}
      </View>
      {meta && <Text style={[styles.strengthLabel, { color: meta.color }]}>{meta.label}</Text>}
    </View>
  );
}

// ── Form field ────────────────────────────────────────────────────────────────
function Field({ label, icon, error, children }) {
  return (
    <View style={{ marginTop: 16 }}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <View style={[styles.inputWrap, error && styles.inputWrapError]}>
        <Text style={styles.inputIcon}>{icon}</Text>
        {children}
      </View>
    </View>
  );
}

// ── Step indicator ────────────────────────────────────────────────────────────
function StepDots({ active = 1 }) {
  return (
    <View style={styles.stepRow}>
      {[0, 1, 2].map(i => (
        <View
          key={i}
          style={[
            styles.stepDot,
            i < active  && styles.stepDotDone,
            i === active && styles.stepDotActive,
          ]}
        />
      ))}
    </View>
  );
}

// ── Main Screen ───────────────────────────────────────────────────────────────
export default function RegisterScreen({ navigation }) {
  const { register } = useContext(AuthContext);

  const [name,     setName]     = useState('');
  const [email,    setEmail]    = useState('');
  const [password, setPassword] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [terms,    setTerms]    = useState(false);
  const [error,    setError]    = useState('');
  const [loading,  setLoading]  = useState(false);

  const isReady = name.trim() && email.trim() && password.length >= 6 && terms;

  // Entrance animation
  const heroOp = useRef(new Animated.Value(0)).current;
  const heroY  = useRef(new Animated.Value(28)).current;
  const formOp = useRef(new Animated.Value(0)).current;
  const formY  = useRef(new Animated.Value(28)).current;
  useEffect(() => {
    Animated.parallel([
      Animated.timing(heroOp, { toValue: 1, duration: 380, useNativeDriver: true }),
      Animated.spring(heroY,  { toValue: 0, useNativeDriver: true }),
    ]).start(() =>
      Animated.parallel([
        Animated.timing(formOp, { toValue: 1, duration: 350, useNativeDriver: true }),
        Animated.spring(formY,  { toValue: 0, useNativeDriver: true }),
      ]).start()
    );
  }, []);

  // Button scale
  const btnScale = useRef(new Animated.Value(1)).current;
  const onPressIn  = () => Animated.spring(btnScale, { toValue: 0.96, useNativeDriver: true }).start();
  const onPressOut = () => Animated.spring(btnScale, { toValue: 1,    useNativeDriver: true }).start();

  // Terms bounce
  const termsScale = useRef(new Animated.Value(1)).current;
  const toggleTerms = () => {
    Animated.sequence([
      Animated.spring(termsScale, { toValue: 0.85, useNativeDriver: true }),
      Animated.spring(termsScale, { toValue: 1,    useNativeDriver: true }),
    ]).start();
    setTerms(t => !t);
  };

  const onRegister = async () => {
    if (!name.trim() || !email.trim() || !password) {
      setError('Please fill in all fields.');
      return;
    }
    try {
      setError('');
      setLoading(true);
      await register(name, email, password);
      navigation.goBack();
    } catch (e) {
      setError(e?.response?.data?.message || 'Registration failed. Please try again.');
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
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        {/* ── Back ── */}
        <View style={styles.backRow}>
          <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()}>
            <Text style={styles.backArrow}>←</Text>
          </TouchableOpacity>
        </View>

        {/* ── Hero ── */}
        <Animated.View style={[styles.hero, { opacity: heroOp, transform: [{ translateY: heroY }] }]}>
          <View style={styles.badge}>
            <View style={styles.badgeDot} />
            <Text style={styles.badgeTxt}>New Account</Text>
          </View>
          <Text style={styles.heroTitle}>
            {'Join\n'}<Text style={styles.heroAccent}>TomatoDoc</Text>
          </Text>
          <Text style={styles.heroSub}>
            Start monitoring your crops with AI-powered precision today.
          </Text>
        </Animated.View>

        {/* ── Step dots ── */}
        <StepDots active={1} />

        {/* ── Error ── */}
        {!!error && (
          <View style={styles.errorBox}>
            <Text style={styles.errorIcon}>⚠</Text>
            <Text style={styles.errorTxt}>{error}</Text>
          </View>
        )}

        {/* ── Form card ── */}
        <Animated.View style={[styles.formCard, { opacity: formOp, transform: [{ translateY: formY }] }]}>
          <Field label="Full Name" icon="👤" error={false}>
            <TextInput
              style={styles.input}
              placeholder="John Doe"
              placeholderTextColor={C.muted}
              value={name}
              onChangeText={setName}
              selectionColor={C.accent}
            />
          </Field>

          <Field label="Email" icon="✉" error={false}>
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
          </Field>

          <Field label="Password" icon="🔒" error={false}>
            <TextInput
              style={[styles.input, { paddingRight: 44 }]}
              placeholder="Min. 8 characters"
              placeholderTextColor={C.muted}
              value={password}
              onChangeText={setPassword}
              secureTextEntry={!showPass}
              selectionColor={C.accent}
            />
            <TouchableOpacity
              style={styles.eyeBtn}
              onPress={() => setShowPass(v => !v)}
              hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
            >
              <Text style={styles.eyeIcon}>{showPass ? '🙈' : '👁'}</Text>
            </TouchableOpacity>
          </Field>

          <StrengthBars password={password} />
        </Animated.View>

        {/* ── Terms ── */}
        <View style={styles.termsRow}>
          <Animated.View style={{ transform: [{ scale: termsScale }] }}>
            <TouchableOpacity
              style={[styles.termsCheck, terms && styles.termsCheckActive]}
              onPress={toggleTerms}
              activeOpacity={0.8}
            >
              {terms && <Text style={styles.termsCheckMark}>✓</Text>}
            </TouchableOpacity>
          </Animated.View>
          <Text style={styles.termsTxt}>
            I agree to the{' '}
            <Text style={styles.termsLink}>Terms of Service</Text>
            {' '}and{' '}
            <Text style={styles.termsLink}>Privacy Policy</Text>
          </Text>
        </View>

        {/* ── CTA ── */}
        <Animated.View style={{ transform: [{ scale: btnScale }] }}>
          <Pressable
            style={[styles.btnPrimary, !isReady && styles.btnPrimaryDisabled]}
            onPressIn={onPressIn}
            onPressOut={onPressOut}
            onPress={onRegister}
            disabled={!isReady || loading}
          >
            <Text style={styles.btnPrimaryIcon}>🌱</Text>
            <Text style={styles.btnPrimaryTxt}>
              {loading ? 'Creating…' : 'Create Account'}
            </Text>
          </Pressable>
        </Animated.View>

        {/* ── Divider ── */}
        <View style={styles.divider}>
          <View style={styles.dividerLine} />
          <Text style={styles.dividerTxt}>or sign up with</Text>
          <View style={styles.dividerLine} />
        </View>

        {/* ── Google ── */}
        <TouchableOpacity style={styles.btnGoogle} activeOpacity={0.85}>
          <Text style={styles.googleG}>G</Text>
          <Text style={styles.btnGoogleTxt}>Continue with Google</Text>
        </TouchableOpacity>

        {/* ── Login link ── */}
        <View style={styles.loginRow}>
          <Text style={styles.loginTxt}>Already have an account? </Text>
          <TouchableOpacity onPress={() => navigation.goBack()}>
            <Text style={styles.loginLink}>Login</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  root:    { flex: 1, backgroundColor: C.bg },
  content: { flexGrow: 1, paddingHorizontal: 24, paddingTop: 54, paddingBottom: 40 },

  // Back
  backRow:   { marginBottom: 4 },
  backBtn:   { width: 32, height: 32, backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: 16, alignItems: 'center', justifyContent: 'center', alignSelf: 'flex-start' },
  backArrow: { fontSize: 15, color: C.text },

  // Hero
  hero:       { marginBottom: 24 },
  badge:      { flexDirection: 'row', alignItems: 'center', alignSelf: 'flex-start',
                backgroundColor: C.accentDim, borderWidth: 1, borderColor: C.accentBorder,
                borderRadius: 100, paddingHorizontal: 12, paddingVertical: 5, marginBottom: 18 },
  badgeDot:   { width: 6, height: 6, borderRadius: 3, backgroundColor: C.accent, marginRight: 6 },
  badgeTxt:   { fontSize: 11, fontWeight: '700', color: C.accent, letterSpacing: 0.4 },
  heroTitle:  { fontSize: 30, fontWeight: '800', color: C.text, lineHeight: 36, marginBottom: 8 },
  heroAccent: { color: C.accent },
  heroSub:    { fontSize: 13, color: C.muted, lineHeight: 20 },

  // Steps
  stepRow:       { flexDirection: 'row', gap: 6, marginBottom: 22 },
  stepDot:       { height: 4, width: 28, borderRadius: 2, backgroundColor: C.surface2 },
  stepDotDone:   { backgroundColor: C.accentDim, width: 28 },
  stepDotActive: { backgroundColor: C.accent,    width: 40 },

  // Error
  errorBox:  { flexDirection: 'row', alignItems: 'flex-start', gap: 8,
               backgroundColor: C.dangerDim, borderWidth: 1, borderColor: 'rgba(255,92,92,0.2)',
               borderRadius: 12, padding: 12, marginBottom: 12 },
  errorIcon: { fontSize: 13, color: C.danger, marginTop: 1 },
  errorTxt:  { flex: 1, fontSize: 12, color: C.danger, lineHeight: 17 },

  // Form card
  formCard: {
    backgroundColor: C.surface,
    borderWidth: 1, borderColor: C.border,
    borderRadius: 22, padding: 20, marginBottom: 16,
  },
  fieldLabel:  { fontSize: 10, fontWeight: '700', color: C.muted, textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 8 },
  inputWrap:   { flexDirection: 'row', alignItems: 'center', backgroundColor: C.surface2, borderWidth: 1.5, borderColor: C.border, borderRadius: 12 },
  inputWrapError:{ borderColor: 'rgba(255,92,92,0.5)' },
  inputIcon:   { paddingLeft: 14, fontSize: 14, color: C.muted },
  input:       { flex: 1, padding: 13, paddingLeft: 10, color: C.text, fontSize: 14 },
  eyeBtn:      { paddingRight: 14 },
  eyeIcon:     { fontSize: 13 },

  // Strength
  strengthRow:  { flexDirection: 'row', gap: 4, marginTop: 8 },
  strengthBar:  { flex: 1, height: 3, borderRadius: 2, backgroundColor: C.surface2 },
  strengthLabel:{ fontSize: 10, fontWeight: '700', textAlign: 'right', marginTop: 5 },

  // Terms
  termsRow:         { flexDirection: 'row', alignItems: 'flex-start', gap: 10, marginBottom: 20 },
  termsCheck:       { width: 18, height: 18, borderRadius: 5, borderWidth: 1.5, borderColor: C.border,
                      alignItems: 'center', justifyContent: 'center', marginTop: 1 },
  termsCheckActive: { backgroundColor: C.accent, borderColor: C.accent },
  termsCheckMark:   { fontSize: 9, color: '#0f0f0f', fontWeight: '900' },
  termsTxt:         { flex: 1, fontSize: 11, color: C.muted, lineHeight: 17 },
  termsLink:        { color: C.accent, fontWeight: '700' },

  // Buttons
  btnPrimary:         { backgroundColor: C.accent, borderRadius: 14, paddingVertical: 16,
                        flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8 },
  btnPrimaryDisabled: { opacity: 0.3 },
  btnPrimaryIcon:     { fontSize: 15 },
  btnPrimaryTxt:      { fontSize: 14, fontWeight: '800', color: '#0f0f0f', letterSpacing: 0.3 },

  divider:     { flexDirection: 'row', alignItems: 'center', marginVertical: 18, gap: 12 },
  dividerLine: { flex: 1, height: 1, backgroundColor: C.border },
  dividerTxt:  { fontSize: 11, color: C.muted },

  btnGoogle:    { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8,
                  backgroundColor: C.surface, borderWidth: 1.5, borderColor: C.border,
                  borderRadius: 14, paddingVertical: 13, marginBottom: 20 },
  googleG:      { fontSize: 14, fontWeight: '800', color: '#4285F4' },
  btnGoogleTxt: { fontSize: 13, fontWeight: '500', color: C.text },

  loginRow:  { flexDirection: 'row', justifyContent: 'center', alignItems: 'center' },
  loginTxt:  { fontSize: 12, color: C.muted },
  loginLink: { fontSize: 12, fontWeight: '700', color: C.accent },
});