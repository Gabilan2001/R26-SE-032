import React, { useContext } from 'react';
import { ScrollView, StyleSheet, View } from 'react-native';
import { Button, Text } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import OptionCard from '../components/OptionCard';
import { colors } from '../constants/colors';
import { AuthContext } from '../context/AuthContext';

export default function HomeScreen({ navigation }) {
  const { logout } = useContext(AuthContext);
  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <MaterialCommunityIcons name="fruit-cherries" size={42} color={colors.primary} />
        <Text style={styles.title}>TomatoDoc</Text>
      </View>
      <Text style={styles.subtitle}>Smart tomato farming assistant</Text>
      <OptionCard title="Price Forecasting" icon="finance" locked />
      <OptionCard title="Nutrient Deficiency" icon="leaf" onPress={() => navigation.navigate('Scan')} />
      <OptionCard title="Disease in Leaf" icon="virus" locked />
      <OptionCard title="Disease in Tomato" icon="food-apple" locked />
      <Button mode="outlined" onPress={logout} style={styles.logout}>Logout</Button>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  content: { padding: 16 },
  header: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  title: { fontSize: 28, fontWeight: '800', color: colors.primary },
  subtitle: { marginBottom: 20, color: colors.text },
  logout: { marginTop: 20, borderColor: colors.primary },
});
