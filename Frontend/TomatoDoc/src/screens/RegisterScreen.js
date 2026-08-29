import React, { useContext, useRef, useState, useEffect } from 'react';
import {
  ActivityIndicator,
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
  dangerDim: 'rgba(255,92,92,0.12)',
  success: '#4adf6f',
};

function getStrength(pass) {
  if (!pass) return 0;
  let s = 0;
  if (pass.length >= 8) s++;
  if (/[A-Z]/.test(pass) || /\d/.test(pass)) s++;
  if (/[^A-Za-z0-9]/.test(pass)) s++;
  return s;
}

const STRENGTH_META = [
  null,
  { label: 'Weak', color: C.danger },
  { label: 'Fair', color: C.accent },
  { label: 'Strong', color: C.success },
];

function StrengthBars({ password }) {
  const str = getStrength(password);
  if (!password) return null;
  const meta = STRENGTH_META[str];
  return (
    <View style={styles.strengthWrap}>
      <View style={styles.strengthRow}>
        {[0, 1, 2].map((i) => (
          <View
            key={i}
            style={[styles.strengthBar, i < str && { backgroundColor: meta?.color ?? C.border }]}
          />
        ))}
      </View>
      {meta && <Text style={[styles.strengthLabel, { color: meta.color }]}>{meta.label}</Text>}
    </View>
  );
}

function InputField({
  label,
  icon,
  value,
  onChangeText,
  placeholder,
  secureTextEntry,
  keyboardType,
  autoCapitalize,
  rightElement,
}) {
  return (
    <View style={styles.fieldGroup}>
      <Text style={styles.label}>{label}</Text>
      <View style={styles.inputWrap}>
        <View style={styles.inputIconBox}>
          <MaterialCommunityIcons name={icon} size={18} color={C.accent} />
        </View>
        <TextInput
          style={[styles.input, rightElement && { paddingRight: 44 }]}
          placeholder={placeholder}
          placeholderTextColor={C.muted}
          value={value}
          onChangeText={onChangeText}
          autoCapitalize={autoCapitalize}
          keyboardType={keyboardType}
          secureTextEntry={secureTextEntry}
          selectionColor={C.accent}
        />
        {rightElement}
      </View>
    </View>
  );
}

