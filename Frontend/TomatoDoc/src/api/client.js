import axios from 'axios';
import { Platform } from 'react-native';

// For Expo Web running in the browser on the same PC, `127.0.0.1` works.
// For real devices/emulators, you must use your PC's LAN IP instead.
const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL ||
  (Platform.OS === 'web'
    ? 'http://127.0.0.1:5000'
    : 'http://192.168.243.127:5000');

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 20000,
});

export default client;
