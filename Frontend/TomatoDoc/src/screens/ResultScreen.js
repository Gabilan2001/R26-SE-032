import React, { useContext, useState } from 'react';
import { ScrollView, StyleSheet } from 'react-native';
import { Button, Text } from 'react-native-paper';
import ResultCard from '../components/ResultCard';
import { saveHistory } from '../api/historyApi';
import { AuthContext } from '../context/AuthContext';
import { isLowConfidence } from '../utils/formatters';
import { colors } from '../constants/colors';

export default function ResultScreen({ route, navigation }) {
  const { token } = useContext(AuthContext);
  const { result, imageUri } = route.params;
  const [saved, setSaved] = useState(false);

  const onSave = async () => {
    await saveHistory(token, { ...result, image_uri: imageUri });
    setSaved(true);
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <ResultCard result={result} />
      {isLowConfidence(result.confidence) ? (
        <Text style={styles.warning}>Warning: Confidence is below 70%. Please re-scan in better lighting.</Text>
      ) : null}
      <Button mode="contained" style={styles.mt} onPress={() => navigation.navigate('Detail', { className: result.class })}>View Full Detail</Button>
      <Button mode="outlined" style={styles.mt} onPress={onSave} disabled={saved}>{saved ? 'Saved to History' : 'Save to History'}</Button>
      <Button mode="text" style={styles.mt} onPress={() => navigation.navigate('Scan')}>Analyze Another</Button>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  content: { padding: 16 },
  mt: { marginTop: 12 },
  warning: { marginTop: 12, color: colors.accent, fontWeight: '600' },
});
