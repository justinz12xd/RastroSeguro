'use client'

import { Bar, BarChart, CartesianGrid, Cell, XAxis, YAxis } from 'recharts'
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart'
import { ClaimSummary } from '@/lib/api'
import {
  buildGlobalRecurrenceRanking,
  formatGlobalRecurrenceLabel,
  GlobalRecurrenceRow,
} from '@/lib/global-recurrence'
import { UI_COPY } from '@/lib/human-labels'
import { AIChartExplainButton } from '@/components/ai-chart-explain-button'

const gridStroke = 'color-mix(in oklch, var(--chart-grid) 45%, transparent)'
const axisStyle = { fill: 'var(--muted-foreground)', fontSize: 11 }

function shortLabel(text: string, max = 28): string {
  if (text.length <= max) return text
  return `${text.slice(0, max - 1)}…`
}

export function RecurrenceTopChart({
  claims,
  currentClaimId,
  limit = 8,
}: {
  claims: ClaimSummary[]
  currentClaimId?: string | null
  limit?: number
}) {
  const rows: GlobalRecurrenceRow[] = buildGlobalRecurrenceRanking(claims, currentClaimId, Math.max(limit, 50)).slice(0, limit)

  const chartRows = rows.map((row) => ({
    ...row,
    name: shortLabel(formatGlobalRecurrenceLabel(row, true)),
    fullName: formatGlobalRecurrenceLabel(row),
    labelCount: `${row.total} ${row.total === 1 ? 'vez' : 'veces'}`,
  }))

  if (!chartRows.length) {
    return (
      <p className="text-sm text-muted-foreground">
        No hay elementos que se repitan en la cartera para mostrar.
      </p>
    )
  }

  return (
    <div className="relative space-y-2">
      <AIChartExplainButton
        prompt={`Explica el gráfico "Top recurrencias" de la cartera${currentClaimId ? ` para el contexto del caso ${currentClaimId}` : ''}. Interpreta qué entidades o atributos repetidos merecen revisión, qué significa que una barra esté resaltada y qué próximos pasos sugieres. Datos: ${chartRows.map((row) => `${row.fullName}: ${row.total} apariciones${row.inCurrentCase ? ', presente en el caso activo' : ''}`).join('; ')}.`}
      />
      <p className="text-sm text-muted-foreground">
        Ranking global de la cartera: posición, tipo de elemento y cuántas veces aparece en otros siniestros.
      </p>
      <ChartContainer
        config={{ total: { label: UI_COPY.recurrenceCount, color: 'var(--chart-1)' } }}
        className="h-[300px] w-full"
      >
        <BarChart data={chartRows} layout="vertical" margin={{ left: 8, right: 12 }}>
          <CartesianGrid horizontal={false} stroke={gridStroke} />
          <XAxis type="number" allowDecimals={false} tickLine={false} axisLine={false} tick={axisStyle} />
          <YAxis
            type="category"
            dataKey="name"
            width={148}
            tickLine={false}
            axisLine={false}
            tick={axisStyle}
          />
          <ChartTooltip
            content={
              <ChartTooltipContent
                formatter={(value, _name, item) => {
                  const row = item.payload as GlobalRecurrenceRow & { labelCount?: string }
                  return (
                    <span className="font-semibold">
                      {row.labelCount} en la cartera
                      {row.inCurrentCase ? ' · presente en este caso' : ''}
                    </span>
                  )
                }}
                labelFormatter={(_, payload) => {
                  const item = payload?.[0]?.payload as { fullName?: string } | undefined
                  return item?.fullName || ''
                }}
              />
            }
          />
          <Bar dataKey="total" radius={4}>
            {chartRows.map((row) => (
              <Cell
                key={row.key}
                fill={row.inCurrentCase ? 'var(--chart-4)' : 'var(--chart-1)'}
              />
            ))}
          </Bar>
        </BarChart>
      </ChartContainer>
      <p className="text-xs text-muted-foreground">
        Barras resaltadas: elementos del caso activo dentro del ranking global.
      </p>
    </div>
  )
}
