import axios from 'axios';
import { Platform } from 'react-native';

const PRICE_API_BASE_URL =
  Platform.OS === 'web'
    ? 'http://127.0.0.1:8008'
    : process.env.EXPO_PUBLIC_PRICE_API_BASE_URL || 'http://10.0.2.2:8008';

const priceClient = axios.create({
  baseURL: PRICE_API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

priceClient.interceptors.response.use(
  (response) => response,
  (error) => {
    let friendlyMessage = 'Unable to connect to Price Prediction server.';
    if (error.code === 'ECONNABORTED') {
      friendlyMessage = 'Price Prediction server timed out. Check that the backend on port 8008 is running.';
    } else if (error.response && error.response.data && error.response.data.detail) {
      friendlyMessage = String(error.response.data.detail);
    } else if (error.message === 'Network Error') {
      friendlyMessage = `Cannot reach Price Prediction API at ${PRICE_API_BASE_URL}. Ensure the backend is running on port 8008.`;
    }
    error.friendlyMessage = friendlyMessage;
    return Promise.reject(error);
  }
);

/**
 * Fetch 14-day LSTM + Weather price forecast & decision engine recommendations.
 */
export async function fetchPricePrediction({ market, type, forecastHorizonDays = 14, targetDate = null }) {
  const payload = {
    market: market || 'Dambulla',
    type: type || 'Wholesale',
    forecast_horizon_days: forecastHorizonDays,
  };
  if (targetDate) {
    payload.target_date = targetDate;
  }
  const response = await priceClient.post('/predict/', payload);
  return response.data;
}

/**
 * Fetch monthly historical CPI-adjusted price range & ECMWF SEAS5 seasonal climate outlook.
 */
export async function fetchSeasonalForecast({ market, type, targetMonth, targetYear }) {
  const response = await priceClient.get('/seasonal-forecast/', {
    params: {
      market: market || 'Dambulla',
      type: type || 'Wholesale',
      target_month: targetMonth,
      target_year: targetYear,
    },
  });
  return response.data;
}

/**
 * Fetch market news intelligence and sentiment for the selected region.
 */
export async function fetchMarketNews(location = 'Dambulla-Wholesale') {
  const response = await priceClient.get('/news/market-analysis', {
    params: { location },
  });
  return response.data;
}

/**
 * Fetch supported market location labels.
 */
export async function fetchMarketLocations() {
  const response = await priceClient.get('/meta/locations');
  return response.data;
}

export default priceClient;
