import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { C } from '../constants/priceTheme';

export default function InsightsTab({ predictionData, newsData }) {
  const regImpact = predictionData ? predictionData.regional_weather_impact : null;
  const gw = regImpact ? regImpact.growing_region_weather : null;
  const regions = gw && gw.regions ? gw.regions : {};
  const season = regImpact ? regImpact.season : 'Maha';
  const overallRisk = regImpact ? regImpact.overall_weather_risk : 'LOW';
  const primaryRegion = regImpact ? regImpact.primary_region : 'Anuradhapura';
  const explanation = regImpact ? regImpact.explanation : '';
  const structAgri = regImpact ? regImpact.structured_agricultural_assessment : null;
  const corroborated = predictionData ? predictionData.corroborated_signals : null;

  const storage = regImpact ? regImpact.market_storage_impact : null;

  // News Data
  const newsMood = newsData ? newsData.news_sentiment || 'neutral' : 'neutral';
  const headlines = newsData && Array.isArray(newsData.relevant_headlines) ? newsData.relevant_headlines.slice(0, 5) : [];
  const detectedLocations = newsData && Array.isArray(newsData.detected_locations) ? newsData.detected_locations : [];
  const agriRecords = newsData && Array.isArray(newsData.agricultural_impact_records) ? newsData.agricultural_impact_records : [];

  let riskBadgeColor = C.emerald;
  let riskBadgeBg = C.emeraldDim;
  if (overallRisk === 'SEVERE') {
    riskBadgeColor = C.red;
    riskBadgeBg = C.redDim;
  } else if (overallRisk === 'MODERATE') {
    riskBadgeColor = C.amber;
    riskBadgeBg = C.amberDim;
  }

  return (
    <View style={styles.container}>
      {/* Regional Weather Risk Card */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <View style={styles.headerTitleRow}>
            <MaterialCommunityIcons name="weather-partly-cloudy" size={18} color={C.amber} />
            <Text style={styles.cardTitle}>Supply Hub Weather & Water Stress</Text>
          </View>
          <View style={[styles.riskBadge, { backgroundColor: riskBadgeBg }]}>
            <Text style={[styles.riskBadgeText, { color: riskBadgeColor }]}>
              {season} Season · {overallRisk}
            </Text>
          </View>
        </View>

        <Text style={styles.signalText}>
          Primary Focus: <Text style={{ fontWeight: '700', color: C.text }}>{primaryRegion}</Text> ({structAgri?.agro_ecological_zone || 'Agricultural Hub'})
        </Text>

        {/* 4 Station Grid */}
        <View style={styles.stationGrid}>
          {Object.entries(regions).map(([name, stData]) => {
            const waterStatus = stData.water_status || 'OPTIMAL_BALANCED';
            const isDrought = waterStatus.includes('DROUGHT') || waterStatus.includes('DEFICIT');
            const isExcess = waterStatus.includes('EXCESS') || waterStatus.includes('MOISTURE');

            let stColor = C.emerald;
            let stBg = C.emeraldDim;
            let statusLabel = 'Optimal';
            if (waterStatus === 'SEVERE_DROUGHT_STRESS') {
              stColor = C.red;
              stBg = C.redDim;
              statusLabel = 'Drought Risk';
            } else if (waterStatus === 'MODERATE_WATER_DEFICIT') {
              stColor = C.amber;
              stBg = C.amberDim;
              statusLabel = 'Water Deficit';
            } else if (waterStatus === 'EXCESS_WATER_SATURATION') {
              stColor = C.red;
              stBg = C.redDim;
              statusLabel = 'Excess Rain';
            } else if (waterStatus === 'ELEVATED_MOISTURE') {
              stColor = C.blue;
              stBg = 'rgba(59, 130, 246, 0.12)';
              statusLabel = 'Elevated Rain';
            }

            const rain21 = stData.rain_21d_cum_mm != null ? stData.rain_21d_cum_mm.toFixed(1) : '—';
            const zScore =
              stData.rain_21d_z != null
                ? (stData.rain_21d_z >= 0 ? '+' : '') + stData.rain_21d_z.toFixed(1) + 'σ'
                : '—';
            const temp3d = stData.temp_3d_avg_c != null ? stData.temp_3d_avg_c.toFixed(1) : '—';
            const dryDays = stData.consecutive_dry_days || 0;

            return (
              <View key={name} style={styles.stationTile}>
                <View style={styles.stationTop}>
                  <Text style={styles.stationName}>📍 {name}</Text>
                  <View style={[styles.miniBadge, { backgroundColor: stBg }]}>
                    <Text style={[styles.miniBadgeText, { color: stColor }]}>{statusLabel}</Text>
                  </View>
                </View>
                <Text style={styles.stationDetail}>
                  21d Rain: <Text style={styles.boldWhite}>{rain21} mm</Text> ({zScore})
                </Text>
                <Text style={styles.stationDetail}>
                  3d Temp: <Text style={styles.boldWhite}>{temp3d} °C</Text>
                </Text>
                <Text style={styles.stationDetail}>
                  Dry Spell: <Text style={styles.boldWhite}>{dryDays} days</Text>
                </Text>
              </View>
            );
          })}
        </View>

        {explanation ? (
          <View style={styles.analysisBox}>
            <Text style={styles.analysisText}>
              <Text style={{ fontWeight: '700', color: C.emerald }}>Agro Analysis: </Text>
              {explanation}
            </Text>
          </View>
        ) : null}
      </View>

      {/* Corroborated Intelligence Box (if active) */}
      {corroborated && (
        <View style={[styles.card, { borderColor: corroborated.multi_source_agreement ? C.amber : C.border }]}>
          <View style={styles.cardHeader}>
            <View style={styles.headerTitleRow}>
              <MaterialCommunityIcons name="shield-search" size={18} color={corroborated.multi_source_agreement ? C.amber : C.blue} />
              <Text style={styles.cardTitle}>Multi-Source Intelligence Corroboration</Text>
            </View>
            <View style={[styles.riskBadge, { backgroundColor: corroborated.multi_source_agreement ? C.amberDim : C.surface2 }]}>
              <Text style={[styles.riskBadgeText, { color: corroborated.multi_source_agreement ? C.amber : C.textSecondary }]}>
                {corroborated.confidence} Confidence
              </Text>
            </View>
          </View>

          <View style={styles.corroboratedGrid}>
            <View style={styles.corroboratedItem}>
              <Text style={styles.corroboratedLabel}>Region Assessed</Text>
              <Text style={styles.corroboratedVal}>{corroborated.primary_region}</Text>
            </View>
            <View style={styles.corroboratedItem}>
              <Text style={styles.corroboratedLabel}>Time Horizon</Text>
              <Text style={styles.corroboratedVal}>{corroborated.impact_time_horizon}</Text>
            </View>
            <View style={styles.corroboratedItem}>
              <Text style={styles.corroboratedLabel}>Supply Impact</Text>
              <Text style={[styles.corroboratedVal, { color: C.amber }]}>{corroborated.tomato_supply_risk}</Text>
            </View>
            <View style={styles.corroboratedItem}>
              <Text style={styles.corroboratedLabel}>Evidence Type</Text>
              <Text style={styles.corroboratedVal}>{corroborated.evidence_type}</Text>
            </View>
          </View>

          <Text style={styles.corroboratedInterpretation}>{corroborated.interpretation}</Text>
        </View>
      )}

      {/* Market Storage Context Card */}
      {storage && (
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <View style={styles.headerTitleRow}>
              <MaterialCommunityIcons name="warehouse" size={18} color={C.blue} />
              <Text style={styles.cardTitle}>
                Market Storage & Spoilage ({storage.market_location || 'Trade Center'})
              </Text>
            </View>
            <View
              style={[
                styles.riskBadge,
                {
                  backgroundColor:
                    storage.spoilage_risk_level === 'HIGH'
                      ? C.redDim
                      : storage.spoilage_risk_level === 'MEDIUM'
                      ? C.amberDim
                      : C.emeraldDim,
                },
              ]}
            >
              <Text
                style={[
                  styles.riskBadgeText,
                  {
                    color:
                      storage.spoilage_risk_level === 'HIGH'
                        ? C.red
                        : storage.spoilage_risk_level === 'MEDIUM'
                        ? C.amber
                        : C.emerald,
                  },
                ]}
              >
                Spoilage: {storage.spoilage_risk_level || 'LOW'}
              </Text>
            </View>
          </View>

          <View style={styles.storageDetailsRow}>
            <View style={styles.storageMetric}>
              <Text style={styles.storageMetricLabel}>3-Day Ambient Temp</Text>
              <Text style={styles.storageMetricVal}>
                {storage.ambient_temp_3d_avg_c != null
                  ? storage.ambient_temp_3d_avg_c.toFixed(1) + ' °C'
                  : '—'}
              </Text>
            </View>
            <View style={styles.storageMetric}>
              <Text style={styles.storageMetricLabel}>Selling Urgency</Text>
              <Text
                style={[
                  styles.storageMetricVal,
                  {
                    color:
                      storage.selling_urgency === 'URGENT'
                        ? C.red
                        : storage.selling_urgency === 'HIGH'
                        ? C.amber
                        : C.emerald,
                  },
                ]}
              >
                {storage.selling_urgency || 'NORMAL'}
              </Text>
            </View>
          </View>

          <Text style={styles.storageNote}>
            💡 Post-harvest tomato shelf life in ambient conditions is typically 3–5 days. High ambient heat increases spoilage risk during hold periods.
          </Text>
        </View>
      )}

      {/* Market News & Intelligence Card */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <View style={styles.headerTitleRow}>
            <MaterialCommunityIcons name="newspaper-variant-outline" size={18} color={C.amber} />
            <Text style={styles.cardTitle}>Market Intelligence & News</Text>
          </View>
          <View style={[styles.riskBadge, { backgroundColor: C.surface2 }]}>
            <Text style={[styles.riskBadgeText, { color: C.amber }]}>
              {newsMood.toUpperCase().replace('_', ' ')}
            </Text>
          </View>
        </View>

        {detectedLocations.length > 0 && (
          <View style={styles.locationsRow}>
            <Text style={styles.locationsLabel}>Locations Mentioned: </Text>
            <Text style={styles.locationsVal}>{detectedLocations.join(', ')}</Text>
          </View>
        )}

        {headlines.length > 0 ? (
          <View style={styles.headlinesList}>
            {headlines.map((headline, idx) => (
              <View key={`head-${idx}`} style={styles.headlineItem}>
                <MaterialCommunityIcons name="circle-medium" size={16} color={C.amber} />
                <Text style={styles.headlineText}>{headline}</Text>
              </View>
            ))}
          </View>
        ) : (
          <Text style={styles.noNewsText}>
            No severe trade or supply disruptions reported in monitored agricultural channels.
          </Text>
        )}
      </View>
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
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  headerTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    flex: 1,
  },
  cardTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: C.text,
  },
  riskBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
  },
  riskBadgeText: {
    fontSize: 10,
    fontWeight: '700',
  },
  signalText: {
    fontSize: 11.5,
    color: C.textSecondary,
    marginBottom: 10,
  },
  stationGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 10,
  },
  stationTile: {
    flex: 1,
    minWidth: '47%',
    backgroundColor: C.surface2,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 10,
    padding: 8,
  },
  stationTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  stationName: {
    fontSize: 11.5,
    fontWeight: '700',
    color: C.text,
  },
  miniBadge: {
    paddingHorizontal: 5,
    paddingVertical: 1,
    borderRadius: 4,
  },
  miniBadgeText: {
    fontSize: 8.5,
    fontWeight: '700',
  },
  stationDetail: {
    fontSize: 10,
    color: C.muted,
    lineHeight: 14,
  },
  boldWhite: {
    color: C.text,
    fontWeight: '700',
  },
  analysisBox: {
    backgroundColor: 'rgba(16, 185, 129, 0.08)',
    borderLeftWidth: 3,
    borderLeftColor: C.emerald,
    padding: 8,
    borderRadius: 6,
  },
  analysisText: {
    fontSize: 11,
    color: C.textSecondary,
    lineHeight: 15,
  },
  corroboratedGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginVertical: 8,
  },
  corroboratedItem: {
    flex: 1,
    minWidth: '47%',
    backgroundColor: C.surface2,
    borderRadius: 8,
    padding: 8,
    borderWidth: 1,
    borderColor: C.border,
  },
  corroboratedLabel: {
    fontSize: 9.5,
    color: C.muted,
    marginBottom: 2,
  },
  corroboratedVal: {
    fontSize: 11.5,
    fontWeight: '700',
    color: C.text,
  },
  corroboratedInterpretation: {
    fontSize: 10.5,
    color: C.textSecondary,
    lineHeight: 15,
    fontStyle: 'italic',
    marginTop: 4,
  },
  storageDetailsRow: {
    flexDirection: 'row',
    gap: 10,
    marginVertical: 6,
  },
  storageMetric: {
    flex: 1,
    backgroundColor: C.surface2,
    borderRadius: 10,
    padding: 10,
    borderWidth: 1,
    borderColor: C.border,
  },
  storageMetricLabel: {
    fontSize: 10,
    color: C.muted,
    marginBottom: 2,
  },
  storageMetricVal: {
    fontSize: 14,
    fontWeight: '800',
    color: C.text,
  },
  storageNote: {
    fontSize: 10.5,
    color: C.textSecondary,
    lineHeight: 15,
    marginTop: 6,
    fontStyle: 'italic',
  },
  locationsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'center',
    marginBottom: 8,
    padding: 6,
    backgroundColor: C.surface2,
    borderRadius: 6,
  },
  locationsLabel: {
    fontSize: 10.5,
    fontWeight: '700',
    color: C.amber,
  },
  locationsVal: {
    fontSize: 10.5,
    color: C.text,
  },
  headlinesList: {
    gap: 8,
    marginTop: 4,
  },
  headlineItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 4,
  },
  headlineText: {
    flex: 1,
    fontSize: 11.5,
    color: C.textSecondary,
    lineHeight: 16,
  },
  noNewsText: {
    fontSize: 11,
    color: C.muted,
    lineHeight: 16,
    fontStyle: 'italic',
  },
});
