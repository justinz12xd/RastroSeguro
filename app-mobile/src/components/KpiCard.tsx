import { StyleSheet, Text, View, type ViewStyle } from 'react-native'
import { colors, radius, spacing } from '../theme/tokens'
import { textStyles } from '../theme/typography'

type Props = {
  label: string
  value: string
  hint?: string
  accent?: 'default' | 'rojo' | 'verde' | 'amarillo'
  style?: ViewStyle
}

export function KpiCard({ label, value, hint, accent = 'default', style }: Props) {
  const accentColor =
    accent === 'rojo'
      ? colors.riskRojo
      : accent === 'verde'
        ? colors.riskVerde
        : accent === 'amarillo'
          ? colors.riskAmarillo
          : colors.primary

  return (
    <View style={[styles.card, style]}>
      <View style={[styles.accent, { backgroundColor: accentColor }]} />
      <Text style={textStyles.labelMono}>{label}</Text>
      <Text style={[textStyles.kpiValue, styles.value]} numberOfLines={1}>
        {value}
      </Text>
      {hint ? <Text style={styles.hint}>{hint}</Text> : null}
    </View>
  )
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
    minWidth: '46%',
    backgroundColor: colors.surfaceLowest,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.lg,
    padding: spacing.md,
    overflow: 'hidden',
  },
  accent: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 3,
  },
  value: {
    marginTop: spacing.xs,
  },
  hint: {
    ...textStyles.label,
    marginTop: spacing.xs,
  },
})
