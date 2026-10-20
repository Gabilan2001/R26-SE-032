import React, { useContext } from 'react';
import { ScrollView, StatusBar, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { AuthContext } from '../context/AuthContext';
import ScreenHeader from '../components/ScreenHeader';
import { palette as P, radius, shadow, type } from '../theme';
import appConfig from '../../app.json';

const C = {
  bg: P.bg,
  surface: P.surface,
  border: P.border,
  text: P.text,
  muted: P.muted,
  accent: P.forestMid,
};

function InfoRow({ icon, label, value, last }) {
  return (
    <View style={[styles.infoRow, !last && styles.infoRowDivider]}>
      <MaterialCommunityIcons name={icon} size={18} color={P.sprout} />
      <Text style={styles.infoLabel}>{label}</Text>
      <Text style={styles.infoValue} numberOfLines={1} selectable>{value}</Text>
    </View>
  );
}

export default function UserScreen() {
  const { user, logout } = useContext(AuthContext);
  const username = user?.name || 'TomatoDoc User';
  const email = user?.email || 'No email available';
  const userId = user?.id ? `#${String(user.id).slice(-8).toUpperCase()}` : 'Not available';

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" translucent backgroundColor="transparent" />
      <ScreenHeader title="Profile" subtitle="Your account details and session." eyebrow="Account" />

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

        <Text style={[type.eyebrow, styles.sectionLabel]}>Account information</Text>
        <View style={styles.infoCard}>
          <InfoRow icon="account-outline" label="Full name" value={username} />
          <InfoRow icon="email-outline" label="Email" value={email} />
          <InfoRow icon="identifier" label="User ID" value={userId} />
          <InfoRow icon="shield-check-outline" label="Sign-in method" value="Email and password" />
          <InfoRow icon="cellphone-information" label="App version" value={appConfig.expo.version} last />
        </View>

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
  infoCard: {
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: radius.lg,
    paddingHorizontal: 16,
    marginBottom: 22,
    ...shadow.card,
  },
  infoRow: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingVertical: 13 },
  infoRowDivider: { borderBottomWidth: 1, borderBottomColor: C.border },
  infoLabel: { color: C.muted, fontSize: 13, fontWeight: '600' },
  infoValue: { flex: 1, textAlign: 'right', color: C.text, fontSize: 13, fontWeight: '700' },
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
