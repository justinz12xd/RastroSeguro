import { Text } from 'react-native'
import { NavigationContainer, DefaultTheme } from '@react-navigation/native'
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs'
import { createNativeStackNavigator } from '@react-navigation/native-stack'
import { DashboardScreen } from '../screens/DashboardScreen'
import { ImpactScreen } from '../screens/ImpactScreen'
import { ClaimDetailScreen } from '../screens/ClaimDetailScreen'
import { colors } from '../theme/tokens'
import { fonts } from '../theme/typography'
import type { RootStackParamList, RootTabParamList } from './types'

const Tab = createBottomTabNavigator<RootTabParamList>()
const Stack = createNativeStackNavigator<RootStackParamList>()

const navTheme = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    background: colors.background,
    card: colors.surfaceLowest,
    text: colors.foreground,
    border: colors.border,
    primary: colors.primary,
  },
}

function TabIcon({ label, focused }: { label: string; focused: boolean }) {
  return (
    <Text
      style={{
        fontFamily: fonts.sansBold,
        fontSize: 11,
        color: focused ? colors.primary : colors.mutedForeground,
      }}
    >
      {label}
    </Text>
  )
}

function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarStyle: {
          backgroundColor: colors.surfaceLowest,
          borderTopColor: colors.border,
          height: 64,
          paddingBottom: 8,
          paddingTop: 8,
        },
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.mutedForeground,
        tabBarLabelStyle: {
          fontFamily: fonts.sansMedium,
          fontSize: 12,
        },
      }}
    >
      <Tab.Screen
        name="Dashboard"
        component={DashboardScreen}
        options={{
          title: 'Control',
          tabBarIcon: ({ focused }) => <TabIcon label="◉" focused={focused} />,
        }}
      />
      <Tab.Screen
        name="Impact"
        component={ImpactScreen}
        options={{
          title: 'Impacto',
          tabBarIcon: ({ focused }) => <TabIcon label="★" focused={focused} />,
        }}
      />
    </Tab.Navigator>
  )
}

export function RootNavigator() {
  return (
    <NavigationContainer theme={navTheme}>
      <Stack.Navigator
        screenOptions={{
          headerStyle: { backgroundColor: colors.primaryContainer },
          headerTintColor: colors.brandSoft,
          headerTitleStyle: {
            fontFamily: fonts.sansSemiBold,
            fontSize: 16,
          },
          contentStyle: { backgroundColor: colors.background },
        }}
      >
        <Stack.Screen
          name="Tabs"
          component={MainTabs}
          options={{ headerShown: false }}
        />
        <Stack.Screen
          name="ClaimDetail"
          component={ClaimDetailScreen}
          options={{ title: 'Expediente', headerBackTitle: 'Atrás' }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  )
}
