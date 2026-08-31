import React from 'react';
import { Dimensions, StyleSheet, Text, View } from 'react-native';
import { LineChart } from 'react-native-chart-kit';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { C } from '../constants/priceTheme';

const screenWidth = Dimensions.get('window').width;

export default function ForecastChart({ data }) {
  if (!data) return null;

  const rawForecast =
    Array.isArray(data.weather_adjusted_forecast) && data.weather_adjusted_forecast.length
      ? data.weather_adjusted_forecast
      : Array.isArray(data.base_lstm_forecast)
      ? data.base_lstm_forecast
      : [];

  if (rawForecast.length === 0) return null;

  // Include baseline current price as point 0 if available
  const baseline = data.current_price_lkr;
  const chartPoints = baseline != null ? [baseline, ...rawForecast] : rawForecast;

  // Labels: Now, D2, D5, D8, D11, D14
  const labels =
    baseline != null
      ? ['Now', 'D2', 'D5', 'D8', 'D11', 'D14']
      : ['D1', 'D3', 'D6', 'D9', 'D12', 'D14'];

  const chartData = {
    labels: labels,
    datasets: [
      {
        data: chartPoints,
        color: (opacity = 1) => `rgba(245, 158, 11, ${opacity})`, // Amber line
        strokeWidth: 2.5,
      },
    ],
  };

  const chartConfig = {
    backgroundColor: C.surface,
    backgroundGradientFrom: C.surface,
    backgroundGradientTo: C.surface2,
    decimalPlaces: 0,
    color: (opacity = 1) => `rgba(240, 240, 240, ${opacity})`,
    labelColor: (opacity = 1) => `rgba(160, 160, 160, ${opacity})`,
    propsForDots: {
      r: '3.5',
      strokeWidth: '1.5',
      stroke: C.amber,
      fill: C.surface,
    },
    propsForBackgroundLines: {
      stroke: 'rgba(255, 255, 255, 0.05)',
      strokeDasharray: '4',
    },
  };

  const peakDay = data.peak_day || data.optimal_sell_day;
  const peakPrice = data.peak_price_lkr ? Math.round(data.peak_price_lkr) : null;

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.titleRow}>
          <MaterialCommunityIcons name="chart-bell-curve-cumulative" size={18} color={C.amber} />
          <Text style={styles.title}>14-Day Trajectory Curve</Text>
        </View>
        {peakPrice && (
          <View style={styles.peakBadge}>
            <Text style={styles.peakText}>
              Peak: {peakPrice} LKR (Day {peakDay || 1})
            </Text>
          </View>
        )}
      </View>

      <LineChart
        data={chartData}
        width={screenWidth - 32}
        height={180}
        chartConfig={chartConfig}
        bezier
        style={styles.chart}
        withInnerLines
        withOuterLines={false}
        withVerticalLines={false}
        yAxisSuffix=" LKR"
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginHorizontal: 16,
    marginBottom: 14,
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 16,
    padding: 12,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  title: {
    fontSize: 13,
    fontWeight: '700',
    color: C.text,
  },
  peakBadge: {
    backgroundColor: C.amberDim,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: C.amberBorder,
  },
  peakText: {
    fontSize: 10,
    fontWeight: '700',
    color: C.amber,
  },
  chart: {
    borderRadius: 12,
    marginVertical: 4,
  },
});
