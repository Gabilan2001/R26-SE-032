// Disease Detection API base URL resolution -- split out from api/client.js
// for consistency with the Disease Monitoring module's config/env.ts pattern.
//
// Hosted on Google Cloud Run (asia-south1, project tomatodoc-hosting) --
// a public HTTPS URL, so no LAN IP/platform split is needed. Override via
// EXPO_PUBLIC_DISEASE_API_BASE_URL in a .env file if you ever need to point
// back at a local backend for debugging (e.g. http://<your-LAN-IP>:5002).
export const API_BASE_URL =
  process.env.EXPO_PUBLIC_DISEASE_API_BASE_URL ||
  'https://disease-detection-backend-518235913411.asia-south1.run.app';
