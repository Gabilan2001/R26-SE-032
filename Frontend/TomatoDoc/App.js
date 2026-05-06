import React from 'react';
import { MD3DarkTheme, MD3LightTheme, Provider as PaperProvider } from 'react-native-paper';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import RootNavigator from './src/navigation/RootNavigator';
import { AuthProvider } from './src/context/AuthContext';
import { UIThemeContext, UIThemeProvider } from './src/context/UIThemeContext';

export default function App() {
  return (
    <SafeAreaProvider>
      <UIThemeProvider>
        <UIThemeContext.Consumer>
          {({ palette, isDark }) => {
            const baseTheme = isDark ? MD3DarkTheme : MD3LightTheme;
            const theme = {
              ...baseTheme,
              colors: {
                ...baseTheme.colors,
                primary: palette.primary,
                secondary: palette.secondary,
                surface: palette.card,
                background: palette.bg,
                error: palette.danger,
                onSurface: palette.text,
              },
            };
            return (
              <PaperProvider theme={theme}>
                <AuthProvider>
                  <RootNavigator />
                </AuthProvider>
              </PaperProvider>
            );
          }}
        </UIThemeContext.Consumer>
      </UIThemeProvider>
    </SafeAreaProvider>
  );
}
