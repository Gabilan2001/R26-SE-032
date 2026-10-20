import React, { createContext, useMemo, useState } from 'react';

import { palette as t } from '../theme';

// Kept for the screens that read the shared palette (primary/secondary/accent/danger/...).
const lightPalette = {
  primary: t.forestMid,
  secondary: t.leaf,
  accent: t.lime,
  danger: t.danger,
  healthy: t.good,
  white: t.surface,
  muted: t.muted,
  bg: t.bg,
  text: t.text,
  card: t.surface,
};

const darkPalette = {
  primary: t.lime,
  secondary: t.sprout,
  accent: t.lime,
  danger: '#EF6B67',
  healthy: '#8FD694',
  white: '#16372B',
  muted: '#9DB3A6',
  bg: '#0B261C',
  text: '#F3F7F0',
  card: '#12382B',
};

export const UIThemeContext = createContext(null);

export function UIThemeProvider({ children }) {
  const [isDark, setIsDark] = useState(false);

  const value = useMemo(
    () => ({
      isDark,
      palette: isDark ? darkPalette : lightPalette,
      toggleTheme: () => setIsDark((prev) => !prev),
    }),
    [isDark],
  );

  return <UIThemeContext.Provider value={value}>{children}</UIThemeContext.Provider>;
}

