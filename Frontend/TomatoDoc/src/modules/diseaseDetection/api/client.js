import axios from 'axios';
import { API_BASE_URL } from '../config/env';

// Disease Detection backend (app_mobile.py) -- single-model (native-640,
// 4-class) lean backend + Gemini RAG treatment system, separate from the
// Nutrient (5000) and Fruit (5001) module backends.
const diseaseClient = axios.create({
  baseURL: API_BASE_URL,
  // Measured end-to-end (detection + background removal + Gemini RAG
  // treatment): ~15-90s depending on how many diseases co-occur (each gets
  // its own full treatment writeup). 30s was too short and caused timeouts
  // during testing -- 120s gives real headroom above the worst case seen.
  timeout: 120000,
});

export default diseaseClient;
