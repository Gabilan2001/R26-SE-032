import React, { useState } from 'react';
import {
  StatusBar,
  StyleSheet,
  Switch,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { getSkipBgRemoval, setSkipBgRemoval } from '../config/devSettings';

const C = {
  bg:           '#0f0f0f',
  surface:      '#1a1a1a',
  text:         '#f0f0f0',
  muted:        '#666666',
  border:       'rgba(255,255,255,0.07)',
  amber:        '#f5a623',
};

// Not linked from any tab -- reached only via the small gear icon on
// DiseaseScanScreen. Testing/dev knobs only, kept off the main flow.
export default function DiseaseSettingsScreen({ navigation }) {
  const [skipBg, setSkipBg] = useState(getSkipBgRemoval());

  const onToggle = (value) => {
    setSkipBg(value);
    setSkipBgRemoval(value);
  };

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" backgroundColor={C.bg} />
      <View style={styles.backRow}>
        <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()}>
          <Text style={styles.backArrow}>←</Text>
        </TouchableOpacity>
        <Text style={styles.screenTitle}>Scan Settings</Text>
      </View>

      <View style={styles.row}>
        <View style={{ flex: 1 }}>
          <Text style={styles.rowTitle}>Skip background removal</Text>
          <Text style={styles.rowSub}>
            Testing only -- compares detection with vs. without the rembg
            step. Resets to off every time the app restarts.
          </Text>
        </View>
        <Switch
          value={skipBg}
          onValueChange={onToggle}
          trackColor={{ false: C.border, true: C.amber }}
          thumbColor="#fff"
        />
      </View>

      {skipBg && (
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
  backBtn: { width: 32, height: 32, backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: 16, alignItems: 'center', justifyContent: 'center' },
  backArrow: { fontSize: 15, color: C.text },
  screenTitle: { fontSize: 18, fontWeight: '800', color: C.text },

  row: {
    flexDirection: 'row', alignItems: 'center', gap: 14,
    backgroundColor: C.surface, borderWidth: 1, borderColor: C.border,
    borderRadius: 16, padding: 16,
  },
  rowTitle: { fontSize: 14, fontWeight: '700', color: C.text, marginBottom: 4 },
  rowSub:   { fontSize: 11.5, color: C.muted, lineHeight: 16 },

  activeNote: { fontSize: 11.5, color: C.amber, marginTop: 12, lineHeight: 16 },
});
