import { StyleSheet, Text, useWindowDimensions, View } from 'react-native'
import { PieChart } from 'react-native-gifted-charts'
import { colors, spacing } from '../theme/tokens'
import { textStyles } from '../theme/typography'
import { formatNumber, formatPercent } from '../lib/format'

type Props = {
  verdes: number
  amarillos: number
  rojos: number
}

export function SemaphorePieChart({ verdes, amarillos, rojos }: Props) {
  const { width } = useWindowDimensions()
  const total = Math.max(verdes + amarillos + rojos, 1)
  const chartSize = Math.min(Math.max(width - 96, 180), 240)

  const segments = [
    { key: 'critico', label: 'Crítico', value: rojos, color: colors.riskRojo },
    { key: 'medio', label: 'Medio', value: amarillos, color: colors.riskAmarillo },
    { key: 'bajo', label: 'Bajo', value: verdes, color: colors.riskVerde },
  ].filter((s) => s.value > 0)

  const data =
    segments.length > 0
      ? segments.map((s) => ({
          value: s.value,
          color: s.color,
          text: String(s.value),
        }))
      : [{ value: 1, color: colors.muted, text: '0' }]

  return (
    <View style={styles.wrap}>
      <View style={styles.chartWrap}>
        <PieChart
          data={data}
          donut
          radius={chartSize / 2.4}
          innerRadius={chartSize / 3.6}
          innerCircleColor={colors.surfaceLowest}
          strokeWidth={3}
          strokeColor={colors.surfaceLowest}
          centerLabelComponent={() => (
            <View style={styles.centerLabel}>
              <Text style={textStyles.labelMono}>Total</Text>
              <Text style={textStyles.kpiValue}>{formatNumber(total)}</Text>
            </View>
          )}
        />
      </View>

      <View style={styles.legend}>
        {[
          { label: 'Crítico', value: rojos, color: colors.riskRojo },
          { label: 'Medio', value: amarillos, color: colors.riskAmarillo },
          { label: 'Bajo', value: verdes, color: colors.riskVerde },
        ].map((row) => (
          <View key={row.label} style={styles.legendItem}>
            <View style={[styles.swatch, { backgroundColor: row.color }]} />
            <Text style={[textStyles.labelMono, { color: row.color }]}>{row.label}</Text>
            <Text style={textStyles.bodyMedium}>{formatNumber(row.value)}</Text>
            <Text style={textStyles.label}>{formatPercent((row.value / total) * 100)}</Text>
          </View>
        ))}
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: {
    gap: spacing.lg,
    alignItems: 'center',
  },
  chartWrap: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  centerLabel: {
    alignItems: 'center',
  },
  legend: {
    width: '100%',
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  legendItem: {
    flexGrow: 1,
    minWidth: '28%',
    backgroundColor: colors.surfaceLow,
    padding: spacing.sm,
    alignItems: 'center',
    gap: 2,
  },
  swatch: {
    width: 10,
    height: 10,
    borderRadius: 2,
    marginBottom: 2,
  },
})
