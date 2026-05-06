import React, { useContext } from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { AuthContext } from '../context/AuthContext';
import { UIThemeContext } from '../context/UIThemeContext';

const C = {
  bg: '#0f0f0f',
  surface: '#1a1a1a',
  border: 'rgba(255,255,255,0.07)',
  text: '#f0f0f0',
  muted: '#777',
  accent: '#c8f135',
};

export default function UserScreen() {
  const { user, logout } = useContext(AuthContext);
  const { isDark, toggleTheme, presentationMode, togglePresentationMode } = useContext(UIThemeContext);
  const username = user?.name || 'TomatoDoc User';
  const email = user?.email || 'No email available';

  return (
    <ScrollView style={styles.root} contentContainerStyle={styles.content}>
      <View style={styles.card}>
        <Text style={styles.title}>User Panel</Text>
        <Text style={styles.sub}>Manage app preferences and account session.</Text>
      </View>
      <View style={styles.profileCard}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>{username.charAt(0).toUpperCase()}</Text>
        </View>
        <View style={{ flex: 1 }}>
          <Text style={styles.name}>{username}</Text>
          <Text style={styles.email}>{email}</Text>
        </View>
      </View>

      <TouchableOpacity style={styles.item} onPress={toggleTheme}>
        <Text style={styles.itemText}>Theme: {isDark ? 'Dark' : 'Light'}</Text>
      </TouchableOpacity>

      <TouchableOpacity style={styles.item} onPress={togglePresentationMode}>
        <Text style={styles.itemText}>Presentation Mode: {presentationMode ? 'On' : 'Off'}</Text>
      </TouchableOpacity>

      <TouchableOpacity style={styles.logoutBtn} onPress={logout}>
        <Text style={styles.logoutTxt}>Logout</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: C.bg },
  content: { padding: 18, paddingBottom: 28 },
  card: { backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: 16, padding: 14, marginBottom: 12 },
  profileCard: { flexDirection: 'row', alignItems: 'center', gap: 12, backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: 16, padding: 14, marginBottom: 12 },
  avatar: { width: 46, height: 46, borderRadius: 23, backgroundColor: C.accent, alignItems: 'center', justifyContent: 'center' },
  avatarText: { color: '#0f0f0f', fontWeight: '800', fontSize: 18 },
  name: { color: C.text, fontSize: 17, fontWeight: '800' },
  email: { color: C.muted, marginTop: 2 },
  title: { color: C.text, fontSize: 20, fontWeight: '800' },
  sub: { color: C.muted, marginTop: 4 },
  item: { backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: 14, padding: 14, marginBottom: 10 },
  itemText: { color: C.text, fontWeight: '600' },
  logoutBtn: { marginTop: 8, borderRadius: 14, borderWidth: 1.5, borderColor: C.accent, padding: 14, alignItems: 'center' },
  logoutTxt: { color: C.accent, fontWeight: '700' },
});

