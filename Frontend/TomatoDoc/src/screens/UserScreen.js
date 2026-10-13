import React, { useContext } from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { AuthContext } from '../context/AuthContext';
import { UIThemeContext } from '../context/UIThemeContext';
import ScreenHeader from '../components/ScreenHeader';
import { palette as P, radius, shadow, type } from '../theme';

const C = {
  bg: P.bg,
  surface: P.surface,
  border: P.border,
  text: P.text,
  muted: P.muted,
  accent: P.forestMid,
};

function SettingRow({ icon, label, value, onPress }) {
  return (
    <TouchableOpacity style={styles.item} onPress={onPress} activeOpacity={0.8}>
      <View style={styles.itemIcon}>
        <MaterialCommunityIcons name={icon} size={20} color={P.forestMid} />
      </View>
      <Text style={styles.itemText}>{label}</Text>
      <View style={styles.valuePill}>
        <Text style={styles.valueText}>{value}</Text>
      </View>
    </TouchableOpacity>
  );
}

export default function UserScreen() {
  const { user, logout } = useContext(AuthContext);
  const { isDark, toggleTheme, presentationMode, togglePresentationMode } = useContext(UIThemeContext);
  const username = user?.name || 'TomatoDoc User';
  const email = user?.email || 'No email available';

  return (
    <View style={styles.root}>
      <ScreenHeader title="Profile" subtitle="Manage app preferences and your account session." eyebrow="Account" />

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.profileCard}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>{username.charAt(0).toUpperCase()}</Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.name} numberOfLines={1}>{username}</Text>
            <Text style={styles.email} numberOfLines={1}>{email}</Text>
          </View>
        </View>

        <Text style={[type.eyebrow, styles.sectionLabel]}>Preferences</Text>

        <SettingRow
          icon="theme-light-dark"
          label="Theme"
          value={isDark ? 'Dark' : 'Light'}
          onPress={toggleTheme}
        />
        <SettingRow
          icon="presentation"
          label="Presentation mode"
          value={presentationMode ? 'On' : 'Off'}
          onPress={togglePresentationMode}
        />

        <TouchableOpacity style={styles.logoutBtn} onPress={logout} activeOpacity={0.85}>
          <MaterialCommunityIcons name="logout" size={18} color={P.danger} />
          <Text style={styles.logoutTxt}>Log out</Text>
        </TouchableOpacity>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: C.bg },
  content: { padding: 18, paddingTop: 20, paddingBottom: 130 },

  profileCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: radius.lg,
    padding: 16,
    marginBottom: 22,
    ...shadow.card,
  },
  avatar: { width: 56, height: 56, borderRadius: 28, backgroundColor: P.forest, alignItems: 'center', justifyContent: 'center' },
  avatarText: { color: P.lime, fontWeight: '800', fontSize: 22 },
  name: { color: C.text, fontSize: 18, fontWeight: '800', letterSpacing: -0.3 },
  email: { color: C.muted, marginTop: 2, fontSize: 13 },

  sectionLabel: { marginBottom: 10 },
  item: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: radius.md,
    padding: 14,
    marginBottom: 10,
  },
  itemIcon: { width: 38, height: 38, borderRadius: 12, backgroundColor: P.surfaceTint, alignItems: 'center', justifyContent: 'center' },
  itemText: { flex: 1, color: C.text, fontWeight: '700', fontSize: 14 },
  valuePill: { backgroundColor: P.surface2, borderRadius: radius.pill, paddingHorizontal: 12, paddingVertical: 5 },
  valueText: { fontSize: 12, fontWeight: '700', color: C.muted },

  logoutBtn: {
    marginTop: 14,
    flexDirection: 'row',
    gap: 8,
    borderRadius: radius.md,
    borderWidth: 1.5,
    borderColor: P.dangerBorder,
    backgroundColor: P.dangerDim,
    padding: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoutTxt: { color: P.danger, fontWeight: '800', fontSize: 14 },
});
