import axios from 'axios';

// Nutrient Deficiency API (also serves /auth). Hosted on Render; override with
// EXPO_PUBLIC_API_BASE_URL in .env to point at a local backend.
const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL || 'https://tomatodoc-nutrient.onrender.com';

// Render's free plan sleeps when idle and takes up to ~1 minute to wake.
const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
});

export default client;
