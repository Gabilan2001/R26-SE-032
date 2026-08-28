import axios from 'axios';
import { Platform } from 'react-native';

// Web on the same PC always uses localhost. Phone/emulator uses EXPO_PUBLIC_* or LAN IP.
const API_BASE_URL =
  Platform.OS === 'web'
    ? 'http://127.0.0.1:5002'
    : process.env.EXPO_PUBLIC_API_BASE_URL || 'http://192.168.225.179:5002';

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 20000,
});

export default client;
