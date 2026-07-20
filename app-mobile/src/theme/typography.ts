import { TextStyle } from 'react-native'
import { colors } from './tokens'

export const fonts = {
  sans: 'IBMPlexSans_400Regular',
  sansMedium: 'IBMPlexSans_500Medium',
  sansSemiBold: 'IBMPlexSans_600SemiBold',
  sansBold: 'IBMPlexSans_700Bold',
  mono: 'JetBrainsMono_400Regular',
  monoMedium: 'JetBrainsMono_500Medium',
  monoBold: 'JetBrainsMono_700Bold',
} as const

export const textStyles = {
  display: {
    fontFamily: fonts.sansBold,
    fontSize: 28,
    lineHeight: 34,
    letterSpacing: -0.4,
    color: colors.foreground,
  } satisfies TextStyle,
  title: {
    fontFamily: fonts.sansSemiBold,
    fontSize: 20,
    lineHeight: 26,
    letterSpacing: -0.2,
    color: colors.foreground,
  } satisfies TextStyle,
  subtitle: {
    fontFamily: fonts.sansMedium,
    fontSize: 15,
    lineHeight: 22,
    color: colors.mutedForeground,
  } satisfies TextStyle,
  body: {
    fontFamily: fonts.sans,
    fontSize: 14,
    lineHeight: 20,
    color: colors.foreground,
  } satisfies TextStyle,
  bodyMedium: {
    fontFamily: fonts.sansMedium,
    fontSize: 14,
    lineHeight: 20,
    color: colors.foreground,
  } satisfies TextStyle,
  label: {
    fontFamily: fonts.sansMedium,
    fontSize: 12,
    lineHeight: 16,
    letterSpacing: 0.2,
    color: colors.mutedForeground,
  } satisfies TextStyle,
  labelMono: {
    fontFamily: fonts.monoMedium,
    fontSize: 11,
    lineHeight: 14,
    letterSpacing: 0.6,
    textTransform: 'uppercase',
    color: colors.mutedForeground,
  } satisfies TextStyle,
  mono: {
    fontFamily: fonts.mono,
    fontSize: 13,
    lineHeight: 18,
    color: colors.foreground,
  } satisfies TextStyle,
  kpiValue: {
    fontFamily: fonts.sansBold,
    fontSize: 22,
    lineHeight: 28,
    letterSpacing: -0.3,
    color: colors.foreground,
  } satisfies TextStyle,
} as const
