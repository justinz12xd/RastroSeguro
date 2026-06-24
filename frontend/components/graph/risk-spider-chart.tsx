'use client'

import { ClaimSummary } from '@/lib/api'
import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
} from 'recharts'
import { ChartContainer, ChartLegend, ChartLegendContent, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart'
import { buildSpiderNarrative, computeSpiderData, getTopSpiderDrivers } from '@/lib/graph-insights'
import { ChartInsight } from '@/components/report/chart-insight'
import { UI_COPY } from '@/lib/human-labels'
import { AIChartExplainButton } from '@/components/ai-chart-explain-button'

const gridStroke = 'color-mix(in oklch, var(--chart-grid) 45%, transparent)'

export function RiskSpiderChart({ selectedClaim, claims }: { selectedClaim: ClaimSummary | null; claims: ClaimSummary[] }) {
  if (!selectedClaim) return null

  const data = computeSpiderData(selectedClaim, claims).map((d) => ({
    dimension: d.dimension,
    Caso: d.caseValue,
    Promedio: d.average,
    diff: d.diff,
  }))

  const topDrivers = getTopSpiderDrivers(selectedClaim, claims, 3)
  const narrative = buildSpiderNarrative(selectedClaim, claims)

  return (
    <div className="space-y-3">
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="institutional-card relative p-3 lg:col-span-2">
          <AIChartExplainButton
            prompt={`Explica el gráfico radar "Señales del caso vs promedio de la cartera" para el siniestro ${selectedClaim.id_siniestro}. Compara dimensiones, destaca desviaciones relevantes y sugiere qué debería validar el analista. Datos: ${data.map((row) => `${row.dimension}: caso ${row.Caso}, promedio ${row.Promedio}, diferencia ${row.diff}`).join('; ')}.`}
          />
          <p className="label-mono mb-2 text-muted-foreground">
            Señales del caso {UI_COPY.vsAverage} de la cartera
          </p>
          <ChartContainer
            config={{
              Caso: { label: 'Caso', color: 'var(--chart-1)' },
              Promedio: { label: 'Promedio', color: 'var(--chart-2)' },
            }}
            className="h-[280px] w-full"
          >
            <RadarChart data={data} outerRadius="72%">
              <PolarGrid stroke={gridStroke} />
              <PolarAngleAxis dataKey="dimension" tick={{ fontSize: 12, fill: 'var(--muted-foreground)' }} />
              <PolarRadiusAxis angle={30} domain={[0, 40]} tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }} stroke={gridStroke} />
              <ChartTooltip content={<ChartTooltipContent />} />
              <ChartLegend content={<ChartLegendContent />} />
              <Radar name="Promedio" dataKey="Promedio" fill="var(--color-Promedio)" fillOpacity={0.15} stroke="var(--color-Promedio)" strokeWidth={2} />
              <Radar name="Caso" dataKey="Caso" fill="var(--color-Caso)" fillOpacity={0.3} stroke="var(--color-Caso)" strokeWidth={2.5} />
            </RadarChart>
          </ChartContainer>
        </div>

        <div className="institutional-card p-3">
          <h4 className="label-mono-md mb-3 font-bold uppercase">{UI_COPY.mainSignals}</h4>
          {topDrivers.length ? (
            <div className="space-y-2">
              {topDrivers.map((d) => (
                <div key={d.dimension} className="border border-border bg-[var(--surface-low)] p-3">
                  <p className="font-semibold">{d.dimension}</p>
                  <p className="text-sm text-muted-foreground">+{d.diff} {UI_COPY.vsAverage}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">Este caso no supera el promedio en señales clave del puntaje.</p>
          )}
        </div>
      </div>
      <ChartInsight text={narrative} />
    </div>
  )
}
