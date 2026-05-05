import client from './client';

const authHeader = (token) => ({ Authorization: `Bearer ${token}` });

export const getHistory = (token) => client.get('/history', { headers: authHeader(token) });
export const saveHistory = (token, payload) => client.post('/history', payload, { headers: authHeader(token) });
export const getStats = (token) => client.get('/stats', { headers: authHeader(token) });
