import React, { useContext, useEffect, useState } from 'react';
import { Dimensions, ScrollView, StyleSheet } from 'react-native';
import { Card, Text } from 'react-native-paper';
import { BarChart, LineChart, PieChart } from 'react-native-chart-kit';
import { getStats } from '../api/historyApi';
import { AuthContext } from '../context/AuthContext';
import { colors } from '../constants/colors';

const width = Dimensions.get('window').width - 32;
const chartConfig = {
  backgroundGradientFrom: '#fff',
  backgroundGradientTo: '#fff',
  decimalPlaces: 0,
  color: (o = 1) => `rgba(46, 125, 50, ${o})`,
  labelColor: () => '#333',
};

export default function StatsScreen() {
  const { token } = useContext(AuthContext);
  const [stats, setStats] = useState({ total_scans: 0, most_common_deficiency: 'N/A', class_counts: {}, scans_per_day: [] });

  useEffect(() => {
    (async () => {
      const res = await getStats(token);
      setStats(res.data);
    })();
  }, [token]);

  const labels = Object.keys(stats.class_counts);
  const values = Object.values(stats.class_counts);
  const pieData = labels.map((l, i) => ({
    name: l,
    population: values[i],
    color: i % 2 === 0 ? '#2E7D32' : '#81C784',
    legendFontColor: '#444',
    legendFontSize: 12,
  }));

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Scan Statistics</Text>
      <Card style={styles.card}><Card.Content><Text>Total scans: {stats.total_scans}</Text><Text>Most common: {stats.most_common_deficiency}</Text></Card.Content></Card>
      {labels.length > 0 ? <BarChart data={{ labels, datasets: [{ data: values }] }} width={width} height={220} chartConfig={chartConfig} fromZero /> : null}
      {pieData.length > 0 ? <PieChart data={pieData} width={width} height={220} chartConfig={chartConfig} accessor="population" backgroundColor="transparent" /> : null}
      {stats.scans_per_day.length > 0 ? <LineChart data={{ labels: stats.scans_per_day.map((d) => d.date.slice(5)), datasets: [{ data: stats.scans_per_day.map((d) => d.count) }] }} width={width} height={220} chartConfig={chartConfig} fromZero /> : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  content: { padding: 16, gap: 12 },
  title: { fontSize: 24, fontWeight: '700', color: colors.primary },
  card: { borderRadius: 16, backgroundColor: colors.white },
});
