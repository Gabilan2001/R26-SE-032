import { Platform } from 'react-native';
import fruitClient from './fruitClient';

export const predictFruitDisease = (formData) =>
  fruitClient.post('/predict', formData, {
    headers: {
      ...(Platform.OS !== 'web' ? { 'Content-Type': 'multipart/form-data' } : {}),
    },
  });

