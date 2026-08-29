import axios from 'axios';

// Disease Detection backend (app_mobile.py) -- single-model (native-640,
// 4-class) lean backend + Gemini RAG treatment system, separate from the
// Nutrient (5000) and Fruit (5001) module backends.
//
// Now hosted on Google Cloud Run (asia-south1, project tomatodoc-hosting)
// instead of the local PC -- a public HTTPS URL, so no LAN IP/platform
// split is needed any more. Override via EXPO_PUBLIC_DISEASE_API_BASE_URL
// in a .env file if you ever need to point back at a local backend for
// debugging (e.g. http://172.20.10.3:5002 on your PC's current LAN IP).
const DISEASE_API_BASE_URL =
  process.env.EXPO_PUBLIC_DISEASE_API_BASE_URL ||
  'https://disease-detection-backend-518235913411.asia-south1.run.app';

const diseaseClient = axios.create({
  baseURL: DISEASE_API_BASE_URL,
  // Measured end-to-end (detection + background removal + Gemini RAG
  // treatment): ~15-90s depending on how many diseases co-occur (each gets
  // its own full treatment writeup). 30s was too short and caused timeouts
  // during testing -- 120s gives real headroom above the worst case seen.
  timeout: 120000,
});

export default diseaseClient;
