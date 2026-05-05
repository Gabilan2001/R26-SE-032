import AsyncStorage from '@react-native-async-storage/async-storage';

const TOKEN_KEY = 'tomatodoc_token';

export const saveToken = (token) => AsyncStorage.setItem(TOKEN_KEY, token);
export const getToken = () => AsyncStorage.getItem(TOKEN_KEY);
export const clearToken = () => AsyncStorage.removeItem(TOKEN_KEY);
