import React, { useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { C } from '../constants/priceTheme';

export default function TechnicalDetailsCard({ data }) {
  const [expanded, setExpanded] = useState(false);

  if (!data) return null;

  // 1. Recent 3-Day Price Trend (Momentum)
  const pctChange = data.pct_change_day1 != null ? data.pct_change_day1 : 0;
  const isPositiveTrend = pctChange >= 0;
  const trendSign = isPositiveTrend ? '+' : '';
  const trendLabel =
    Math.abs(pctChange) < 1.0
      ? 'Stable Price Momentum'
      : isPositiveTrend
      ? 'Upward Price Momentum'
      : 'Downward Price Momentum';
  const trendBarColor = Math.abs(pctChange) < 1.0 ? C.blue : isPositiveTrend ? C.emerald : C.red;
  const trendFillPct = Math.min(Math.max(Math.round((Math.abs(pctChange) / 10) * 100), 20), 100);

  // 2. Supply Hub Weather Impact
  const weatherLevel = (data.weather_flag_level || 'none').toLowerCase();
  let weatherImpactLabel = 'Minimal Impact';
  let weatherColor = C.emerald;
  let weatherBg = C.emeraldDim;
  let weatherDesc = 'Dry zone rainfall patterns remain within normal seasonal bounds.';

  if (weatherLevel === 'severe') {
    weatherImpactLabel = 'High Impact';
    weatherColor = C.red;
    weatherBg = C.redDim;
    weatherDesc = 'Substantial rainfall changes in key supply hubs are influencing farm-gate arrivals.';
  } else if (weatherLevel === 'moderate') {
    weatherImpactLabel = 'Moderate Impact';
    weatherColor = C.amber;
    weatherBg = C.amberDim;
    weatherDesc = 'Minor rainfall deficit observed; irrigation monitoring recommended.';
  }

  // 3. Market Stability Check
  const isAnomaly = !!data.is_anomaly;
  const stabilityLabel = isAnomaly ? 'Unseasonal Volatility' : 'Normal Daily Trading';
  const stabilityColor = isAnomaly ? C.amber : C.emerald;
  const stabilityBg = isAnomaly ? C.amberDim : C.emeraldDim;
  const stabilityDesc = isAnomaly
    ? 'Irregular market price movements detected; verify spot deals locally.'
    : 'Price patterns align with normal seasonal trading cycles.';

  // 4. Clean Market Summary (strip any technical driver parenthetical math)
  const cleanReasoning = (data.reasoning || '')
    .replace(/\s*\([^)]*driven[^)]*\)\.?/gi, '')
    .replace(/\s*\([^)]*weather impact[^)]*\)\.?/gi, '')
    .replace(/^RECOMMENDATION:\s*/i, '')
    .trim();

  return (
    <View style={styles.container}>
      <TouchableOpacity
        style={styles.header}
        onPress={() => setExpanded((prev) => !prev)}
        activeOpacity={0.75}
      >
        <View style={styles.headerLeft}>
          <MaterialCommunityIcons name="lightbulb-on-outline" size={18} color={C.amber} />
          <Text style={styles.headerTitle}>Why this forecast? (Market Drivers)</Text>
        </View>
        <View style={styles.headerRight}>
          <Text style={styles.badgeText}>Market Drivers</Text>
          <MaterialCommunityIcons
            name={expanded ? 'chevron-up' : 'chevron-down'}
            size={18}
            color={C.muted}
          />
        </View>
      </TouchableOpacity>

      {expanded && (
        <View style={styles.body}>
          {/* Visual Driver Card 1: Recent Price Trend */}
          <View style={styles.driverCard}>
            <View style={styles.driverTopRow}>
              <View style={styles.driverTitleWrap}>
                <MaterialCommunityIcons name="chart-line-variant" size={16} color={trendBarColor} />
                <Text style={styles.driverLabel}>Recent 3-Day Price Trend</Text>
              </View>
              <Text style={[styles.driverStatusText, { color: trendBarColor }]}>
                {trendSign}{pctChange.toFixed(1)}% · {trendLabel}
              </Text>
            </View>
            <View style={styles.barTrack}>
              <View
                style={[
                  styles.barFill,
                  { width: `${trendFillPct}%`, backgroundColor: trendBarColor },
                ]}
              />
            </View>
          </View>

          {/* Visual Driver Card 2: Weather Impact */}
          <View style={styles.driverCard}>
            <View style={styles.driverTopRow}>
              <View style={styles.driverTitleWrap}>
                <MaterialCommunityIcons name="weather-partly-rainy" size={16} color={weatherColor} />
                <Text style={styles.driverLabel}>Supply Hub Weather Impact</Text>
              </View>
              <View style={[styles.statusBadge, { backgroundColor: weatherBg }]}>
                <Text style={[styles.statusBadgeText, { color: weatherColor }]}>
                  {weatherImpactLabel}
                </Text>
              </View>
            </View>
            <Text style={styles.driverSubText}>{weatherDesc}</Text>
          </View>

          {/* Visual Driver Card 3: Market Stability */}
          <View style={styles.driverCard}>
            <View style={styles.driverTopRow}>
              <View style={styles.driverTitleWrap}>
                <MaterialCommunityIcons name="shield-check-outline" size={16} color={stabilityColor} />
                <Text style={styles.driverLabel}>Market Stability Check</Text>
              </View>
              <View style={[styles.statusBadge, { backgroundColor: stabilityBg }]}>
                <Text style={[styles.statusBadgeText, { color: stabilityColor }]}>
                  {stabilityLabel}
                </Text>
              </View>
            </View>
            <Text style={styles.driverSubText}>{stabilityDesc}</Text>
          </View>

          {/* Decision Summary */}
          {cleanReasoning ? (
            <View style={styles.reasoningBox}>
              <Text style={styles.reasoningTitle}>Market Summary</Text>
              <Text style={styles.reasoningText}>{cleanReasoning}</Text>
            </View>
          ) : null}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginHorizontal: 16,
    marginBottom: 20,
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 16,
    overflow: 'hidden',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 14,
    paddingVertical: 13,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    flex: 1,
  },
  headerTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: C.text,
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  badgeText: {
    fontSize: 9,
    fontWeight: '700',
    color: C.amber,
    backgroundColor: C.amberDim,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  body: {
    paddingHorizontal: 14,
    paddingBottom: 14,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.05)',
    gap: 10,
    paddingTop: 12,
  },
  driverCard: {
    backgroundColor: C.surface2,
    borderRadius: 10,
    padding: 10,
    borderWidth: 1,
    borderColor: C.border,
  },
  driverTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  driverTitleWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  driverLabel: {
    fontSize: 11.5,
    fontWeight: '700',
    color: C.text,
  },
  driverStatusText: {
    fontSize: 10.5,
    fontWeight: '700',
  },
  statusBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  statusBadgeText: {
    fontSize: 9.5,
    fontWeight: '700',
  },
  driverSubText: {
    fontSize: 11,
    color: C.textSecondary,
    lineHeight: 15,
  },
  barTrack: {
    height: 5,
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    borderRadius: 3,
    overflow: 'hidden',
    marginTop: 2,
  },
  barFill: {
    height: '100%',
    borderRadius: 3,
  },
  reasoningBox: {
    backgroundColor: 'rgba(245, 158, 11, 0.06)',
    borderLeftWidth: 3,
    borderLeftColor: C.amber,
    padding: 10,
    borderRadius: 6,
    marginTop: 2,
  },
  reasoningTitle: {
    fontSize: 10,
    fontWeight: '700',
    color: C.amber,
    textTransform: 'uppercase',
    letterSpacing: 0.3,
    marginBottom: 3,
  },
  reasoningText: {
    fontSize: 11,
    color: C.textSecondary,
    lineHeight: 16,
  },
});
