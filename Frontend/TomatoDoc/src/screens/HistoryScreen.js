import React, { useContext, useEffect, useState } from 'react';
import { ScrollView, StyleSheet } from 'react-native';
import { Chip, List, Text } from 'react-native-paper';
import { AuthContext } from '../context/AuthContext';
import { getHistory } from '../api/historyApi';
import { formatDateTime } from '../utils/formatters';
import { colors } from '../constants/colors';

export default function HistoryScreen({ navigation }) {
  const { token } = useContext(AuthContext);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    const unsub = navigation.addListener('focus', async () => {
      const res = await getHistory(token);
      setHistory(res.data.history || []);
    });
    return unsub;
  }, [navigation, token]);

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Scan History</Text>
      {history.map((item) => (
        <List.Item
          key={item._id}
          title={`${item.class_name} (${item.confidence}%)`}
          description={formatDateTime(item.created_at)}
          right={() => <Chip style={{ backgroundColor: item.class_name === 'Healthy' ? '#D0F0D2' : '#FFEBEE' }}>{item.class_name === 'Healthy' ? 'Healthy' : 'Deficiency'}</Chip>}
          onPress={() => navigation.navigate('Result', { result: {
            class: item.class_name,
            confidence: item.confidence,
            description: item.description,
            symptoms: item.symptoms,
            solution: item.solution,
            fertilizer: item.fertilizer,
          }, imageUri: item.image_uri || null })}
        />
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  content: { padding: 16 },
  title: { fontSize: 24, fontWeight: '700', color: colors.primary, marginBottom: 12 },
});
