import React, { createContext, useMemo, useState } from 'react';

const lightPalette = {
  primary: '#2E7D32',
  secondary: '#81C784',
  accent: '#FF6F00',
  danger: '#C62828',
  healthy: '#2E7D32',
  white: '#FFFFFF',
  muted: '#9E9E9E',
  bg: '#F5F8F5',
  text: '#1B1B1B',
  card: '#FFFFFF',
};

const darkPalette = {
  primary: '#D7FF3F',
  secondary: '#AEEA00',
  accent: '#E6FF55',
  danger: '#EF5350',
  healthy: '#B2FF59',
  white: '#1F1F1F',
  muted: '#B0B0B0',
  bg: '#0E1014',
  text: '#F5F7FA',
  card: '#171A20',
};

export const UIThemeContext = createContext(null);

export function UIThemeProvider({ children }) {
  const [isDark, setIsDark] = useState(false);
  const [presentationMode, setPresentationMode] = useState(false);

  const value = useMemo(
    () => ({
      isDark,
      presentationMode,
      palette: isDark ? darkPalette : lightPalette,
      toggleTheme: () => setIsDark((prev) => !prev),
      togglePresentationMode: () => setPresentationMode((prev) => !prev),
    }),
    [isDark, presentationMode],
  );

  return <UIThemeContext.Provider value={value}>{children}</UIThemeContext.Provider>;
}

