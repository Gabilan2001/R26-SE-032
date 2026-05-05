import client from './client';
import { Platform } from 'react-native';

export const predictNutrient = (formData, token) =>
  client.post('/predict', formData, {
    headers: {
      ...(Platform.OS !== 'web' ? { 'Content-Type': 'multipart/form-data' } : {}),
      Authorization: token ? `Bearer ${token}` : undefined,
    },
  });
