import React, { useState } from 'react';
import {
  ActivityIndicator,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { C } from '../constants/priceTheme';
import { fetchSeasonalForecast } from '../api/priceClient';

export default function PlanningTab({ selectedMarket, selectedType }) {
  const [targetMonth, setTargetMonth] = useState(new Date().getMonth() + 2 > 12 ? 1 : new Date().getMonth() + 2);
  const [targetYear, setTargetYear] = useState(
    new Date().getMonth() + 2 > 12 ? new Date().getFullYear() + 1 : new Date().getFullYear()
  );
  const [loading, setLoading] = useState(false);
  const [seasonalData, setSeasonalData] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');

  const months = [
    { num: 1, name: 'January' },
    { num: 2, name: 'February' },
    { num: 3, name: 'March' },
    { num: 4, name: 'April' },
    { num: 5, name: 'May' },
    { num: 6, name: 'June' },
    { num: 7, name: 'July' },
    { num: 8, name: 'August' },
    { num: 9, name: 'September' },
    { num: 10, name: 'October' },
    { num: 11, name: 'November' },
    { num: 12, name: 'December' },
  ];

  const handleFetchSeasonal = async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      const res = await fetchSeasonalForecast({
        market: selectedMarket,
        type: selectedType,
        targetMonth,
        targetYear,
      });
      setSeasonalData(res);
    } catch (err) {
      setErrorMsg(err.friendlyMessage || 'Unable to retrieve seasonal forecast.');
    } finally {
      setLoading(false);
    }
  };

  const nom = seasonalData ? seasonalData.planning_estimates_nominal || {} : {};
  const wObj = seasonalData ? seasonalData.weather || {} : {};

  // Clean Price Values
  const lowPrice = nom.low_p10 != null ? Math.round(nom.low_p10) : (nom.core_p25 != null ? Math.round(nom.core_p25) : '—');
  const avgPrice = nom.median_p50 != null ? Math.round(nom.median_p50) : '—';
  const highPrice = nom.high_p90 != null ? Math.round(nom.high_p90) : (nom.core_p75 != null ? Math.round(nom.core_p75) : '—');

  // Simplified Climate Gauge Logic
  let climateLabel = '⛅ Normal Seasonal Weather';
  let climateColor = C.emerald;
  let climateBg = C.emeraldDim;
  let climateProb = 50;

  if (wObj.ensemble_probability) {
    const above = wObj.ensemble_probability.above_normal || 0;
    const near = wObj.ensemble_probability.near_normal || 0;
    const below = wObj.ensemble_probability.below_normal || 0;

    if (above >= near && above >= below) {
      climateLabel = '🌧️ Wetter than Normal';
      climateColor = C.blue;
      climateBg = 'rgba(59, 130, 246, 0.12)';
      climateProb = above;
    } else if (below >= near && below >= above) {
      climateLabel = '☀️ Drier than Normal';
      climateColor = C.amber;
      climateBg = C.amberDim;
      climateProb = below;
    } else {
      climateLabel = '⛅ Normal Seasonal Weather';
      climateColor = C.emerald;
      climateBg = C.emeraldDim;
      climateProb = near;
    }
  } else if (wObj.regional_outlook) {
    if (String(wObj.regional_outlook).toLowerCase().includes('above')) {
      climateLabel = '🌧️ Wetter than Normal';
      climateColor = C.blue;
      climateBg = 'rgba(59, 130, 246, 0.12)';
    } else if (String(wObj.regional_outlook).toLowerCase().includes('below')) {
      climateLabel = '☀️ Drier than Normal';
      climateColor = C.amber;
      climateBg = C.amberDim;
    } else {
      climateLabel = '⛅ Normal Seasonal Weather';
      climateColor = C.emerald;
      climateBg = C.emeraldDim;
    }
  }

  // Single Actionable Planning Sentence
  const selectedMonthName = months.find((m) => m.num === targetMonth)?.name || 'Harvest Month';
  let cleanGuidance = `Plan staggered crop cultivation to align peak harvest in ${selectedMonthName} with expected average returns of ${avgPrice} LKR/kg.`;
  if (seasonalData?.planning_recommendation) {
    cleanGuidance = seasonalData.planning_recommendation.split('.')[0] + '.';
  }

  return (
    <View style={styles.container}>
      {/* Target Planning Horizon Card */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <MaterialCommunityIcons name="calendar-month" size={18} color={C.amber} />
          <Text style={styles.cardTitle}>Select Target Harvest Month</Text>
        </View>

        <Text style={styles.descText}>
          Select target harvest timing (1–12 months ahead) to view seasonal market price trends:
        </Text>

        <View style={styles.monthSelectorGrid}>
          {months.map((m) => {
            const isSelected = m.num === targetMonth;
            return (
              <TouchableOpacity
                key={m.num}
                style={[styles.monthChip, isSelected && styles.monthChipSelected]}
                onPress={() => setTargetMonth(m.num)}
                activeOpacity={0.7}
              >
                <Text style={[styles.monthText, isSelected && styles.monthTextSelected]}>
                  {m.name.slice(0, 3)}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>

        <View style={styles.yearRow}>
          <Text style={styles.yearLabel}>Target Year:</Text>
          <View style={styles.yearChips}>
            {[new Date().getFullYear(), new Date().getFullYear() + 1].map((yr) => (
              <TouchableOpacity
                key={yr}
                style={[styles.yearChip, targetYear === yr && styles.yearChipSelected]}
                onPress={() => setTargetYear(yr)}
                activeOpacity={0.7}
              >
                <Text
                  style={[styles.yearChipText, targetYear === yr && styles.yearChipTextSelected]}
                >
                  {yr}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        <TouchableOpacity
          style={[styles.actionBtn, loading && styles.actionBtnDisabled]}
          onPress={handleFetchSeasonal}
          disabled={loading}
          activeOpacity={0.8}
        >
          {loading ? (
            <ActivityIndicator size="small" color="#0f0f0f" />
          ) : (
            <>
              <MaterialCommunityIcons name="lightning-bolt" size={18} color="#0f0f0f" />
              <Text style={styles.actionBtnText}>Generate Seasonal Price Outlook</Text>
            </>
          )}
        </TouchableOpacity>

        {errorMsg ? <Text style={styles.errorText}>{errorMsg}</Text> : null}
      </View>

      {/* Seasonal Results View */}
      {seasonalData && (
        <View style={styles.resultsCard}>
          <View style={styles.resultsHeader}>
            <View>
              <Text style={styles.resultsTitle}>
                {seasonalData.target_month_name} {seasonalData.target_year} Price Outlook
              </Text>
              <Text style={styles.resultsSub}>
                Based on historical seasonal price cycles ({seasonalData.series || selectedMarket})
              </Text>
            </View>
            <View style={styles.confBadge}>
              <Text style={styles.confBadgeText}>
                {seasonalData.confidence_rating || 'MODERATE'} CONFIDENCE
              </Text>
            </View>
          </View>

          {/* 3 Clean Price Cards */}
          <View style={styles.rangeRow}>
            {/* Low Estimate */}
            <View style={[styles.rangeBox, { backgroundColor: C.redDim, borderColor: C.redBorder }]}>
              <Text style={[styles.rangeBoxLabel, { color: C.red }]}>Low Estimate</Text>
              <Text style={styles.rangeBoxSub}>(Market Glut)</Text>
              <Text style={[styles.rangeBoxPrice, { color: C.red }]}>{lowPrice}</Text>
              <Text style={styles.rangeUnit}>LKR/kg</Text>
            </View>

            {/* Expected Average */}
            <View style={[styles.rangeBox, { backgroundColor: C.blueDim, borderColor: C.blueBorder }]}>
              <Text style={[styles.rangeBoxLabel, { color: C.blue }]}>Expected Average</Text>
              <Text style={styles.rangeBoxSub}>(Normal Season)</Text>
              <Text style={[styles.rangeBoxPrice, { color: C.blue }]}>{avgPrice}</Text>
              <Text style={styles.rangeUnit}>LKR/kg</Text>
            </View>

            {/* High Estimate */}
            <View style={[styles.rangeBox, { backgroundColor: C.emeraldDim, borderColor: C.emeraldBorder }]}>
              <Text style={[styles.rangeBoxLabel, { color: C.emerald }]}>High Estimate</Text>
              <Text style={styles.rangeBoxSub}>(Supply Shortage)</Text>
              <Text style={[styles.rangeBoxPrice, { color: C.emerald }]}>{highPrice}</Text>
              <Text style={styles.rangeUnit}>LKR/kg</Text>
            </View>
          </View>

          {/* Simplified Climate Outlook Gauge */}
          <View style={styles.climateCard}>
            <View style={styles.climateHeaderRow}>
              <Text style={styles.climateTitle}>
                Expected Weather in {seasonalData.target_month_name}:
              </Text>
              <View style={[styles.climateBadge, { backgroundColor: climateBg }]}>
                <Text style={[styles.climateBadgeText, { color: climateColor }]}>
                  {climateLabel}
                </Text>
              </View>
            </View>

            <View style={styles.gaugeTrack}>
              <View
                style={[
                  styles.gaugeFill,
                  { width: `${Math.max(climateProb, 20)}%`, backgroundColor: climateColor },
                ]}
              />
            </View>
          </View>

          {/* Actionable Crop Planning Guidance */}
          <View style={styles.guidanceBox}>
            <MaterialCommunityIcons name="lightbulb-on-outline" size={18} color={C.emerald} />
            <Text style={styles.guidanceText}>
              <Text style={{ fontWeight: '700', color: C.emerald }}>Planning Tip: </Text>
              {cleanGuidance}
            </Text>
          </View>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingTop: 4,
    paddingBottom: 24,
  },
  card: {
    marginHorizontal: 16,
    marginBottom: 14,
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 16,
    padding: 14,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 6,
  },
  cardTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: C.text,
  },
  descText: {
    fontSize: 11.5,
    color: C.textSecondary,
    marginBottom: 10,
    lineHeight: 16,
  },
  monthSelectorGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginBottom: 12,
  },
  monthChip: {
    flex: 1,
    minWidth: '22%',
    backgroundColor: C.surface2,
    borderWidth: 1,
    borderColor: C.border,
    paddingVertical: 7,
    borderRadius: 8,
    alignItems: 'center',
  },
  monthChipSelected: {
    backgroundColor: C.amberDim,
    borderColor: C.amberBorder,
  },
  monthText: {
    fontSize: 11,
    fontWeight: '600',
    color: C.textSecondary,
  },
  monthTextSelected: {
    color: C.amber,
    fontWeight: '700',
  },
  yearRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 14,
  },
  yearLabel: {
    fontSize: 12,
    color: C.muted,
    fontWeight: '600',
  },
  yearChips: {
    flexDirection: 'row',
    gap: 8,
  },
  yearChip: {
    backgroundColor: C.surface2,
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: C.border,
  },
  yearChipSelected: {
    backgroundColor: C.amberDim,
    borderColor: C.amberBorder,
  },
  yearChipText: {
    fontSize: 12,
    fontWeight: '600',
    color: C.textSecondary,
  },
  yearChipTextSelected: {
    color: C.amber,
    fontWeight: '700',
  },
  actionBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: C.amber,
    borderRadius: 12,
    paddingVertical: 12,
    gap: 6,
  },
  actionBtnDisabled: {
    opacity: 0.6,
  },
  actionBtnText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#0f0f0f',
  },
  errorText: {
    fontSize: 11,
    color: C.red,
    marginTop: 8,
    textAlign: 'center',
  },
  resultsCard: {
    marginHorizontal: 16,
    marginBottom: 14,
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 16,
    padding: 14,
  },
  resultsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  resultsTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: C.text,
  },
  resultsSub: {
    fontSize: 10,
    color: C.muted,
    marginTop: 1,
  },
  confBadge: {
    backgroundColor: C.amberDim,
    paddingHorizontal: 6,
    paddingVertical: 3,
    borderRadius: 6,
  },
  confBadgeText: {
    fontSize: 8.5,
    fontWeight: '700',
    color: C.amber,
  },
  rangeRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 12,
  },
  rangeBox: {
    flex: 1,
    borderWidth: 1,
    borderRadius: 10,
    padding: 8,
    alignItems: 'center',
  },
  rangeBoxLabel: {
    fontSize: 9.5,
    fontWeight: '700',
    marginBottom: 1,
  },
  rangeBoxSub: {
    fontSize: 8,
    color: C.muted,
    marginBottom: 3,
  },
  rangeBoxPrice: {
    fontSize: 16,
    fontWeight: '800',
  },
  rangeUnit: {
    fontSize: 8.5,
    color: C.muted,
    marginTop: 1,
  },
  climateCard: {
    backgroundColor: C.surface2,
    borderRadius: 10,
    padding: 10,
    borderWidth: 1,
    borderColor: C.border,
    marginBottom: 10,
  },
  climateHeaderRow: {
    flexDirection: 'column',
    alignItems: 'flex-start',
    gap: 5,
    marginBottom: 8,
  },
  climateTitle: {
    fontSize: 11,
    fontWeight: '700',
    color: C.text,
  },
  climateBadge: {
    paddingHorizontal: 7,
    paddingVertical: 3,
    borderRadius: 6,
  },
  climateBadgeText: {
    fontSize: 10,
    fontWeight: '700',
  },
  gaugeTrack: {
    height: 6,
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    borderRadius: 3,
    overflow: 'hidden',
  },
  gaugeFill: {
    height: '100%',
    borderRadius: 3,
  },
  guidanceBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: 'rgba(16, 185, 129, 0.08)',
    borderLeftWidth: 3,
    borderLeftColor: C.emerald,
    padding: 10,
    borderRadius: 8,
    gap: 8,
  },
  guidanceText: {
    flex: 1,
    fontSize: 11,
    color: C.textSecondary,
    lineHeight: 16,
  },
});
