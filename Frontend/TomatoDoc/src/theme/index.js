// TomatoDoc design tokens. The look follows the project's portfolio site: a warm cream page,
// deep forest-green hero areas with glassy cards, a lime accent and soft rounded cards.
// Screens import from here so every module (Nutrient, Fruit, Disease, Monitoring, Price) shares
// one visual language. Nothing in this file affects application logic.
import { Platform } from 'react-native';

export const palette = {
  // Surfaces
  bg: '#FBFAF5', // page background (cream)
  surface: '#FFFFFF', // cards
  surface2: '#F3F5EE', // inputs, quiet panels
  surfaceTint: '#EDF6DF', // soft green highlight
  border: '#E3E8DF',
  borderStrong: '#CFD8CA',

  // Greens (from the portfolio)
  forest: '#12382B', // deepest green: hero, headers, tab bar
  forestMid: '#1F6044', // primary actions
  forestSoft: '#2D7A52',
  leaf: '#56823C',
  sprout: '#6B9C52', // eyebrow labels
  lime: '#D6EF75', // accent on dark green
  limeDim: 'rgba(214,239,117,0.16)',

  // Text
  text: '#1E3027',
  textSoft: '#4D5C53',
  muted: '#5E6E64',
  onDark: '#FFFFFF',
  onDarkSoft: 'rgba(255,255,255,0.72)',
  onDarkMuted: 'rgba(255,255,255,0.55)',

  // Status
  danger: '#D64545',
  dangerDim: '#FDECEA',
  dangerBorder: '#F4C7C3',
  warn: '#B7791F',
  warnDim: '#FBF1DA',
  warnBorder: '#EBD59B',
  good: '#2F8F4E',
  goodDim: '#E4F4E8',
  goodBorder: '#BFE3C8',
  info: '#2C6E9B',
  infoDim: '#E6F1F8',
  gold: '#C6A94C',
  tomato: '#E34A3B',
  tomatoDim: '#FDEDEA',
};

export const gradients = {
  hero: ['#0E3326', '#1B5A3F', '#357A4A'],
  heroSoft: ['#154734', '#1F6044'],
  lime: ['#D6EF75', '#B9DE5C'],
};

export const radius = { xs: 8, sm: 12, md: 16, lg: 20, xl: 28, pill: 999 };

export const space = { xs: 4, sm: 8, md: 12, lg: 16, xl: 20, xxl: 28 };

export const shadow = {
  card: Platform.select({
    web: { boxShadow: '0 6px 18px rgba(18,56,43,0.07)' },
    default: { shadowColor: '#12382B', shadowOpacity: 0.08, shadowRadius: 14, shadowOffset: { width: 0, height: 6 }, elevation: 3 },
  }),
  raised: Platform.select({
    web: { boxShadow: '0 14px 30px rgba(18,56,43,0.16)' },
    default: { shadowColor: '#12382B', shadowOpacity: 0.16, shadowRadius: 24, shadowOffset: { width: 0, height: 12 }, elevation: 8 },
  }),
};

export const type = {
  // Small uppercase labels ("eyebrow"), as on the portfolio site.
  eyebrow: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.6,
    textTransform: 'uppercase',
    color: palette.sprout,
    fontFamily: Platform.select({ ios: 'Menlo', android: 'monospace', default: 'monospace' }),
  },
  h1: { fontSize: 30, fontWeight: '800', letterSpacing: -0.8, color: palette.text },
  h2: { fontSize: 22, fontWeight: '800', letterSpacing: -0.5, color: palette.text },
  h3: { fontSize: 17, fontWeight: '700', letterSpacing: -0.2, color: palette.text },
  body: { fontSize: 14, lineHeight: 21, color: palette.textSoft },
  small: { fontSize: 12, lineHeight: 17, color: palette.muted },
};

export const theme = { palette, gradients, radius, space, shadow, type };
export default theme;
