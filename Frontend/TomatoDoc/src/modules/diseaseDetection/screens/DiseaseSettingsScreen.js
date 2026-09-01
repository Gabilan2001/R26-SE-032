import React, { useState } from 'react';
import {
  StatusBar,
  StyleSheet,
  Switch,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { getSkipBgRemoval, setSkipBgRemoval } from '../config/devSettings';

const C = {
  bg:           '#F8F7F2',
  card:         '#FFFFFF',
  text:         '#24352A',
  muted:        '#68756B',
  border:       'rgba(36,53,42,0.10)',
  leaf:         '#3F7D45',
};

// Not linked from any tab -- reached only via the small gear icon on
// DiseaseScanScreen. Testing/dev knobs only, kept off the main flow.
export default function DiseaseSettingsScreen({ navigation }) {
  const insets = useSafeAreaInsets();
  // Background removal is OFF by default (skipBgRemoval starts true) --
  // faster scans without needing rembg. This toggle's own value is the
  // inverse of skipBgRemoval so it reads naturally as "turn ON to remove
  // the background", not "turn ON to skip it".
  const [bgRemovalOn, setBgRemovalOn] = useState(!getSkipBgRemoval());

  const onToggle = (enabled) => {
    setBgRemovalOn(enabled);
    setSkipBgRemoval(!enabled);
  };

  return (
    <View style={[styles.root, { paddingTop: insets.top + 18, paddingBottom: insets.bottom + 18 }]}>
      <StatusBar barStyle="dark-content" backgroundColor={C.bg} />
      <View style={styles.backRow}>
        <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()}>
          <Text style={styles.backArrow}>←</Text>
        </TouchableOpacity>
        <Text style={styles.screenTitle}>Scan Settings</Text>
      </View>

      <View style={styles.row}>
        <View style={{ flex: 1 }}>
          <Text style={styles.rowTitle}>Background removal</Text>
          <Text style={styles.rowSub}>
            Off by default -- faster scans. Turn on to remove the background
            (rembg) before detection. Resets to off every time the app restarts.
          </Text>
        </View>
        <Switch
          value={bgRemovalOn}
          onValueChange={onToggle}
          trackColor={{ false: C.border, true: C.leaf }}
          thumbColor="#fff"
        />
      </View>

      {!bgRemovalOn && (
        <Text style={styles.activeNote}>
          ⚠ Background removal is currently OFF for scans in this session.
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  root:    { flex: 1, backgroundColor: C.bg, padding: 18 },
  backRow: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 20, paddingTop: 4 },
  backBtn: { width: 32, height: 32, backgroundColor: C.card, borderWidth: 1, borderColor: C.border, borderRadius: 16, alignItems: 'center', justifyContent: 'center' },
  backArrow: { fontSize: 15, color: C.text },
  screenTitle: { fontSize: 18, fontWeight: '800', color: C.text },

  row: {
    flexDirection: 'row', alignItems: 'center', gap: 14,
    backgroundColor: C.card, borderWidth: 1, borderColor: C.border,
    borderRadius: 16, padding: 16,
    shadowColor: '#24352A', shadowOpacity: 0.05, shadowRadius: 8, shadowOffset: { width: 0, height: 3 }, elevation: 2,
  },
  rowTitle: { fontSize: 14, fontWeight: '700', color: C.text, marginBottom: 4 },
  rowSub:   { fontSize: 11.5, color: C.muted, lineHeight: 16 },

  activeNote: { fontSize: 11.5, color: C.leaf, marginTop: 12, lineHeight: 16 },
});
