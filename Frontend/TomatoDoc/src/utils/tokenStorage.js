import AsyncStorage from '@react-native-async-storage/async-storage';

const TOKEN_KEY = 'tomatodoc_token';
const USER_KEY = 'tomatodoc_user';

export const saveToken = (token) => AsyncStorage.setItem(TOKEN_KEY, token);
export const getToken = () => AsyncStorage.getItem(TOKEN_KEY);
export const clearToken = () => AsyncStorage.removeItem(TOKEN_KEY);

export const saveUser = (user) => AsyncStorage.setItem(USER_KEY, JSON.stringify(user || null));
export const getUser = async () => {
  const raw = await AsyncStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch (_) {
    return null;
  }
};
export const clearUser = () => AsyncStorage.removeItem(USER_KEY);
