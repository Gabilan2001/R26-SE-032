import axios from 'axios';
import { Platform } from 'react-native';

const FRUIT_API_BASE_URL =
  process.env.EXPO_PUBLIC_FRUIT_API_BASE_URL ||
  (Platform.OS === 'web'
    ? 'http://127.0.0.1:5001'
    : 'http://192.168.243.127:5001');

const fruitClient = axios.create({
  baseURL: FRUIT_API_BASE_URL,
  timeout: 20000,
});

export default fruitClient;

