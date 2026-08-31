import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useContext } from 'react';
import HomeScreen from '../screens/HomeScreen';
import UserScreen from '../screens/UserScreen';
import ScanScreen from '../screens/ScanScreen';
import ResultScreen from '../screens/ResultScreen';
import DetailScreen from '../screens/DetailScreen';
import HistoryScreen from '../screens/HistoryScreen';
import StatsScreen from '../screens/StatsScreen';
import FruitScanScreen from '../screens/FruitScanScreen';
import FruitResultScreen from '../screens/FruitResultScreen';
import FruitDetailScreen from '../screens/FruitDetailScreen';
import DiseaseMonitoringFlowScreen from '../modules/diseaseMonitoring/DiseaseMonitoringFlowScreen';
import DiseaseScanScreen from '../modules/diseaseDetection/screens/DiseaseScanScreen';
import DiseaseResultScreen from '../modules/diseaseDetection/screens/DiseaseResultScreen';
import DiseaseHistoryScreen from '../modules/diseaseDetection/screens/DiseaseHistoryScreen';
import DiseaseSettingsScreen from '../modules/diseaseDetection/screens/DiseaseSettingsScreen';
import { UIThemeContext } from '../context/UIThemeContext';

const Stack = createNativeStackNavigator();
const Tabs = createBottomTabNavigator();
const ModuleTabs = createBottomTabNavigator();

function TabRoutes() {
  const { palette } = useContext(UIThemeContext);

  return (
    <Tabs.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarStyle: {
          backgroundColor: palette.card,
          position: 'absolute',
          marginHorizontal: 14,
          marginBottom: 10,
          borderRadius: 20,
          height: 64,
          paddingBottom: 8,
          paddingTop: 8,
          borderTopWidth: 0,
          elevation: 8,
        },
        tabBarActiveTintColor: palette.primary,
        tabBarInactiveTintColor: palette.muted,
        tabBarIcon: ({ color, size }) => {
          const map = { Home: 'home', User: 'account-circle' };
          return <MaterialCommunityIcons name={map[route.name]} size={size} color={color} />;
        },
      })}
    >
      <Tabs.Screen name="Home" component={HomeScreen} />
      <Tabs.Screen name="User" component={UserScreen} />
    </Tabs.Navigator>
  );
}

function NutrientModuleTabs() {
  const { palette } = useContext(UIThemeContext);
  return (
    <ModuleTabs.Navigator
      initialRouteName="Scan"
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarStyle: {
          backgroundColor: palette.card,
          position: 'absolute',
          marginHorizontal: 14,
          marginBottom: 10,
          borderRadius: 20,
          height: 64,
          paddingBottom: 8,
          paddingTop: 8,
          borderTopWidth: 0,
          elevation: 8,
        },
        tabBarActiveTintColor: palette.primary,
        tabBarInactiveTintColor: palette.muted,
        tabBarIcon: ({ color, size }) => {
          const map = { Home: 'home', Scan: 'camera', History: 'history', Stats: 'chart-bar', User: 'account-circle' };
          return <MaterialCommunityIcons name={map[route.name]} size={size} color={color} />;
        },
      })}
    >
      <ModuleTabs.Screen
        name="Home"
        component={HomeScreen}
        options={{ title: 'Home' }}
      />
      <ModuleTabs.Screen name="Scan" component={ScanScreen} />
      <ModuleTabs.Screen name="History" component={HistoryScreen} />
      <ModuleTabs.Screen name="Stats" component={StatsScreen} />
      <ModuleTabs.Screen name="User" component={UserScreen} />
    </ModuleTabs.Navigator>
  );
}

