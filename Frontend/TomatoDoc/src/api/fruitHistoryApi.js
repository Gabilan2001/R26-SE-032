import fruitClient from './fruitClient';

const authHeaders = (token) => {
  if (!token) {
    throw new Error('You must be logged in to access fruit scan history.');
  }
  return {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  };
};

export const getFruitHistory = (token) =>
  fruitClient.get('/history', { headers: authHeaders(token) });

export const saveFruitHistory = (token, payload) =>
  fruitClient.post('/history', payload, { headers: authHeaders(token) });

export const getFruitStats = (token) =>
  fruitClient.get('/stats', { headers: authHeaders(token) });

