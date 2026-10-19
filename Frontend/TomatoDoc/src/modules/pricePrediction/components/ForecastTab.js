import React from 'react';
import { StyleSheet, View } from 'react-native';
import RecommendationBanner from './RecommendationBanner';
import MetricTiles from './MetricTiles';
import ForecastChart from './ForecastChart';
import ForecastTable from './ForecastTable';
import TechnicalDetailsCard from './TechnicalDetailsCard';

export default function ForecastTab({ data }) {
  if (!data) return null;

  return (
    <View style={styles.container}>
      <RecommendationBanner data={data} />
      <MetricTiles data={data} />
      <ForecastChart data={data} />
      <ForecastTable data={data} />
      <TechnicalDetailsCard data={data} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingTop: 4,
    paddingBottom: 20,
  },
});
