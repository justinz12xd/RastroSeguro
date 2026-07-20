import { StyleSheet, Text, useWindowDimensions, View } from 'react-native'
import { BarChart } from 'react-native-gifted-charts'
import { colors, spacing } from '../theme/tokens'
import { fonts, textStyles } from '../theme/typography'
import type { RiskAggregateRow } from '../lib/api'

type Props = {
  rows: RiskAggregateRow[]
  nameKey?: 'name' | 'ramo' | 'ciudad' | 'id_proveedor'
  barColor?: string
  layout?: 'vertical' | 'horizontal'
  limit?: number
}

function shortLabel(raw: string, max = 10) {
  const text = raw.trim() || 'N/D'
  return text.length > max ? `${text.slice(0, max - 1)}…` : text
}

export function RiskBarChart({
  rows,
  nameKey = 'name',
  barColor = colors.chart1,
  layout = 'vertical',
  limit = 6,
}: Props) {
  const { width } = useWindowDimensions()
  const chartWidth = Math.max(width - 72, 280)
  const items = rows.slice(0, limit)

  if (!items.length) {
    return <Text style={textStyles.subtitle}>Sin datos disponibles.</Text>
  }

  const data = items.map((row) => {
    const name = String(row.name || row[nameKey] || 'No informado')
    const score = Math.round(Number(row.score_promedio || 0))
    return {
      value: score,
      label: shortLabel(name, layout === 'horizontal' ? 12 : 8),
      frontColor: barColor,
      topLabelComponent: () => (
        <Text style={styles.topLabel}>{score}</Text>
      ),
    }
  })

  if (layout === 'horizontal') {
    const maxValue = Math.max(...data.map((d) => d.value), 100)
    return (
      <View style={styles.wrap}>
        <BarChart
          data={data}
          horizontal
          barWidth={18}
          spacing={18}
          height={Math.max(items.length * 42, 160)}
          width={chartWidth - 40}
          maxValue={maxValue}
          noOfSections={4}
          xAxisThickness={0}
          yAxisThickness={0}
          yAxisTextStyle={styles.axis}
          xAxisLabelTextStyle={styles.axis}
          rulesColor={colors.border}
          rulesType="solid"
          showValuesAsTopLabel={false}
          isAnimated
          animationDuration={600}
        />
        <View style={styles.metaList}>
          {items.map((row, index) => {
            const name = String(row.name || row[nameKey] || 'No informado')
            return (
              <Text key={`${name}-${index}`} style={styles.metaLine} numberOfLines={1}>
                {name} · {row.total_siniestros} casos
                {row.casos_rojos != null ? ` · ${row.casos_rojos} rojos` : ''}
              </Text>
            )
          })}
        </View>
      </View>
    )
  }

  return (
    <View style={styles.wrap}>
      <BarChart
        data={data}
        barWidth={28}
        spacing={20}
        roundedTop
        roundedBottom
        height={200}
        width={chartWidth}
        maxValue={100}
        noOfSections={4}
        yAxisThickness={0}
        xAxisThickness={1}
        xAxisColor={colors.border}
        yAxisTextStyle={styles.axis}
        xAxisLabelTextStyle={styles.axis}
        rulesColor={colors.border}
        rulesType="solid"
        isAnimated
        animationDuration={600}
      />
      <View style={styles.metaList}>
        {items.map((row, index) => {
          const name = String(row.name || row[nameKey] || 'No informado')
          return (
            <Text key={`${name}-${index}`} style={styles.metaLine} numberOfLines={1}>
              {name} · {row.total_siniestros} casos
              {row.casos_rojos != null ? ` · ${row.casos_rojos} rojos` : ''}
            </Text>
          )
        })}
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: {
    gap: spacing.md,
    overflow: 'hidden',
  },
  axis: {
    color: colors.mutedForeground,
    fontSize: 10,
    fontFamily: fonts.sans,
  },
  topLabel: {
    color: colors.foreground,
    fontSize: 10,
    fontFamily: fonts.sansSemiBold,
    marginBottom: 2,
  },
  metaList: {
    gap: spacing.xs,
  },
  metaLine: {
    ...textStyles.label,
  },
})
