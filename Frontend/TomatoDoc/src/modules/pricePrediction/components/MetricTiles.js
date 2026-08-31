import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { C } from '../constants/priceTheme';

export default function MetricTiles({ data }) {
  if (!data) return null;

  const currentPrice = data.current_price_lkr != null ? Math.round(data.current_price_lkr) : '—';
  const day1Price = data.day1_forecast_lkr != null ? Math.round(data.day1_forecast_lkr) : '—';
  const day14Price = data.day14_forecast_lkr != null ? Math.round(data.day14_forecast_lkr) : '—';

  const baseline = data.current_price_lkr || (data.base_lstm_forecast && data.base_lstm_forecast[0]);
  const totalChgPct =
    baseline && data.day14_forecast_lkr
      ? ((data.day14_forecast_lkr - baseline) / baseline) * 100
      : 0;

  let trendIcon = '➡️';
  let trendColor = C.blue;
  if (totalChgPct > 2.0) {
    trendIcon = '📈';
    trendColor = C.emerald;
  } else if (totalChgPct < -2.0) {
    trendIcon = '📉';
    trendColor = C.red;
  }

  const chgSign = totalChgPct >= 0 ? '+' : '';
  const chgStr = `${chgSign}${totalChgPct.toFixed(1)}%`;

  return (
    <View style={styles.grid}>
      {/* Current Price */}
      <View style={styles.tile}>
        <Text style={styles.tileLabel}>Current Price</Text>
        <View style={styles.priceRow}>
          <Text style={styles.priceValue}>{currentPrice}</Text>
          <Text style={styles.unit}>LKR/kg</Text>
        </View>
        <Text style={styles.tileSub} numberOfLines={1}>
          As of {data.data_as_of_date || 'latest'}
        </Text>
      </View>

      {/* Tomorrow (Day 1) */}
      <View style={styles.tile}>
        <Text style={styles.tileLabel}>Tomorrow</Text>
        <View style={styles.priceRow}>
          <Text style={[styles.priceValue, { color: C.amber }]}>{day1Price}</Text>
          <Text style={styles.unit}>LKR/kg</Text>
        </View>
        <Text style={styles.tileSub} numberOfLines={1}>
          {data.forecast_start_date || 'Day 1'}
        </Text>
      </View>

      {/* 14-Day Horizon */}
      <View style={[styles.tile, styles.tileHighlight]}>
        <Text style={styles.tileLabel}>14-Day Horizon</Text>
        <View style={styles.priceRow}>
          <Text style={[styles.priceValue, { color: trendColor }]}>{day14Price}</Text>
          <Text style={styles.unit}>LKR/kg</Text>
        </View>
        <Text style={[styles.tileSub, { color: trendColor }]} numberOfLines={1}>
          {trendIcon} {chgStr} ({data.forecast_end_date ? data.forecast_end_date.slice(5) : 'Day 14'})
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  grid: {
    flexDirection: 'row',
    gap: 8,
    marginHorizontal: 16,
    marginBottom: 14,
  },
  tile: {
    flex: 1,
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 14,
    padding: 10,
    justifyContent: 'space-between',
    minHeight: 88,
  },
  tileHighlight: {
    borderColor: C.borderLight,
    backgroundColor: C.surface2,
  },
  tileLabel: {
    fontSize: 10,
    fontWeight: '600',
    color: C.muted,
    textTransform: 'uppercase',
    letterSpacing: 0.3,
  },
  priceRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: 3,
    marginVertical: 2,
  },
  priceValue: {
    fontSize: 17,
    fontWeight: '800',
    color: C.text,
  },
  unit: {
    fontSize: 9,
    color: C.muted,
    fontWeight: '600',
  },
  tileSub: {
    fontSize: 10,
    color: C.muted,
    fontWeight: '500',
  },
});
