import { StyleSheet, Text, View } from 'react-native'
import { colors, radius, spacing } from '../theme/tokens'
import { fonts } from '../theme/typography'
import { normalizeRisk, riskLabel } from '../lib/format'

type Props = {
  level?: string | null
}

export function RiskBadge({ level }: Props) {
  const risk = normalizeRisk(level)
  const palette =
    risk === 'critico' || risk === 'alto'
      ? { bg: colors.errorContainer, fg: colors.onErrorContainer }
      : risk === 'bajo'
        ? { bg: colors.successContainer, fg: colors.onSuccessContainer }
        : { bg: colors.warningContainer, fg: colors.onWarningContainer }

  return (
    <View style={[styles.badge, { backgroundColor: palette.bg }]}>
      <Text style={[styles.text, { color: palette.fg }]}>{riskLabel(level)}</Text>
    </View>
  )
}

const styles = StyleSheet.create({
  badge: {
    borderRadius: radius.sm,
    paddingHorizontal: spacing.sm,
    paddingVertical: 3,
    alignSelf: 'flex-start',
  },
  text: {
    fontFamily: fonts.sansSemiBold,
    fontSize: 11,
    letterSpacing: 0.2,
  },
})
