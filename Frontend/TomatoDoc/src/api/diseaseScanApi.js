import { Platform } from 'react-native';
import diseaseClient from './diseaseClient';

export const predictDisease = (formData) =>
  diseaseClient.post('/predict', formData, {
    headers: {
      ...(Platform.OS !== 'web' ? { 'Content-Type': 'multipart/form-data' } : {}),
    },
  });
