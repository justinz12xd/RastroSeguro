/**
 * Design tokens ported from frontend/app/globals.css (OKLCH → hex).
 * Brand hue ~264 (indigo), blue-tinted slate neutrals.
 */
export const colors = {
  background: '#f8fafd',
  foreground: '#0f182b',
  card: '#ffffff',
  cardForeground: '#0f182b',
  primary: '#3a67d0',
  primaryForeground: '#f9fafd',
  secondary: '#364055',
  secondaryForeground: '#f9fafd',
  muted: '#e3e8f1',
  mutedForeground: '#4a5469',
  accent: '#dae8ff',
  accentForeground: '#193578',
  destructive: '#be0019',
  destructiveForeground: '#ffffff',
  border: '#cdd4e2',
  input: '#f2f4f9',
  ring: '#3a67d0',

  brand: '#3a67d0',
  brandStrong: '#2350be',
  brandSoft: '#dae8ff',

  surface: '#f8fafd',
  surfaceLowest: '#ffffff',
  surfaceLow: '#f2f4f9',
  surfaceContainer: '#e3e8f1',
  surfaceHigh: '#cdd4e2',
  primaryContainer: '#13203e',
  onPrimaryContainer: '#dce5f5',

  riskVerde: '#007142',
  riskVerdeForeground: '#ffffff',
  riskAmarillo: '#efad32',
  riskAmarilloForeground: '#3d2a0a',
  riskRojo: '#be0019',
  riskRojoForeground: '#ffffff',

  successContainer: '#d6f4e1',
  onSuccessContainer: '#004c28',
  warningContainer: '#ffecc9',
  onWarningContainer: '#6f4100',
  errorContainer: '#ffe2de',
  onErrorContainer: '#8a0314',

  chart1: '#3a67d0',
  chart2: '#008853',
  chart3: '#d19000',
  chart4: '#c53637',
} as const

export const radius = {
  sm: 4,
  md: 6,
  lg: 8,
  xl: 12,
} as const

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 24,
  xxxl: 32,
} as const
