import axios from 'axios';

// Tomato Fruit Disease API. Hosted on Render; override with
// EXPO_PUBLIC_FRUIT_API_BASE_URL in .env to point at a local backend.
const FRUIT_API_BASE_URL =
  process.env.EXPO_PUBLIC_FRUIT_API_BASE_URL || 'https://tomatodoc-fruit.onrender.com';

// Render's free plan sleeps when idle and takes up to ~1 minute to wake.
const fruitClient = axios.create({
  baseURL: FRUIT_API_BASE_URL,
  timeout: 60000,
});

fruitClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNABORTED') {
      error.message = `Fruit server timed out at ${FRUIT_API_BASE_URL}. It may be waking up — please try again.`;
    } else if (error.message === 'Network Error') {
      error.message = `Cannot reach fruit API at ${FRUIT_API_BASE_URL}. Update EXPO_PUBLIC_FRUIT_API_BASE_URL in .env.`;
    }
    return Promise.reject(error);
  }
);

export default fruitClient;

