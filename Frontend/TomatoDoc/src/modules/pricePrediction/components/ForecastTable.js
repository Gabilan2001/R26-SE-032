import React, { useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { C } from '../constants/priceTheme';

export default function ForecastTable({ data }) {
  const [showAllDays, setShowAllDays] = useState(false);

  if (!data) return null;

  const prices =
    Array.isArray(data.weather_adjusted_forecast) && data.weather_adjusted_forecast.length
      ? data.weather_adjusted_forecast
      : Array.isArray(data.predicted_prices)
      ? data.predicted_prices.map((p) => parseFloat(p))
      : [];

  if (prices.length === 0) return null;

  const dates = data.forecast_dates || [];
  const baseline = data.current_price_lkr || prices[0];

  const milestoneIndices = [0, 2, 6, prices.length - 1].filter(
    (idx) => idx >= 0 && idx < prices.length
  );
  const displayIndices = showAllDays
    ? Array.from({ length: prices.length }, (_, i) => i)
    : milestoneIndices;

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Day-by-Day Forecast</Text>
          <Text style={styles.subTitle}>
            {data.forecast_period_label || 'Next 14-day projection'}
          </Text>
        </View>
        <TouchableOpacity
          style={styles.toggleBtn}
          onPress={() => setShowAllDays((prev) => !prev)}
          activeOpacity={0.7}
        >
          <Text style={styles.toggleText}>
            {showAllDays ? 'Key Milestones' : 'Show All 14 Days'}
          </Text>
        </TouchableOpacity>
      </View>

      <View style={styles.table}>
        <View style={styles.tableHeaderRow}>
          <Text style={[styles.th, { flex: 1.4 }]}>Forecast Day</Text>
          <Text style={[styles.th, { flex: 1.2, textAlign: 'center' }]}>Expected</Text>
          <Text style={[styles.th, { flex: 1, textAlign: 'right' }]}>Daily Trend</Text>
        </View>

        {displayIndices.map((i) => {
          const currentVal = prices[i];
          const prevVal = i === 0 ? baseline : prices[i - 1];
          const diffPct =
            prevVal && currentVal ? ((currentVal - prevVal) / prevVal) * 100 : 0;

          let trendIcon = '➡️';
          let trendColor = C.muted;
          if (diffPct > 0.5) {
            trendIcon = '📈';
            trendColor = C.emerald;
          } else if (diffPct < -0.5) {
            trendIcon = '📉';
            trendColor = C.red;
          }

          const sign = diffPct >= 0 ? '+' : '';
          const diffStr = `${sign}${diffPct.toFixed(1)}%`;
          const dateStr = dates[i] || '';
          const dayLabel = i === 0 ? 'Day 1 (Tomorrow)' : `Day ${i + 1}`;

          return (
            <View key={`day-${i}`} style={styles.tableRow}>
              <View style={{ flex: 1.4 }}>
                <Text style={styles.dayText}>{dayLabel}</Text>
                {dateStr ? <Text style={styles.dateText}>{dateStr}</Text> : null}
              </View>
              <Text style={[styles.priceText, { flex: 1.2, textAlign: 'center' }]}>
                {Math.round(currentVal)} LKR
              </Text>
              <View style={[styles.trendCell, { flex: 1 }]}>
                <Text style={[styles.trendText, { color: trendColor }]}>
                  {trendIcon} {diffStr}
                </Text>
              </View>
            </View>
          );
        })}
      </View>

      <Text style={styles.provenanceNote}>
        Model trained on historical price data from {data.dataset_coverage || 'Aug 2016 to Aug 2026'}.
      </Text>
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
    padding: 14,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  title: {
    fontSize: 13,
    fontWeight: '700',
    color: C.text,
  },
  subTitle: {
    fontSize: 10,
    color: C.muted,
    marginTop: 1,
  },
  toggleBtn: {
    backgroundColor: C.amberDim,
    borderWidth: 1,
    borderColor: C.amberBorder,
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  toggleText: {
    fontSize: 10,
    fontWeight: '700',
    color: C.amber,
  },
  table: {
    borderRadius: 10,
    overflow: 'hidden',
  },
  tableHeaderRow: {
    flexDirection: 'row',
    backgroundColor: C.surface2,
    paddingHorizontal: 10,
    paddingVertical: 7,
    borderRadius: 8,
    marginBottom: 4,
  },
  th: {
    fontSize: 10,
    fontWeight: '700',
    color: C.muted,
    textTransform: 'uppercase',
  },
  tableRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.04)',
  },
  dayText: {
    fontSize: 12,
    fontWeight: '600',
    color: C.text,
  },
  dateText: {
    fontSize: 9.5,
    color: C.muted,
  },
  priceText: {
    fontSize: 13,
    fontWeight: '700',
    color: C.text,
  },
  trendCell: {
    alignItems: 'flex-end',
  },
  trendText: {
    fontSize: 11,
    fontWeight: '600',
  },
  provenanceNote: {
    fontSize: 9.5,
    color: C.muted,
    textAlign: 'center',
    marginTop: 10,
    fontStyle: 'italic',
  },
});
