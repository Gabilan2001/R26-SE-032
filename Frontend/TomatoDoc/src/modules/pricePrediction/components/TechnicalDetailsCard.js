import React, { useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { C } from '../constants/priceTheme';

export default function TechnicalDetailsCard({ data }) {
  const [expanded, setExpanded] = useState(false);

  if (!data) return null;

  const lstmShare =
    data.driver_share_lstm_pct != null ? data.driver_share_lstm_pct.toFixed(0) : '100';
  const weatherShare =
    data.driver_share_weather_pct != null ? data.driver_share_weather_pct.toFixed(0) : '0';

  const d14Rain = data.d14_cum_rain_mm != null ? data.d14_cum_rain_mm.toFixed(1) : '—';
  const weatherLevel = (data.weather_flag_level || 'none').toUpperCase();

  const isAnomaly = data.is_anomaly
    ? 'YES (Market shock detected)'
    : 'NO (Normal market behavior)';

  const shap = data.shap_explanation;
  const rankedTimesteps = shap && Array.isArray(shap.ranked_timesteps) ? shap.ranked_timesteps.slice(0, 5) : [];
  const maxShap = Math.max(...rankedTimesteps.map((t) => Math.abs(t.shap_contribution_lkr || 0)), 0.01);

  const confRating = data.is_anomaly ? '50%' : '90%';

  return (
    <View style={styles.container}>
      <TouchableOpacity
        style={styles.header}
        onPress={() => setExpanded((prev) => !prev)}
        activeOpacity={0.75}
      >
        <View style={styles.headerLeft}>
          <MaterialCommunityIcons name="cogs" size={18} color={C.amber} />
          <Text style={styles.headerTitle}>Technical & SHAP Details</Text>
        </View>
        <View style={styles.headerRight}>
          <Text style={styles.badgeText}>Research</Text>
          <MaterialCommunityIcons
            name={expanded ? 'chevron-up' : 'chevron-down'}
            size={18}
            color={C.muted}
          />
        </View>
      </TouchableOpacity>

      {expanded && (
        <View style={styles.body}>
          {/* Reasoning */}
          <View style={styles.section}>
            <Text style={styles.secLabel}>Decision Reasoning Engine</Text>
            <Text style={styles.secValue}>{data.reasoning || 'No rule trace recorded.'}</Text>
          </View>

          {/* SHAP Attributions */}
          {shap && shap.summary_sentence && (
            <View style={styles.section}>
              <Text style={styles.secLabel}>LSTM SHAP Timestep Attributions</Text>
              <Text style={styles.shapSummary}>{shap.summary_sentence}</Text>

              <View style={styles.shapList}>
                {rankedTimesteps.map((t, idx) => {
                  const val = t.shap_contribution_lkr || 0;
                  const isPos = val >= 0;
                  const sign = isPos ? '+' : '';
                  const barColor = isPos ? C.emerald : C.red;
                  const pct = Math.min(Math.round((Math.abs(val) / maxShap) * 100), 100);

                  return (
                    <View key={`shap-${idx}`} style={styles.shapItem}>
                      <View style={styles.shapRow}>
                        <Text style={styles.shapLag}>
                          {t.timestep_label}{' '}
                          <Text style={styles.shapPrice}>
                            ({t.observed_price_lkr.toFixed(1)} LKR)
                          </Text>
                        </Text>
                        <Text style={[styles.shapVal, { color: barColor }]}>
                          {sign}
                          {val.toFixed(2)} LKR
                        </Text>
                      </View>
                      <View style={styles.track}>
                        <View
                          style={[
                            styles.fill,
                            { width: `${pct}%`, backgroundColor: barColor },
                          ]}
                        />
                      </View>
                    </View>
                  );
                })}
              </View>
            </View>
          )}

          {/* Driver Share */}
          <View style={styles.section}>
            <Text style={styles.secLabel}>Forecast Driver Deconstruction</Text>
            <Text style={styles.secValue}>
              LSTM Price Momentum: <Text style={{ color: C.amber, fontWeight: '700' }}>{lstmShare}%</Text> | Weather Calibration: <Text style={{ color: C.emerald, fontWeight: '700' }}>{weatherShare}%</Text>
            </Text>
          </View>

          {/* 14-Day Rain Delta */}
          <View style={styles.section}>
            <Text style={styles.secLabel}>14-Day Lagged Weather Signal (Anuradhapura)</Text>
            <Text style={styles.secValue}>
              Signal Flag: <Text style={{ fontWeight: '700', color: C.text }}>{weatherLevel}</Text> ({d14Rain} mm cumulative rainfall change)
            </Text>
          </View>

          {/* Anomaly Check */}
          <View style={styles.section}>
            <Text style={styles.secLabel}>Price Residual Anomaly Check (IsolationForest)</Text>
            <Text style={styles.secValue}>
              Anomaly Detected: <Text style={{ fontWeight: '700', color: data.is_anomaly ? C.red : C.emerald }}>{isAnomaly}</Text>
              {data.anomaly_score != null ? ` (Score: ${data.anomaly_score.toFixed(4)})` : ''}
            </Text>
          </View>

          {/* Confidence */}
          <View style={styles.section}>
            <Text style={styles.secLabel}>Heuristic Model Confidence</Text>
            <Text style={styles.secValue}>
              Confidence Rating: <Text style={{ fontWeight: '700', color: C.text }}>{confRating}</Text>
            </Text>
          </View>
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
    paddingVertical: 12,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
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
  },
  section: {
    marginTop: 10,
  },
  secLabel: {
    fontSize: 10,
    fontWeight: '700',
    color: C.amber,
    textTransform: 'uppercase',
    letterSpacing: 0.3,
    marginBottom: 2,
  },
  secValue: {
    fontSize: 11.5,
    color: C.textSecondary,
    lineHeight: 16,
  },
  shapSummary: {
    fontSize: 11,
    color: C.text,
    fontWeight: '600',
    marginBottom: 6,
  },
  shapList: {
    gap: 6,
  },
  shapItem: {
    backgroundColor: C.surface2,
    padding: 6,
    borderRadius: 6,
  },
  shapRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 3,
  },
  shapLag: {
    fontSize: 11,
    fontWeight: '700',
    color: C.text,
  },
  shapPrice: {
    fontSize: 10,
    color: C.muted,
    fontWeight: '400',
  },
  shapVal: {
    fontSize: 11,
    fontWeight: '800',
  },
  track: {
    height: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    borderRadius: 2,
    overflow: 'hidden',
  },
  fill: {
    height: '100%',
    borderRadius: 2,
  },
});
