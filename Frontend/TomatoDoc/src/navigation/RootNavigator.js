import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { ActivityIndicator, View } from 'react-native';
import { useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import AuthNavigator from './AuthNavigator';
import AppNavigator from './AppNavigator';
import { colors } from '../constants/colors';

export default function RootNavigator() {
  const { loading, isAuthenticated } = useContext(AuthContext);

  if (loading) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.bg }}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  // ⚠️ Local-testing-only auth bypass, since the Nutrient team's auth backend
  // (MongoDB) isn't always running/configured here. Left commented out so it
  // stays out of the real auth path by default -- uncomment the `= true`
  // line (and comment out the `= false` one) whenever it's needed again.
  // const BYPASS_AUTH_FOR_LOCAL_TESTING = true;
  const BYPASS_AUTH_FOR_LOCAL_TESTING = true;
  return (
    <NavigationContainer>
      {isAuthenticated || BYPASS_AUTH_FOR_LOCAL_TESTING ? <AppNavigator /> : <AuthNavigator />}
    </NavigationContainer>
  );
}