function FruitModuleTabs() {
  const { palette } = useContext(UIThemeContext);
  return (
    <ModuleTabs.Navigator
      initialRouteName="FruitScan"
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarStyle: {
          backgroundColor: palette.card,
          position: 'absolute',
          marginHorizontal: 14,
          marginBottom: 10,
          borderRadius: 20,
          height: 64,
          paddingBottom: 8,
          paddingTop: 8,
          borderTopWidth: 0,
          elevation: 8,
        },
        tabBarActiveTintColor: palette.primary,
        tabBarInactiveTintColor: palette.muted,
        tabBarIcon: ({ color, size }) => {
          const map = { Home: 'home', FruitScan: 'food-apple', History: 'history', Stats: 'chart-bar', User: 'account-circle' };
          return <MaterialCommunityIcons name={map[route.name]} size={size} color={color} />;
        },
      })}
    >
      <ModuleTabs.Screen
        name="Home"
        component={HomeScreen}
        options={{ title: 'Home' }}
      />
      <ModuleTabs.Screen
        name="FruitScan"
        component={FruitScanScreen}
        options={{ title: 'Scan' }}
      />
      <ModuleTabs.Screen name="History" component={HistoryScreen} initialParams={{ initialMode: 'fruit' }} />
      <ModuleTabs.Screen name="Stats" component={StatsScreen} initialParams={{ initialMode: 'fruit' }} />
      <ModuleTabs.Screen name="User" component={UserScreen} />
    </ModuleTabs.Navigator>
  );
}

function DiseaseModuleTabs() {
  const { palette } = useContext(UIThemeContext);
  return (
    <ModuleTabs.Navigator
      initialRouteName="DiseaseScan"
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarStyle: {
          backgroundColor: palette.card,
          position: 'absolute',
          marginHorizontal: 14,
          marginBottom: 10,
          borderRadius: 20,
          height: 64,
          paddingBottom: 8,
          paddingTop: 8,
          borderTopWidth: 0,
          elevation: 8,
        },
        tabBarActiveTintColor: palette.primary,
        tabBarInactiveTintColor: palette.muted,
        tabBarIcon: ({ color, size }) => {
          const map = { Home: 'home', DiseaseScan: 'virus', DiseaseHistory: 'history', User: 'account-circle' };
          return <MaterialCommunityIcons name={map[route.name]} size={size} color={color} />;
        },
      })}
    >
      <ModuleTabs.Screen
        name="Home"
        component={HomeScreen}
        options={{ title: 'Home' }}
      />
      <ModuleTabs.Screen
        name="DiseaseScan"
        component={DiseaseScanScreen}
        options={{ title: 'Scan' }}
      />
      <ModuleTabs.Screen
        name="DiseaseHistory"
        component={DiseaseHistoryScreen}
        options={{ title: 'History' }}
      />
      <ModuleTabs.Screen name="User" component={UserScreen} />
    </ModuleTabs.Navigator>
  );
}

export default function AppNavigator() {
  return (
    <Stack.Navigator>
      <Stack.Screen
        name="MainTabs"
        component={TabRoutes}
        options={{ headerShown: false }}
      />
      <Stack.Screen name="NutrientModule" component={NutrientModuleTabs} options={{ headerShown: false }} />
      <Stack.Screen name="FruitModule" component={FruitModuleTabs} options={{ headerShown: false }} />
      <Stack.Screen name="DiseaseModule" component={DiseaseModuleTabs} options={{ headerShown: false }} />
      <Stack.Screen
        name="DiseaseResult"
        component={DiseaseResultScreen}
        options={{ title: 'Disease Result' }}
      />
      <Stack.Screen
        name="DiseaseSettings"
        component={DiseaseSettingsScreen}
        options={{ headerShown: false }}
      />
      <Stack.Screen
        name="MonitoringModule"
        component={DiseaseMonitoringFlowScreen}
        options={{ headerShown: false }}
      />
      <Stack.Screen
        name="Result"
        component={ResultScreen}
        options={{ headerShown: false }}
      />
      <Stack.Screen
        name="Detail"
        component={DetailScreen}
        options={{ title: 'Nutrient Detail' }}
      />
      <Stack.Screen
        name="FruitScan"
        component={FruitScanScreen}
        options={{ title: 'Tomato Fruit Scan' }}
      />
      <Stack.Screen
        name="FruitResult"
        component={FruitResultScreen}
        options={{ headerShown: false }}
      />
      <Stack.Screen
        name="FruitDetail"
        component={FruitDetailScreen}
        options={{ title: 'Fruit Treatment Guide' }}
      />
    </Stack.Navigator>
  );
}