export default function RegisterScreen({ navigation }) {
  const { register } = useContext(AuthContext);
  const insets = useSafeAreaInsets();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [terms, setTerms] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const isReady = name.trim() && email.trim() && password.length >= 6 && terms;

  const slideY = useRef(new Animated.Value(32)).current;
  const opacity = useRef(new Animated.Value(0)).current;
  const btnScale = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.spring(slideY, { toValue: 0, useNativeDriver: true, delay: 120 }),
      Animated.timing(opacity, { toValue: 1, duration: 400, delay: 120, useNativeDriver: true }),
    ]).start();
  }, []);

  const onPressIn = () => Animated.spring(btnScale, { toValue: 0.97, useNativeDriver: true }).start();
  const onPressOut = () => Animated.spring(btnScale, { toValue: 1, useNativeDriver: true }).start();

  const onRegister = async () => {
    if (!isReady) {
      setError('Please complete all fields and accept the terms.');
      return;
    }
    try {
      setError('');
      setLoading(true);
      await register(name.trim(), email.trim(), password);
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
        contentContainerStyle={[
          styles.scroll,
          { paddingTop: insets.top + 16, paddingBottom: insets.bottom + 32 },
        ]}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        {/* Back */}
        <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()} activeOpacity={0.7}>
          <MaterialCommunityIcons name="arrow-left" size={20} color={C.text} />
        </TouchableOpacity>

        {/* Hero */}
        <View style={styles.hero}>
          <View style={styles.logoRow}>
            <View style={styles.logoBox}>
              <MaterialCommunityIcons name="account-plus-outline" size={24} color="#0f0f0f" />
            </View>
            <View style={styles.badge}>
              <View style={styles.badgeDot} />
              <Text style={styles.badgeText}>New account</Text>
            </View>
          </View>

          <Text style={styles.heroTitle}>
            Join{'\n'}
            <Text style={styles.heroAccent}>TomatoDoc</Text>
          </Text>
          <Text style={styles.heroSub}>
            Create an account to save scans, track crop health, and access treatment plans.
          </Text>
        </View>

        {/* Form */}
        <Animated.View style={[styles.formCard, { opacity, transform: [{ translateY: slideY }] }]}>
          <Text style={styles.formTitle}>Create account</Text>

          {!!error && (
            <View style={styles.errorBox}>
              <MaterialCommunityIcons name="alert-circle-outline" size={18} color={C.danger} />
              <Text style={styles.errorText}>{error}</Text>
            </View>
          )}

          <InputField
            label="Full name"
            icon="account-outline"
            value={name}
            onChangeText={setName}
            placeholder="Your name"
            autoCapitalize="words"
          />

          <InputField
            label="Email"
            icon="email-outline"
            value={email}
            onChangeText={setEmail}
            placeholder="you@example.com"
            keyboardType="email-address"
            autoCapitalize="none"
          />

          <InputField
            label="Password"
            icon="lock-outline"
            value={password}
            onChangeText={setPassword}
            placeholder="Minimum 6 characters"
            secureTextEntry={!showPass}
            rightElement={
              <TouchableOpacity
                style={styles.eyeBtn}
                onPress={() => setShowPass((v) => !v)}
                hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
              >
                <MaterialCommunityIcons
                  name={showPass ? 'eye-off-outline' : 'eye-outline'}
                  size={20}
                  color={C.muted}
                />
              </TouchableOpacity>
            }
          />

          <StrengthBars password={password} />

          {/* Terms */}
          <TouchableOpacity style={styles.termsRow} onPress={() => setTerms((t) => !t)} activeOpacity={0.8}>
            <View style={[styles.termsCheck, terms && styles.termsCheckActive]}>
              {terms && (
                <MaterialCommunityIcons name="check" size={14} color="#0f0f0f" />
              )}
            </View>
            <Text style={styles.termsText}>
              I agree to the <Text style={styles.termsLink}>Terms of Service</Text> and{' '}
              <Text style={styles.termsLink}>Privacy Policy</Text>
            </Text>
          </TouchableOpacity>

          <Animated.View style={{ transform: [{ scale: btnScale }] }}>
            <Pressable
              style={[styles.btnPrimary, (!isReady || loading) && styles.btnPrimaryDisabled]}
              onPressIn={onPressIn}
              onPressOut={onPressOut}
              onPress={onRegister}
              disabled={!isReady || loading}
            >
              {loading ? (
                <ActivityIndicator color="#0f0f0f" size="small" />
              ) : (
                <>
                  <MaterialCommunityIcons name="account-check-outline" size={20} color="#0f0f0f" style={styles.btnIcon} />
                  <Text style={styles.btnPrimaryText}>Create account</Text>
                </>
              )}
            </Pressable>
          </Animated.View>

          <View style={styles.divider}>
            <View style={styles.dividerLine} />
            <Text style={styles.dividerText}>or</Text>
            <View style={styles.dividerLine} />
          </View>

          <TouchableOpacity style={styles.btnSecondary} activeOpacity={0.85}>
            <MaterialCommunityIcons name="google" size={18} color="#4285F4" />
            <Text style={styles.btnSecondaryText}>Continue with Google</Text>
          </TouchableOpacity>

          <View style={styles.loginRow}>
            <Text style={styles.loginText}>Already have an account?</Text>
            <TouchableOpacity onPress={() => navigation.goBack()}>
              <Text style={styles.loginLink}>Sign in</Text>
            </TouchableOpacity>
          </View>
        </Animated.View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: C.bg },
  scroll: { flexGrow: 1, paddingHorizontal: 24 },

  backBtn: {
    width: 40,
    height: 40,
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
  },

  hero: { marginBottom: 24 },
  logoRow: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 20 },
  logoBox: {
    width: 48,
    height: 48,
    borderRadius: 14,
    backgroundColor: C.accent,
    alignItems: 'center',
    justifyContent: 'center',
  },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: C.accentDim,
    borderWidth: 1,
    borderColor: C.accentBorder,
    borderRadius: 100,
    paddingHorizontal: 12,
    paddingVertical: 5,
  },
  badgeDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: C.accent, marginRight: 6 },
  badgeText: { fontSize: 11, fontWeight: '600', color: C.accent, letterSpacing: 0.4 },
  heroTitle: { fontSize: 30, fontWeight: '800', color: C.text, lineHeight: 36, marginBottom: 10 },
  heroAccent: { color: C.accent },
  heroSub: { fontSize: 14, color: C.muted, lineHeight: 21 },

  formCard: {
    backgroundColor: C.surface,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: C.border,
    padding: 22,
  },
  formTitle: { fontSize: 17, fontWeight: '700', color: C.text, marginBottom: 20 },

  errorBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    backgroundColor: C.dangerDim,
    borderWidth: 1,
    borderColor: 'rgba(255,92,92,0.2)',
    borderRadius: 10,
    padding: 12,
    marginBottom: 16,
  },
  errorText: { flex: 1, fontSize: 13, color: C.danger, lineHeight: 18 },

  fieldGroup: { marginBottom: 16 },
  label: { fontSize: 12, fontWeight: '600', color: C.muted, marginBottom: 8, letterSpacing: 0.3 },
  inputWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: C.surface2,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 12,
    overflow: 'hidden',
  },
  inputIconBox: {
    width: 46,
    height: 48,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: C.accentDim,
    borderRightWidth: 1,
    borderRightColor: C.border,
  },
  input: { flex: 1, paddingHorizontal: 14, paddingVertical: 14, color: C.text, fontSize: 15 },
  eyeBtn: { paddingRight: 14 },

  strengthWrap: { marginTop: -4, marginBottom: 8 },
  strengthRow: { flexDirection: 'row', gap: 4 },
  strengthBar: { flex: 1, height: 3, borderRadius: 2, backgroundColor: C.surface2 },
  strengthLabel: { fontSize: 10, fontWeight: '700', textAlign: 'right', marginTop: 6 },

  termsRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 10, marginBottom: 20, marginTop: 4 },
  termsCheck: {
    width: 20,
    height: 20,
    borderRadius: 6,
    borderWidth: 1.5,
    borderColor: C.border,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 1,
  },
  termsCheckActive: { backgroundColor: C.accent, borderColor: C.accent },
  termsText: { flex: 1, fontSize: 12, color: C.muted, lineHeight: 18 },
  termsLink: { color: C.accent, fontWeight: '700' },

  btnPrimary: {
    flexDirection: 'row',
    backgroundColor: C.accent,
    borderRadius: 12,
    paddingVertical: 15,
    alignItems: 'center',
    justifyContent: 'center',
  },
  btnPrimaryDisabled: { opacity: 0.35 },
  btnIcon: { marginRight: 8 },
  btnPrimaryText: { fontSize: 15, fontWeight: '700', color: '#0f0f0f', letterSpacing: 0.2 },

  divider: { flexDirection: 'row', alignItems: 'center', marginVertical: 20, gap: 12 },
  dividerLine: { flex: 1, height: 1, backgroundColor: C.border },
  dividerText: { fontSize: 12, color: C.muted },

  btnSecondary: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    backgroundColor: C.surface2,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 12,
    paddingVertical: 14,
  },
  btnSecondaryText: { fontSize: 14, fontWeight: '500', color: C.text },

  loginRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 6,
    marginTop: 22,
  },
  loginText: { fontSize: 13, color: C.muted },
  loginLink: { fontSize: 13, fontWeight: '700', color: C.accent },
});
