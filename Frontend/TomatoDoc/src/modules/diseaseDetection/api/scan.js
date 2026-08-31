import { Platform } from 'react-native';
import diseaseClient from './client';
import { getSkipBgRemoval } from '../config/devSettings';

export const predictDisease = (formData) => {
  // Testing toggle, off by default -- see config/devSettings.js and
  // screens/DiseaseSettingsScreen.js.
  formData.append('skip_bg_removal', getSkipBgRemoval() ? 'true' : 'false');
  return diseaseClient.post('/predict', formData, {
    headers: {
      ...(Platform.OS !== 'web' ? { 'Content-Type': 'multipart/form-data' } : {}),
    },
  });
};

// Second phase, called right after predictDisease resolves -- fetches the
// RAG/Gemini treatment advice separately (that call alone can take up to
// ~90s) so the result screen can show the detection immediately instead of
// waiting for everything before showing anything.
export const getTreatment = (detections, diseasesFound, coOccurrence) =>
  diseaseClient.post('/treatment', {
    detections,
    diseases_found: diseasesFound,
    co_occurrence: coOccurrence,
  });
