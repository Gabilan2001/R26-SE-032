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
  const real = seasonalData ? seasonalData.real_price_estimates_constant_lkr || {} : {};
  const wObj = seasonalData ? seasonalData.weather || {} : {};
  const isSeas5 = wObj.source === 'ECMWF SEAS5';

  return (
    <View style={styles.container}>
      {/* Target Planning Horizon Card */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <MaterialCommunityIcons name="calendar-month" size={18} color={C.amber} />
          <Text style={styles.cardTitle}>Select Target Harvest Month</Text>
        </View>

        <Text style={styles.descText}>
          Plan crop sales 1–12 months ahead using 10 years of CPI-adjusted historical price distributions:
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
                {seasonalData.target_month_name} {seasonalData.target_year} Price Distribution
              </Text>
              <Text style={styles.resultsSub}>
                Based on {seasonalData.historical_seasons_count || 10} years of historical data ({seasonalData.series || selectedMarket})
              </Text>
            </View>
            <View style={styles.confBadge}>
              <Text style={styles.confBadgeText}>
                {seasonalData.confidence_rating || 'MODERATE'} CONFIDENCE
              </Text>
            </View>
          </View>

          {/* 3 Range Boxes */}
          <Text style={styles.rangeLabel}>
            Expected Core Planning Range (Nominal LKR, ~4% inflation assumed):
          </Text>
          <View style={styles.rangeRow}>
            <View style={[styles.rangeBox, { backgroundColor: C.redDim, borderColor: C.redBorder }]}>
              <Text style={[styles.rangeBoxLabel, { color: C.red }]}>Core Low (25th)</Text>
              <Text style={[styles.rangeBoxPrice, { color: C.red }]}>{nom.core_p25 || '—'}</Text>
              <Text style={styles.rangeUnit}>LKR/kg</Text>
            </View>

            <View style={[styles.rangeBox, { backgroundColor: C.blueDim, borderColor: C.blueBorder }]}>
              <Text style={[styles.rangeBoxLabel, { color: C.blue }]}>Expected (50th)</Text>
              <Text style={[styles.rangeBoxPrice, { color: C.blue }]}>{nom.median_p50 || '—'}</Text>
              <Text style={styles.rangeUnit}>LKR/kg</Text>
            </View>

            <View style={[styles.rangeBox, { backgroundColor: C.emeraldDim, borderColor: C.emeraldBorder }]}>
              <Text style={[styles.rangeBoxLabel, { color: C.emerald }]}>Core High (75th)</Text>
              <Text style={[styles.rangeBoxPrice, { color: C.emerald }]}>{nom.core_p75 || '—'}</Text>
              <Text style={styles.rangeUnit}>LKR/kg</Text>
            </View>
          </View>

          <Text style={styles.riskRangeText}>
            Wider Risk Range (10th–90th pctl): <Text style={styles.boldWhite}>{nom.low_p10} – {nom.high_p90} LKR/kg</Text> | Constant Real Baseline: <Text style={styles.boldWhite}>{real.median_p50} LKR/kg</Text>
          </Text>

          {/* SEAS5 Climate Outlook */}
          {isSeas5 && wObj.ensemble_probability && (
            <View style={styles.seas5Box}>
              <View style={styles.seas5Header}>
                <Text style={styles.seas5Title}>ECMWF SEAS5 Regional Climate Outlook</Text>
                <Text style={styles.seas5Source}>50-member ensemble</Text>
              </View>
              <Text style={styles.seas5Outlook}>
                Regional Tendency: <Text style={styles.boldWhite}>{wObj.regional_outlook}</Text>
              </Text>
              <View style={styles.probRow}>
                <View style={styles.probCol}>
                  <Text style={styles.probLabel}>Above Normal</Text>
                  <Text style={[styles.probVal, { color: C.emerald }]}>{wObj.ensemble_probability.above_normal}%</Text>
                </View>
                <View style={styles.probCol}>
                  <Text style={styles.probLabel}>Near Normal</Text>
                  <Text style={[styles.probVal, { color: C.blue }]}>{wObj.ensemble_probability.near_normal}%</Text>
                </View>
                <View style={styles.probCol}>
                  <Text style={styles.probLabel}>Below Normal</Text>
                  <Text style={[styles.probVal, { color: C.red }]}>{wObj.ensemble_probability.below_normal}%</Text>
                </View>
              </View>
            </View>
          )}

          {/* Agronomic Guidance */}
          {seasonalData.planning_recommendation ? (
            <View style={styles.guidanceBox}>
              <MaterialCommunityIcons name="lightbulb-on-outline" size={18} color={C.emerald} />
              <Text style={styles.guidanceText}>
                <Text style={{ fontWeight: '700', color: C.emerald }}>Planning Guidance: </Text>
                {seasonalData.planning_recommendation}
              </Text>
            </View>
          ) : null}
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
    marginBottom: 10,
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
  rangeLabel: {
    fontSize: 10.5,
    color: C.textSecondary,
    fontWeight: '600',
    marginBottom: 6,
  },
  rangeRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 8,
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
    marginBottom: 2,
  },
  rangeBoxPrice: {
    fontSize: 16,
    fontWeight: '800',
  },
  rangeUnit: {
    fontSize: 8.5,
    color: C.muted,
  },
  riskRangeText: {
    fontSize: 10,
    color: C.muted,
    lineHeight: 14,
    textAlign: 'center',
    marginBottom: 10,
  },
  boldWhite: {
    color: C.text,
    fontWeight: '700',
  },
  seas5Box: {
    backgroundColor: C.surface2,
    borderRadius: 10,
    padding: 10,
    borderWidth: 1,
    borderColor: C.border,
    marginBottom: 10,
  },
  seas5Header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  seas5Title: {
    fontSize: 11,
    fontWeight: '700',
    color: C.text,
  },
  seas5Source: {
    fontSize: 9,
    color: C.muted,
  },
  seas5Outlook: {
    fontSize: 10.5,
    color: C.textSecondary,
    marginBottom: 6,
  },
  probRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  probCol: {
    alignItems: 'center',
  },
  probLabel: {
    fontSize: 9,
    color: C.muted,
  },
  probVal: {
    fontSize: 13,
    fontWeight: '800',
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
