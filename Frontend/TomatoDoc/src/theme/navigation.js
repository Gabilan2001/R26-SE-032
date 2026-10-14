import React from 'react';
import { Platform } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { palette, shadow } from './index';

/** Floating forest-green tab bar with a lime active state. Used by every tab navigator. */
export const tabOptions = (iconMap) => ({ route }) => ({
  headerShown: false,
  tabBarStyle: {
    backgroundColor: palette.forest,
    position: 'absolute',
    marginHorizontal: 16,
    marginBottom: Platform.OS === 'ios' ? 14 : 12,
    borderRadius: 26,
    height: 70,
    paddingBottom: 11,
    paddingTop: 8,
    borderTopWidth: 0,
    ...shadow.raised,
  },
  tabBarActiveTintColor: palette.lime,
  tabBarInactiveTintColor: 'rgba(255,255,255,0.55)',
  tabBarLabelStyle: { fontSize: 11, fontWeight: '700', letterSpacing: 0.2 },
  tabBarIcon: ({ color, size }) => (
    <MaterialCommunityIcons name={iconMap[route.name]} size={size} color={color} />
  ),
});

/** Header used by the few stack screens that show the native header. */
export const stackHeaderOptions = {
  headerStyle: { backgroundColor: palette.forest },
  headerTintColor: palette.onDark,
  headerTitleStyle: { fontWeight: '700' },
  headerShadowVisible: false,
  contentStyle: { backgroundColor: palette.bg },
};

/** Options for screens that live inside a tab navigator but must not appear as a tab. */
export const hiddenTab = {
  tabBarButton: () => null,
  tabBarItemStyle: { display: 'none' },
};
