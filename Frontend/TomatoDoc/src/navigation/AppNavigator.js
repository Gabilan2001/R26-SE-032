import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import HomeScreen from '../screens/HomeScreen';
import ScanScreen from '../screens/ScanScreen';
import ResultScreen from '../screens/ResultScreen';
import DetailScreen from '../screens/DetailScreen';
import HistoryScreen from '../screens/HistoryScreen';
import StatsScreen from '../screens/StatsScreen';
import { colors } from '../constants/colors';

const Stack = createNativeStackNavigator();
const Tabs = createBottomTabNavigator();

function TabRoutes() {
  return (
    <Tabs.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.muted,
        tabBarIcon: ({ color, size }) => {
          const map = { Home: 'home', Scan: 'camera', History: 'history', Stats: 'chart-bar' };
          return <MaterialCommunityIcons name={map[route.name]} size={size} color={color} />;
        },
      })}
    >
      <Tabs.Screen name="Home" component={HomeScreen} />
      <Tabs.Screen name="Scan" component={ScanScreen} />
      <Tabs.Screen name="History" component={HistoryScreen} />
      <Tabs.Screen name="Stats" component={StatsScreen} />
    </Tabs.Navigator>
  );
}

export default function AppNavigator() {
  return (
    <Stack.Navigator>
      <Stack.Screen name="MainTabs" component={TabRoutes} options={{ headerShown: false }} />
      <Stack.Screen name="Result" component={ResultScreen} options={{ title: 'Analysis Result' }} />
      <Stack.Screen name="Detail" component={DetailScreen} options={{ title: 'Nutrient Detail' }} />
    </Stack.Navigator>
  );
}
