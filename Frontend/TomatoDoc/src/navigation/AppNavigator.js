import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
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
import PricePredictionScreen from '../modules/pricePrediction/screens/PricePredictionScreen';
import { tabOptions, stackHeaderOptions, hiddenTab } from '../theme/navigation';

const Stack = createNativeStackNavigator();
const Tabs = createBottomTabNavigator();
const ModuleTabs = createBottomTabNavigator();

// Every module has its own tab bar. Screens reached from a tab (results, detail pages, settings)
// are registered inside the same tab navigator but hidden from the bar (`hiddenTab`), so the bar
// stays visible on them. `backBehavior="history"` makes the back button return to the screen the
// user came from (for example Result -> Scan, or Result -> History).

function TabRoutes() {
  const insets = useSafeAreaInsets();
  return (
    <Tabs.Navigator
      screenOptions={tabOptions({ Home: 'home', User: 'account-circle' }, insets)}
    >
      <Tabs.Screen name="Home" component={HomeScreen} />
      <Tabs.Screen name="User" component={UserScreen} />
    </Tabs.Navigator>
  );
}

function NutrientModuleTabs() {
  const insets = useSafeAreaInsets();
  return (
    <ModuleTabs.Navigator
      initialRouteName="Scan"
      backBehavior="history"
      screenOptions={tabOptions({ Home: 'home', Scan: 'camera', History: 'history', Stats: 'chart-bar', User: 'account-circle' }, insets)}
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

      {/* Reached from Scan and History; hidden from the bar. */}
      <ModuleTabs.Screen name="Result" component={ResultScreen} options={hiddenTab} />
      <ModuleTabs.Screen name="Detail" component={DetailScreen} options={hiddenTab} />
      <ModuleTabs.Screen name="FruitResult" component={FruitResultScreen} options={hiddenTab} />
      <ModuleTabs.Screen name="FruitDetail" component={FruitDetailScreen} options={hiddenTab} />
    </ModuleTabs.Navigator>
  );
}

function FruitModuleTabs() {
  const insets = useSafeAreaInsets();
  return (
    <ModuleTabs.Navigator
      initialRouteName="FruitScan"
      backBehavior="history"
      screenOptions={tabOptions({ Home: 'home', FruitScan: 'food-apple', History: 'history', Stats: 'chart-bar', User: 'account-circle' }, insets)}
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

      {/* Reached from Scan and History; hidden from the bar. */}
      <ModuleTabs.Screen name="FruitResult" component={FruitResultScreen} options={hiddenTab} />
      <ModuleTabs.Screen name="FruitDetail" component={FruitDetailScreen} options={hiddenTab} />
      <ModuleTabs.Screen name="Result" component={ResultScreen} options={hiddenTab} />
      <ModuleTabs.Screen name="Detail" component={DetailScreen} options={hiddenTab} />
    </ModuleTabs.Navigator>
  );
}

function DiseaseModuleTabs() {
  const insets = useSafeAreaInsets();
  return (
    <ModuleTabs.Navigator
      initialRouteName="DiseaseScan"
      backBehavior="history"
      screenOptions={tabOptions({ Home: 'home', DiseaseScan: 'virus', DiseaseHistory: 'history', User: 'account-circle' }, insets)}
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

      {/* Reached from Scan; hidden from the bar. */}
      <ModuleTabs.Screen name="DiseaseResult" component={DiseaseResultScreen} options={hiddenTab} />
      <ModuleTabs.Screen name="DiseaseSettings" component={DiseaseSettingsScreen} options={hiddenTab} />
    </ModuleTabs.Navigator>
  );
}

function MonitoringModuleTabs() {
  const insets = useSafeAreaInsets();
  return (
    <ModuleTabs.Navigator
      initialRouteName="Monitor"
      backBehavior="history"
      screenOptions={tabOptions({ Home: 'home', Monitor: 'chart-timeline-variant', User: 'account-circle' }, insets)}
    >
      <ModuleTabs.Screen
        name="Home"
        component={HomeScreen}
        options={{ title: 'Home' }}
      />
      <ModuleTabs.Screen
        name="Monitor"
        component={DiseaseMonitoringFlowScreen}
        options={{ title: 'Monitor' }}
      />
      <ModuleTabs.Screen name="User" component={UserScreen} />
    </ModuleTabs.Navigator>
  );
}

function PriceModuleTabs() {
  const insets = useSafeAreaInsets();
  return (
    <ModuleTabs.Navigator
      initialRouteName="Price"
      backBehavior="history"
      screenOptions={tabOptions({ Home: 'home', Price: 'chart-line', User: 'account-circle' }, insets)}
    >
      <ModuleTabs.Screen
        name="Home"
        component={HomeScreen}
        options={{ title: 'Home' }}
      />
      <ModuleTabs.Screen
        name="Price"
        component={PricePredictionScreen}
        options={{ title: 'Price' }}
      />
      <ModuleTabs.Screen name="User" component={UserScreen} />
    </ModuleTabs.Navigator>
  );
}

export default function AppNavigator() {
  return (
    <Stack.Navigator screenOptions={stackHeaderOptions}>
      <Stack.Screen
        name="MainTabs"
        component={TabRoutes}
        options={{ headerShown: false }}
      />
      <Stack.Screen name="NutrientModule" component={NutrientModuleTabs} options={{ headerShown: false }} />
      <Stack.Screen name="FruitModule" component={FruitModuleTabs} options={{ headerShown: false }} />
      <Stack.Screen name="DiseaseModule" component={DiseaseModuleTabs} options={{ headerShown: false }} />
      <Stack.Screen name="MonitoringModule" component={MonitoringModuleTabs} options={{ headerShown: false }} />
      <Stack.Screen name="PricePrediction" component={PriceModuleTabs} options={{ headerShown: false }} />
    </Stack.Navigator>
  );
}
