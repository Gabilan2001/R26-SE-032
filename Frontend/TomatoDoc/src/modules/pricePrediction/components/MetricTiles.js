import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { C } from '../constants/priceTheme';

function formatRange(val, halfBandPct = 0.04) {
  if (val == null || isNaN(val)) return '—';
  const num = parseFloat(val);
  const delta = Math.max(5, Math.round(num * halfBandPct));
  return `${Math.round(num - delta)} – ${Math.round(num + delta)}`;
}

export default function MetricTiles({ data }) {
  if (!data) return null;

  const currentPrice = data.current_price_lkr != null ? Math.round(data.current_price_lkr) : '—';
  const day1Range = formatRange(data.day1_forecast_lkr, 0.035);
  const day14Range = formatRange(data.day14_forecast_lkr, 0.05);

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

      {/* Tomorrow (Day 1 Expected Range) */}
      <View style={styles.tile}>
        <Text style={styles.tileLabel}>Tomorrow (Expected)</Text>
        <View style={styles.priceRow}>
          <Text style={[styles.priceValueRange, { color: C.amber }]}>{day1Range}</Text>
          <Text style={styles.unit}>LKR/kg</Text>
        </View>
        <Text style={styles.tileSub} numberOfLines={1}>
          {data.forecast_start_date || 'Day 1 Range'}
        </Text>
      </View>

      {/* 14-Day Horizon Range */}
      <View style={[styles.tile, styles.tileHighlight]}>
        <Text style={styles.tileLabel}>14-Day Range</Text>
        <View style={styles.priceRow}>
          <Text style={[styles.priceValueRange, { color: trendColor }]}>{day14Range}</Text>
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
    fontSize: 9.5,
    fontWeight: '600',
    color: C.muted,
    textTransform: 'uppercase',
    letterSpacing: 0.2,
  },
  priceRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: 2,
    marginVertical: 2,
    flexWrap: 'wrap',
  },
  priceValue: {
    fontSize: 17,
    fontWeight: '800',
    color: C.text,
  },
  priceValueRange: {
    fontSize: 14,
    fontWeight: '800',
    color: C.text,
  },
  unit: {
    fontSize: 8.5,
    color: C.muted,
    fontWeight: '600',
  },
  tileSub: {
    fontSize: 9.5,
    color: C.muted,
    fontWeight: '500',
  },
});
