import diseaseClient from './client';

// Disease module's own history/stats -- backed by Firestore on app_mobile.py,
// independent of the Nutrient/Fruit modules' shared MongoDB + login. No auth
// required, no user_id -- a single shared scan log for this module.

export const getDiseaseHistory = (limit = 30) =>
  diseaseClient.get('/history', { params: { limit } });

export const getDiseaseStats = () =>
  diseaseClient.get('/stats');
