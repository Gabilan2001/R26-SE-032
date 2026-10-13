import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  RefreshControl,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { C } from '../constants/priceTheme';
import ScreenHeader from '../../../components/ScreenHeader';
import { fetchMarketNews, fetchPricePrediction } from '../api/priceClient';
import MarketSelector from '../components/MarketSelector';
import ForecastTab from '../components/ForecastTab';
import InsightsTab from '../components/InsightsTab';
import PlanningTab from '../components/PlanningTab';

export default function PricePredictionScreen({ navigation }) {
  const insets = useSafeAreaInsets();
  const [activeTab, setActiveTab] = useState('forecast'); // 'forecast' | 'insights' | 'planning'

  const [selectedMarket, setSelectedMarket] = useState('Dambulla');
  const [selectedType, setSelectedType] = useState('Wholesale');

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [predictionData, setPredictionData] = useState(null);
  const [newsData, setNewsData] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  const loadData = async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setErrorMessage('');

    try {
      const locationStr = `${selectedMarket}-${selectedType}`;
      const [pred, news] = await Promise.all([
        fetchPricePrediction({
          market: selectedMarket,
          type: selectedType,
          forecastHorizonDays: 14,
        }),
        fetchMarketNews(locationStr).catch(() => null),
      ]);

      setPredictionData(pred);
      setNewsData(news);
    } catch (err) {
      setErrorMessage(
        err.friendlyMessage || 'Unable to connect to Price Prediction service. Ensure the backend is running on port 8008.'
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedMarket, selectedType]);

  const handleMarketSelect = (market, type) => {
    setSelectedMarket(market);
    setSelectedType(type);
  };

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" backgroundColor="#12382B" />

      {/* Top Header */}
      <ScreenHeader
        title="Tomato Price Advisor"
        subtitle="Agro Intelligence · AI Advisor"
        eyebrow="Price module"
        onBack={() => navigation.goBack()}
        right={
          <TouchableOpacity
            style={styles.reloadBtn}
            onPress={() => loadData(true)}
            disabled={loading || refreshing}
            activeOpacity={0.7}
          >
            <MaterialCommunityIcons
              name="refresh"
              size={20}
              color={loading || refreshing ? 'rgba(255,255,255,0.4)' : '#D6EF75'}
            />
          </TouchableOpacity>
        }
      />

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => loadData(true)}
            tintColor={C.amber}
            colors={[C.amber]}
          />
        }
      >
        {/* Market & Series Selector */}
        <MarketSelector
          selectedMarket={selectedMarket}
          selectedType={selectedType}
          onSelect={handleMarketSelect}
        />

        {/* 3-Segmented Navigation Tabs */}
        <View style={styles.tabBar}>
          <TouchableOpacity
            style={[styles.tabBtn, activeTab === 'forecast' && styles.tabBtnActive]}
            onPress={() => setActiveTab('forecast')}
            activeOpacity={0.75}
          >
            <MaterialCommunityIcons
              name="chart-line"
              size={16}
              color={activeTab === 'forecast' ? C.amber : C.muted}
            />
            <Text
              style={[styles.tabText, activeTab === 'forecast' && styles.tabTextActive]}
            >
              Forecast
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.tabBtn, activeTab === 'insights' && styles.tabBtnActive]}
            onPress={() => setActiveTab('insights')}
            activeOpacity={0.75}
          >
            <MaterialCommunityIcons
              name="weather-partly-cloudy"
              size={16}
              color={activeTab === 'insights' ? C.amber : C.muted}
            />
            <Text
              style={[styles.tabText, activeTab === 'insights' && styles.tabTextActive]}
            >
              Insights
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.tabBtn, activeTab === 'planning' && styles.tabBtnActive]}
            onPress={() => setActiveTab('planning')}
            activeOpacity={0.75}
          >
            <MaterialCommunityIcons
              name="calendar-month"
              size={16}
              color={activeTab === 'planning' ? C.amber : C.muted}
            />
            <Text
              style={[styles.tabText, activeTab === 'planning' && styles.tabTextActive]}
            >
              Planning
            </Text>
          </TouchableOpacity>
        </View>

        {/* Loading Spinner */}
        {loading && !refreshing ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={C.amber} />
            <Text style={styles.loadingText}>Analyzing market price & weather signals...</Text>
          </View>
        ) : null}

        {/* Error Banner */}
        {!loading && errorMessage && !predictionData ? (
          <View style={styles.errorCard}>
            <MaterialCommunityIcons name="alert-circle-outline" size={24} color={C.red} />
            <View style={{ flex: 1 }}>
              <Text style={styles.errorTitle}>Connection Notice</Text>
              <Text style={styles.errorBody}>{errorMessage}</Text>
            </View>
            <TouchableOpacity
              style={styles.retryBtn}
              onPress={() => loadData(false)}
              activeOpacity={0.8}
            >
              <Text style={styles.retryText}>Retry</Text>
            </TouchableOpacity>
          </View>
        ) : null}

        {/* Active Tab Body */}
        {!loading && (
          <>
            {activeTab === 'forecast' && <ForecastTab data={predictionData} />}
            {activeTab === 'insights' && (
              <InsightsTab predictionData={predictionData} newsData={newsData} />
            )}
            {activeTab === 'planning' && (
              <PlanningTab selectedMarket={selectedMarket} selectedType={selectedType} />
            )}
          </>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: C.bg,
  },
  reloadBtn: {
    width: 40,
    height: 40,
    borderRadius: 14,
    backgroundColor: 'rgba(255,255,255,0.10)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.18)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  scrollContent: {
    paddingTop: 16,
    paddingBottom: 120,
  },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: C.surface,
    marginHorizontal: 16,
    borderRadius: 12,
    padding: 4,
    borderWidth: 1,
    borderColor: C.border,
    marginBottom: 12,
  },
  tabBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 9,
    borderRadius: 8,
    gap: 6,
  },
  tabBtnActive: {
    backgroundColor: C.surface2,
    borderWidth: 1,
    borderColor: C.amberBorder,
  },
  tabText: {
    fontSize: 12,
    fontWeight: '600',
    color: C.muted,
  },
  tabTextActive: {
    color: C.amber,
    fontWeight: '700',
  },
  loadingContainer: {
    padding: 30,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 12,
    color: C.muted,
    fontWeight: '500',
  },
  errorCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: C.redDim,
    borderWidth: 1,
    borderColor: C.redBorder,
    marginHorizontal: 16,
    marginBottom: 14,
    padding: 14,
    borderRadius: 12,
  },
  errorTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: C.red,
  },
  errorBody: {
    fontSize: 11,
    color: C.textSecondary,
    marginTop: 2,
    lineHeight: 15,
  },
  retryBtn: {
    backgroundColor: C.red,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 6,
  },
  retryText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#fff',
  },
});
