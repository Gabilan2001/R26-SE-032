// Shared TomatoDoc light theme (see src/theme); the price module keeps amber as its accent.
export const C = {
  bg: '#FBFAF5',
  surface: '#FFFFFF',
  surface2: '#F3F5EE',
  text: '#1E3027',
  textSecondary: '#4D5C53',
  muted: '#5E6E64',
  border: '#E3E8DF',
  borderLight: '#CFD8CA',

  // Price Prediction module accent tokens
  amber: '#C98A12',
  amberDim: '#FBF1DA',
  amberBorder: '#EBD59B',

  emerald: '#2F8F4E',
  emeraldDim: '#E4F4E8',
  emeraldBorder: '#BFE3C8',

  red: '#D64545',
  redDim: '#FDECEA',
  redBorder: '#F4C7C3',

  blue: '#2C6E9B',
  blueDim: '#E6F1F8',
  blueBorder: '#BFD8E8',

  purple: '#7C5CBF',
  purpleDim: '#EFE9FA',
  purpleBorder: '#D5C8EE',
};

export const SUPPORTED_MARKETS = [
  { id: 'Dambulla-Wholesale', market: 'Dambulla', type: 'Wholesale', label: 'Dambulla — Wholesale' },
  { id: 'Dambulla-Retail', market: 'Dambulla', type: 'Retail', label: 'Dambulla — Retail' },
  { id: 'Pettah-Wholesale', market: 'Pettah', type: 'Wholesale', label: 'Pettah (Colombo) — Wholesale' },
  { id: 'Pettah-Retail', market: 'Pettah', type: 'Retail', label: 'Pettah (Colombo) — Retail' },
];
