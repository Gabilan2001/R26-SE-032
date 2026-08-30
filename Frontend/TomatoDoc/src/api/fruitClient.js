import axios from 'axios';
import { Platform } from 'react-native';

const FRUIT_API_BASE_URL =
  Platform.OS === 'web'
    ? 'http://127.0.0.1:5001'
    : process.env.EXPO_PUBLIC_FRUIT_API_BASE_URL || 'http://192.168.225.179:5001';

const fruitClient = axios.create({
  baseURL: FRUIT_API_BASE_URL,
  timeout: 30000,
});

fruitClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNABORTED') {
      error.message = 'Fruit server timed out. Check that the backend on port 5001 is running and MongoDB is connected.';
    } else if (error.message === 'Network Error') {
      error.message = `Cannot reach fruit API at ${FRUIT_API_BASE_URL}. Update EXPO_PUBLIC_FRUIT_API_BASE_URL in .env.`;
    }
    return Promise.reject(error);
  }
);

export default fruitClient;

