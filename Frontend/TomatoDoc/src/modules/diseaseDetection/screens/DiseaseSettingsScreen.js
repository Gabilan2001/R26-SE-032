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
import ScreenHeader from '../../../components/ScreenHeader';
import { palette as P, radius, shadow } from '../../../theme';

const C = {
  bg:           P.bg,
  card:         P.surface,
  text:         P.text,
  muted:        P.muted,
  border:       P.border,
  leaf:         P.forestMid,
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
    <View style={[styles.root, { paddingBottom: insets.bottom + 18 }]}>
      <StatusBar barStyle="light-content" backgroundColor={P.forest} />
      <ScreenHeader
        title="Scan Settings"
        subtitle="Testing options for the disease scanner"
        eyebrow="Disease module"
        onBack={() => navigation.goBack()}
      />

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
  root:    { flex: 1, backgroundColor: C.bg },

  row: {
    flexDirection: 'row', alignItems: 'center', gap: 14,
    backgroundColor: C.card, borderWidth: 1, borderColor: C.border,
    borderRadius: radius.lg, padding: 16, margin: 18, ...shadow.card,
  },
  rowTitle: { fontSize: 14, fontWeight: '800', color: C.text, marginBottom: 4 },
  rowSub:   { fontSize: 12, color: C.muted, lineHeight: 17 },

  activeNote: { fontSize: 12, color: C.leaf, marginHorizontal: 22, lineHeight: 17 },
});
