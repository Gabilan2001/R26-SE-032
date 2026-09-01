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
  const structAgri = regImpact ? regImpact.structured_agricultural_assessment : null;
  const corroborated = predictionData ? predictionData.corroborated_signals : null;
  const storage = regImpact ? regImpact.market_storage_impact : null;

  // News Data
  const newsMood = newsData ? newsData.news_sentiment || 'neutral' : 'neutral';
  const headlines = newsData && Array.isArray(newsData.relevant_headlines) ? newsData.relevant_headlines.slice(0, 5) : [];
  const detectedLocations = newsData && Array.isArray(newsData.detected_locations) ? newsData.detected_locations : [];

  let riskBadgeColor = C.emerald;
  let riskBadgeBg = C.emeraldDim;
  if (overallRisk === 'SEVERE') {
    riskBadgeColor = C.red;
    riskBadgeBg = C.redDim;
  } else if (overallRisk === 'MODERATE') {
    riskBadgeColor = C.amber;
    riskBadgeBg = C.amberDim;
  }

  // 4 Key Hub Definitions with farmer-intuitive status mapping
  const hubList = [
    {
      name: 'Anuradhapura',
      defaultLabel: 'Dry / Minor Water Deficit',
      defaultColor: C.amber,
      defaultBg: C.amberDim,
      defaultIcon: '🟡',
      defaultNote: 'Tank water levels lower; monitor upcoming planting irrigation.',
    },
    {
      name: 'Dambulla',
      defaultLabel: 'Favourable / Normal Harvest',
      defaultColor: C.emerald,
      defaultBg: C.emeraldDim,
      defaultIcon: '🟢',
      defaultNote: 'Regular harvesting conditions across trading hub suppliers.',
    },
    {
      name: 'Nuwara Eliya',
      defaultLabel: 'Balanced Conditions',
      defaultColor: C.emerald,
      defaultBg: C.emeraldDim,
      defaultIcon: '🟢',
      defaultNote: 'Favourable highland temperature and soil moisture levels.',
    },
    {
      name: 'Badulla',
      defaultLabel: 'Higher Rainfall Expected',
      defaultColor: C.blue,
      defaultBg: 'rgba(59, 130, 246, 0.12)',
      defaultIcon: '🔵',
      defaultNote: 'Adequate rain supporting active vegetable crop growth.',
    },
  ];

  return (
    <View style={styles.container}>
      {/* 1. Regional Weather Risk Card */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <View style={styles.headerTitleRow}>
            <MaterialCommunityIcons name="weather-partly-cloudy" size={18} color={C.amber} />
            <Text style={styles.cardTitle}>Supply Hub Weather & Water Stress</Text>
          </View>
          <View style={[styles.riskBadge, { backgroundColor: riskBadgeBg }]}>
            <Text style={[styles.riskBadgeText, { color: riskBadgeColor }]}>
              {season} Season · {overallRisk === 'LOW' ? 'Stable' : overallRisk}
            </Text>
          </View>
        </View>

        <Text style={styles.signalText}>
          Primary Focus: <Text style={{ fontWeight: '700', color: C.text }}>{primaryRegion}</Text> ({structAgri?.agro_ecological_zone || 'Dry Zone Agro Hub'})
        </Text>

        {/* 4 Clean Hub Status Cards */}
        <View style={styles.stationGrid}>
          {hubList.map((hub) => {
            const stData = regions[hub.name] || {};
            const waterStatus = stData.water_status || '';

            let statusLabel = hub.defaultLabel;
            let stColor = hub.defaultColor;
            let stBg = hub.defaultBg;
            let statusIcon = hub.defaultIcon;

            if (waterStatus === 'SEVERE_DROUGHT_STRESS') {
              statusLabel = 'Severe Water Deficit';
              stColor = C.red;
              stBg = C.redDim;
              statusIcon = '🔴';
            } else if (waterStatus === 'MODERATE_WATER_DEFICIT') {
              statusLabel = 'Dry / Minor Deficit';
              stColor = C.amber;
              stBg = C.amberDim;
              statusIcon = '🟡';
            } else if (waterStatus === 'EXCESS_WATER_SATURATION') {
              statusLabel = 'Excess Rain Risk';
              stColor = C.red;
              stBg = C.redDim;
              statusIcon = '🌧️';
            } else if (waterStatus === 'ELEVATED_MOISTURE') {
              statusLabel = 'Higher Rainfall Expected';
              stColor = C.blue;
              stBg = 'rgba(59, 130, 246, 0.12)';
              statusIcon = '🔵';
            } else if (waterStatus === 'OPTIMAL_BALANCED') {
              statusLabel = 'Favourable / Balanced';
              stColor = C.emerald;
              stBg = C.emeraldDim;
              statusIcon = '🟢';
            }

            return (
              <View key={hub.name} style={styles.stationTile}>
                <View style={styles.stationTop}>
                  <Text style={styles.stationName}>📍 {hub.name}</Text>
                  <View style={[styles.miniBadge, { backgroundColor: stBg }]}>
                    <Text style={[styles.miniBadgeText, { color: stColor }]}>
                      {statusIcon} {statusLabel}
                    </Text>
                  </View>
                </View>
                <Text style={styles.hubNoteText}>{hub.defaultNote}</Text>
              </View>
            );
          })}
        </View>

        {/* Short, Concise Planting & Water Summary */}
        <View style={styles.analysisBox}>
          <Text style={styles.analysisText}>
            <Text style={{ fontWeight: '700', color: C.emerald }}>Agro Advisory: </Text>
            Dry conditions in Anuradhapura are reducing tank water levels. Current market arrivals remain steady, but water shortages may temper upcoming planting schedules in the dry zone.
          </Text>
        </View>
      </View>

      {/* 2. Regional Supply Outlook Card */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <View style={styles.headerTitleRow}>
            <MaterialCommunityIcons name="truck-delivery-outline" size={18} color={C.amber} />
            <Text style={styles.cardTitle}>Regional Supply Outlook</Text>
          </View>
          <View style={[styles.riskBadge, { backgroundColor: C.surface2 }]}>
            <Text style={[styles.riskBadgeText, { color: C.amber }]}>
              {corroborated?.confidence || 'High'} Agreement
            </Text>
          </View>
        </View>

        <View style={styles.corroboratedGrid}>
          <View style={styles.corroboratedItem}>
            <Text style={styles.corroboratedLabel}>Supply Hub</Text>
            <Text style={styles.corroboratedVal}>{corroborated?.primary_region || primaryRegion}</Text>
          </View>
          <View style={styles.corroboratedItem}>
            <Text style={styles.corroboratedLabel}>Impact Window</Text>
            <Text style={styles.corroboratedVal}>{corroborated?.impact_time_horizon || 'Next 3–4 Weeks'}</Text>
          </View>
        </View>

        <Text style={styles.takeawayText}>
          Dry conditions in Anuradhapura are reducing tank water levels. Current market arrivals remain steady, but upcoming harvests in 3–4 weeks may see reduced volumes.
        </Text>
      </View>

      {/* 3. Fresh Produce Storage & Shelf-Life Card */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <View style={styles.headerTitleRow}>
            <MaterialCommunityIcons name="timer-sand" size={18} color={C.emerald} />
            <Text style={styles.cardTitle}>
              Produce Storage & Shelf-Life
            </Text>
          </View>
          <View style={[styles.riskBadge, { backgroundColor: C.emeraldDim }]}>
            <Text style={[styles.riskBadgeText, { color: C.emerald }]}>
              Shelf-Life: 3–5 Days
            </Text>
          </View>
        </View>

        <View style={styles.storageTipBox}>
          <MaterialCommunityIcons name="alert-circle-outline" size={20} color={C.emerald} />
          <View style={{ flex: 1 }}>
            <Text style={styles.storageTipTitle}>Fresh Produce Shelf-Life: 3–5 Days</Text>
            <Text style={styles.storageTipBody}>
              Tomatoes should be dispatched within 3 days unless cold storage is available to avoid heat-related fruit softening.
            </Text>
          </View>
        </View>

        {storage && (
          <View style={styles.storageMetaRow}>
            <Text style={styles.storageMetaText}>
              Ambient Temperature: {storage.ambient_temp_3d_avg_c != null ? `${storage.ambient_temp_3d_avg_c.toFixed(0)}°C` : '27°C'} · Selling Urgency:{' '}
              <Text style={{ fontWeight: '700', color: storage.selling_urgency === 'URGENT' ? C.red : C.emerald }}>
                {storage.selling_urgency || 'Normal'}
              </Text>
            </Text>
          </View>
        )}
      </View>

      {/* 4. Market News & Intelligence Card */}
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
    padding: 9,
  },
  stationTop: {
    flexDirection: 'column',
    alignItems: 'flex-start',
    gap: 4,
    marginBottom: 4,
  },
  stationName: {
    fontSize: 12,
    fontWeight: '700',
    color: C.text,
  },
  miniBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  miniBadgeText: {
    fontSize: 9,
    fontWeight: '700',
  },
  hubNoteText: {
    fontSize: 10,
    color: C.muted,
    lineHeight: 14,
    marginTop: 2,
  },
  analysisBox: {
    backgroundColor: 'rgba(16, 185, 129, 0.08)',
    borderLeftWidth: 3,
    borderLeftColor: C.emerald,
    padding: 10,
    borderRadius: 6,
  },
  analysisText: {
    fontSize: 11,
    color: C.textSecondary,
    lineHeight: 16,
  },
  corroboratedGrid: {
    flexDirection: 'row',
    gap: 8,
    marginVertical: 8,
  },
  corroboratedItem: {
    flex: 1,
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
    fontSize: 12,
    fontWeight: '700',
    color: C.text,
  },
  takeawayText: {
    fontSize: 11.5,
    color: C.text,
    lineHeight: 17,
    backgroundColor: 'rgba(245, 158, 11, 0.06)',
    borderLeftWidth: 3,
    borderLeftColor: C.amber,
    padding: 10,
    borderRadius: 6,
    marginTop: 4,
  },
  storageTipBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: 'rgba(16, 185, 129, 0.08)',
    borderLeftWidth: 3,
    borderLeftColor: C.emerald,
    padding: 10,
    borderRadius: 8,
    gap: 8,
    marginVertical: 6,
  },
  storageTipTitle: {
    fontSize: 11.5,
    fontWeight: '700',
    color: C.emerald,
    marginBottom: 2,
  },
  storageTipBody: {
    fontSize: 11,
    color: C.textSecondary,
    lineHeight: 16,
  },
  storageMetaRow: {
    marginTop: 4,
    paddingHorizontal: 4,
  },
  storageMetaText: {
    fontSize: 10,
    color: C.muted,
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
