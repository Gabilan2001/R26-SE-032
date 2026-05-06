import fruitClient from './fruitClient';

const authHeader = (token) => ({ Authorization: `Bearer ${token}` });

export const getFruitHistory = (token) =>
  fruitClient.get('/history', { headers: authHeader(token) });

export const saveFruitHistory = (token, payload) =>
  fruitClient.post('/history', payload, { headers: authHeader(token) });

export const getFruitStats = (token) =>
  fruitClient.get('/stats', { headers: authHeader(token) });

