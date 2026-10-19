// Disease class -> display color. Must stay in sync with CLASS_COLORS_BGR in
// app_mobile.py (that's BGR, this is the RGB hex equivalent) -- these colors
// are what the backend draws the annotation boxes with, so the chips here
// need to visually match. Shared between DiseaseResultScreen (scan result
// chips) and DiseaseHistoryScreen (past-scan list chips).
export const CLASS_COLORS = {
  Early_Blight: '#ff6432',
  Late_Blight:  '#32b4ff',
  Healthy:      '#3cc83c',
  Leaf_Miner:   '#ffa500',
};
