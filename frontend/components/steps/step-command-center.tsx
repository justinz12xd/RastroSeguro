'use client'

import { useEffect, useMemo, useState, type HTMLAttributes, type HTMLInputTypeAttribute } from 'react'
import { AlertTriangle, ArrowRight, BarChart3, Bot, Building2, CircleDollarSign, FileText, FlaskConical, MapPin, FileSearch, GitBranch, Inbox, Loader2, ShieldCheck, Target, UploadCloud, UsersRound } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, XAxis, YAxis } from 'recharts'
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart'
import { useAppState } from '@/lib/app-context'
import { ClaimSummary, ExecutiveReport, RiskAggregateRow, SimulationResponse, alertToText, getBranchRiskDistribution, getCityRiskDistribution, getExecutiveReport, getProviderRiskRanking, simulateClaim } from '@/lib/api'
import { formatCurrency, getRiskColor, getRiskLabel } from '@/lib/claims-data'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { RiskBadge } from '@/components/ui/risk-badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { AIChartExplainButton } from '@/components/ai-chart-explain-button'

const num = (value: unknown) => Number(value ?? 0)
function normalizeRisk(level?: string | null) {
  const value = String(level || '').toLowerCase()
  if (['critico', 'crítico', 'rojo'].includes(value)) return 'critico'
  if (['alto', 'high'].includes(value)) return 'alto'
  if (['medio', 'amarillo', 'medium'].includes(value)) return 'medio'
  if (['bajo', 'verde', 'low'].includes(value)) return 'bajo'
  return 'medio'
}

function normalizeClaimCode(raw: string) {
  const text = String(raw || '').trim().toUpperCase().replace(/_/g, '-')
  const match = text.match(/^SIN-?(\d+)$/)
  if (match) return `SIN-${String(Number(match[1]))}`
  return text
}

function countAlerts(claim: ClaimSummary) {
  const alerts = claim.alertas_activadas
  if (Array.isArray(alerts)) return alerts.length
  if (typeof alerts === 'string') return alerts ? 1 : 0
  return 0
}

function normalizeBackendRows(rows: RiskAggregateRow[] | null, key: 'id_proveedor' | 'ramo' | 'ciudad') {
  return (rows || []).map((row) => ({
    name: String(row.name || row[key] || 'No informado'),
    total: Number(row.total_siniestros || 0),
    risk: Number(row.score_promedio || 0) * Number(row.total_siniestros || 0),
    avgRisk: Math.round(Number(row.score_promedio || 0)),
    casosRojos: Number(row.casos_rojos || 0),
  }))
}

function ReportDialog({ report, loading, onLoad }: { report: ExecutiveReport | null; loading: boolean; onLoad: () => void }) {
  const summary = report?.summary
  return (
    <Dialog onOpenChange={(open) => { if (open && !report && !loading) onLoad() }}>
      <DialogTrigger asChild>
        <Button variant="outline-inverse" className="h-auto px-4 py-2 text-[13px] font-semibold">
          <FileText className="h-4 w-4" /> Reporte ejecutivo
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[86vh] overflow-y-auto sm:max-w-4xl">
        <DialogHeader>
          <DialogTitle>Reporte ejecutivo RastroSeguro</DialogTitle>
          <DialogDescription>Resumen ejecutivo generado por RastroSeguro para auditoria y seguimiento.</DialogDescription>
        </DialogHeader>
        {loading ? (
          <div className="flex items-center gap-2 p-8 text-muted-foreground" aria-live="polite"><Loader2 className="h-4 w-4 animate-spin" /> Generando reporte...</div>
        ) : report && summary ? (
          <div className="space-y-5">
            <div className="grid gap-3 md:grid-cols-4">
              {[
                ['Total', summary.total_siniestros],
                ['Rojos', summary.casos_rojos],
                ['% rojo', `${summary.porcentaje_rojo}%`],
                ['Monto rojo', formatCurrency(summary.monto_reclamado_casos_rojos)],
              ].map(([label, value]) => (
                <div key={label} className="border border-border bg-[var(--surface-low)] p-2.5">
                  <p className="label-mono text-muted-foreground">{label}</p>
                  <p className="font-display text-xl font-semibold">{value}</p>
                </div>
              ))}
            </div>
            <p className="rounded-md border border-border bg-[var(--surface-low)] p-3 text-sm italic text-muted-foreground">{report.ethics_note}</p>
            {report.ahorro_potencial_estimado ? (
              <div className="action-panel-verde p-4">
                <p className="label-mono text-[var(--risk-verde)]">Ahorro potencial estimado</p>
                <p className="font-display text-2xl font-semibold">
                  {formatCurrency(report.ahorro_potencial_estimado.ahorro_potencial_estimado)}
                </p>
                <p className="mt-2 text-xs text-muted-foreground">
                  {report.ahorro_potencial_estimado.nota_etica}
                </p>
              </div>
            ) : null}
            <div className="grid gap-4 lg:grid-cols-2">
              <ReportTable title="Casos prioritarios" rows={report.top_casos || []} primary="id_siniestro" secondary="score_final" />
              <ReportTable title="Proveedores con mayor alerta" rows={report.top_proveedores || []} primary="id_proveedor" secondary="score_promedio" />
              <ReportTable title="Riesgo por ramo" rows={report.riesgo_por_ramo || []} primary="ramo" secondary="score_promedio" />
              <ReportTable title="Ciudades con mayor alerta" rows={report.top_ciudades || []} primary="ciudad" secondary="score_promedio" />
            </div>
          </div>
        ) : (
          <div className="p-6 text-sm text-muted-foreground">No se pudo cargar el reporte. Verifica que el sistema esté disponible.</div>
        )}
      </DialogContent>
    </Dialog>
  )
}

function ReportTable({ title, rows, primary, secondary }: { title: string; rows: unknown[]; primary: string; secondary: string }) {
  return (
    <div className="border border-border">
      <div className="section-header">{title}</div>
      <div className="divide-y divide-border">
        {rows.slice(0, 5).map((raw, index) => {
          const row = (raw || {}) as Record<string, unknown>
          return (
            <div key={`${title}-${index}`} className="flex items-center justify-between gap-3 p-3 text-sm">
              <span className="font-mono font-semibold">{String(row[primary] || 'N/D')}</span>
              <span className="label-mono-md text-muted-foreground">{String(row[secondary] ?? row.total_siniestros ?? '')}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function SimulatorDialog() {
  const [form, setForm] = useState({
    ramo: 'vehiculo',
    cobertura: 'choque',
    ciudad: 'Ambato',
    monto_reclamado: '18000',
    suma_asegurada: '20000',
    proveedor: 'PROV-012',
    dias_desde_inicio_poliza: '3',
    dias_entre_ocurrencia_reporte: '0',
    documentos_presentes: 'false',
    tercero_identificado: 'false',
    ocurrio_noche: 'true',
    hay_testigos: 'false',
    reporte_policial: 'false',
    narrativa: 'Vehículo impactado por tercero no identificado durante la noche. No existen testigos directos.',
  })
  const [result, setResult] = useState<SimulationResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const update = (key: keyof typeof form, value: string) => setForm((prev) => ({ ...prev, [key]: value }))
  const run = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await simulateClaim({
        ...form,
        monto_reclamado: Number(form.monto_reclamado),
        suma_asegurada: Number(form.suma_asegurada),
        dias_desde_inicio_poliza: Number(form.dias_desde_inicio_poliza),
        dias_entre_ocurrencia_reporte: Number(form.dias_entre_ocurrencia_reporte),
        documentos_presentes: form.documentos_presentes === 'true',
        tercero_identificado: form.tercero_identificado === 'true',
        ocurrio_noche: form.ocurrio_noche === 'true',
        hay_testigos: form.hay_testigos === 'true',
        reporte_policial: form.reporte_policial === 'true',
      })
      setResult(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo simular el siniestro.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline-inverse" className="h-auto px-4 py-2 text-[13px] font-semibold">
          <FlaskConical className="h-4 w-4" /> Simular caso
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[88vh] overflow-y-auto sm:max-w-5xl">
        <DialogHeader>
          <DialogTitle>Simulador de nuevo siniestro</DialogTitle>
          <DialogDescription>Evalua un caso de prueba con el motor de riesgo: reglas, narrativa y red de relaciones. No guarda datos reales.</DialogDescription>
        </DialogHeader>
        <div className="grid gap-5 lg:grid-cols-[1fr_.9fr]">
          <div className="space-y-3">
            <div className="grid gap-3 sm:grid-cols-2">
              <SelectField
                label="Ramo"
                value={form.ramo}
                onChange={(v) => update('ramo', v)}
                options={[
                  ['vehiculo', 'Vehículo'],
                  ['salud', 'Salud'],
                  ['hogar', 'Hogar'],
                  ['vida', 'Vida'],
                ]}
              />
              <SelectField
                label="Cobertura / evento"
                value={form.cobertura}
                onChange={(v) => update('cobertura', v)}
                options={[
                  ['choque', 'Choque'],
                  ['robo', 'Robo'],
                  ['incendio', 'Incendio'],
                  ['atencion_medica', 'Atención médica'],
                  ['fallecimiento', 'Fallecimiento'],
                ]}
              />
              <Field name="ciudad" label="Ciudad" value={form.ciudad} onChange={(v) => update('ciudad', v)} />
              <Field name="monto_reclamado" label="Monto reclamado" value={form.monto_reclamado} type="number" inputMode="decimal" onChange={(v) => update('monto_reclamado', v)} />
              <Field name="suma_asegurada" label="Suma asegurada" value={form.suma_asegurada} type="number" inputMode="decimal" onChange={(v) => update('suma_asegurada', v)} />
              <Field name="proveedor" label="Proveedor" value={form.proveedor} onChange={(v) => update('proveedor', v)} />
              <Field name="dias_desde_inicio_poliza" label="Días desde inicio póliza" value={form.dias_desde_inicio_poliza} type="number" inputMode="numeric" onChange={(v) => update('dias_desde_inicio_poliza', v)} />
              <Field name="dias_entre_ocurrencia_reporte" label="Días hasta reporte" value={form.dias_entre_ocurrencia_reporte} type="number" inputMode="numeric" onChange={(v) => update('dias_entre_ocurrencia_reporte', v)} />
            </div>
            <label className="block">
              <span className="label-mono-md font-bold uppercase text-muted-foreground">Narrativa</span>
              <Textarea name="narrativa" value={form.narrativa} onChange={(e) => update('narrativa', e.target.value)} className="mt-1 min-h-[110px]" />
            </label>
            <div className="grid gap-2 sm:grid-cols-2">
              <BooleanField label="Documentación completa" checked={form.documentos_presentes === 'true'} onChange={(checked) => update('documentos_presentes', String(checked))} />
              <BooleanField label="Tercero identificado" checked={form.tercero_identificado === 'true'} onChange={(checked) => update('tercero_identificado', String(checked))} />
              <BooleanField label="Ocurrió de noche" checked={form.ocurrio_noche === 'true'} onChange={(checked) => update('ocurrio_noche', String(checked))} />
              <BooleanField label="Hay testigos" checked={form.hay_testigos === 'true'} onChange={(checked) => update('hay_testigos', String(checked))} />
              <BooleanField label="Reporte policial" checked={form.reporte_policial === 'true'} onChange={(checked) => update('reporte_policial', String(checked))} />
            </div>
            {Number(form.suma_asegurada) > 0 && Number(form.monto_reclamado) > 0 && Number(form.suma_asegurada) > Number(form.monto_reclamado) * 100 ? (
              <p className="rounded-md border border-amber-300 bg-amber-50 p-2 text-xs text-amber-900">
                La suma asegurada es más de 100 veces el monto reclamado. Revisa si agregaste ceros de más, porque esto reduce las alertas por monto.
              </p>
            ) : null}
            <Button onClick={run} disabled={loading} className="h-auto w-full px-4 py-2 text-[13px] font-semibold">
              {loading && <Loader2 className="h-4 w-4 animate-spin" />} Ejecutar simulación
            </Button>
            {error && <p className="text-sm text-destructive">{error}</p>}
          </div>
          <div className="institutional-card overflow-hidden">
            <div className="section-header">Resultado simulado</div>
            {result ? (
              <div className="space-y-3 p-4">
                <div className="flex items-end justify-between">
                  <div>
                    <p className="label-mono text-muted-foreground">PUNTAJE FINAL</p>
                    <p className="font-display text-4xl font-semibold">{Math.round(num(result.score_final))}</p>
                  </div>
                  <RiskBadge level={normalizeRisk(result.nivel_riesgo)} className="px-3 py-2" />
                </div>
                <p className="text-sm leading-relaxed text-muted-foreground">{result.explicacion}</p>
                {result.alertas?.length ? (
                  <div>
                    <p className="label-mono-md mb-2 font-bold uppercase">Alertas activadas</p>
                    <ul className="space-y-2 text-xs">
                      {result.alertas.slice(0, 5).map((alert, index) => {
                        const item = (alert || {}) as Record<string, unknown>
                        return (
                          <li key={`${String(item.code || item.name || index)}-${index}`} className="border border-border bg-[var(--surface-low)] p-2">
                            <span className="font-semibold">{String(item.code || 'ALERTA')}:</span> {alertToText(alert)}
                          </li>
                        )
                      })}
                    </ul>
                  </div>
                ) : null}
                <div>
                  <p className="label-mono-md mb-2 font-bold uppercase">Próximos pasos</p>
                  <ul className="space-y-2 text-sm">
                    {(result.ui?.recommended_next_steps || [result.accion_sugerida || 'Revisión humana.']).map((step) => <li key={step} className="border border-border bg-[var(--surface-low)] p-2">{step}</li>)}
                  </ul>
                </div>
              </div>
            ) : (
              <div className="flex min-h-[240px] items-center justify-center p-6 text-center text-sm text-muted-foreground">Complete el formulario y ejecute una simulación para ver el puntaje, las alertas y la recomendación.</div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}


function SelectField({ label, value, onChange, options }: { label: string; value: string; onChange: (value: string) => void; options: [string, string][] }) {
  return (
    <label className="block">
      <span className="label-mono-md font-bold uppercase text-muted-foreground">{label}</span>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger className="mt-1 w-full">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {options.map(([optionValue, optionLabel]) => (
            <SelectItem key={optionValue} value={optionValue}>{optionLabel}</SelectItem>
          ))}
        </SelectContent>
      </Select>
    </label>
  )
}

function BooleanField({ label, checked, onChange }: { label: string; checked: boolean; onChange: (checked: boolean) => void }) {
  return (
    <label className="flex items-center gap-2 rounded-md border border-border bg-[var(--surface-low)] px-3 py-2 text-sm">
      <Checkbox checked={checked} onCheckedChange={(next) => onChange(next === true)} />
      {label}
    </label>
  )
}

function Field({
  name,
  label,
  value,
  onChange,
  type = 'text',
  inputMode,
}: {
  name: string
  label: string
  value: string
  onChange: (value: string) => void
  type?: HTMLInputTypeAttribute
  inputMode?: HTMLAttributes<HTMLInputElement>['inputMode']
}) {
  return (
    <label className="block">
      <span className="label-mono-md font-bold uppercase text-muted-foreground">{label}</span>
      <Input name={name} type={type} inputMode={inputMode} value={value} onChange={(e) => onChange(e.target.value)} className="mt-1" autoComplete="off" />
    </label>
  )
}


function formatSubmittedAt(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Recibido recientemente'
  return new Intl.DateTimeFormat('es-EC', { dateStyle: 'short', timeStyle: 'short' }).format(date)
}

function sourceLabel(source: string) {
  if (source === 'csv') return 'Archivo de datos'
  if (source === 'txt') return 'TXT'
  if (source === 'pdf') return 'PDF'
  if (source === 'analysis') return 'Análisis guardado'
  return 'Documento'
}

function GlobalRelationshipMap({ claims, onAnalyze }: { claims: ClaimSummary[]; onAnalyze: (claim: ClaimSummary) => void }) {
  const [hoveredClaim, setHoveredClaim] = useState<ClaimSummary | null>(null)
  const topClaims = claims.slice(0, 9)
  const center = { x: 260, y: 150 }
  const satellites = topClaims.map((claim, index) => {
    const angle = (Math.PI * 2 * index) / Math.max(topClaims.length, 1) - Math.PI / 2
    const radius = index % 2 === 0 ? 112 : 86
    return {
      claim,
      x: center.x + Math.cos(angle) * radius,
      y: center.y + Math.sin(angle) * radius,
      color: getRiskColor(normalizeRisk(claim.nivel_riesgo)),
    }
  })
  const activeClaim = hoveredClaim
  const prompt = [
    'Explica el gráfico "Mapa global de relaciones" del Centro de Control.',
    'Quiero una explicación ejecutiva y accionable: qué representa, qué patrones se observan, qué casos parecen más prioritarios y qué preguntas debería hacer el analista.',
    `Nodos visibles: ${topClaims.map((claim) => `${claim.id_siniestro} puntaje ${Math.round(num(claim.score_final))} nivel ${getRiskLabel(normalizeRisk(claim.nivel_riesgo))}`).join('; ') || 'sin datos'}.`,
  ].join('\n')

  return (
    <div className="dark-panel relative h-[300px] overflow-hidden">
      <AIChartExplainButton prompt={prompt} className="border-white/25 bg-black/35 text-white hover:bg-white hover:text-black" />
      <div className="absolute inset-0 opacity-20 [background-image:linear-gradient(var(--primary-fixed)_1px,transparent_1px),linear-gradient(90deg,var(--primary-fixed)_1px,transparent_1px)] [background-size:32px_32px]" />
      <svg viewBox="0 0 520 320" className="absolute inset-0 h-full w-full">
        {satellites.map((node) => (
          <line key={`line-${node.claim.id_siniestro}`} x1={center.x} y1={center.y} x2={node.x} y2={node.y} stroke="rgba(218,226,253,.35)" strokeWidth="1" />
        ))}
        <circle cx={center.x} cy={center.y} r="44" fill="var(--primary-fixed)" opacity=".14" />
        <circle cx={center.x} cy={center.y} r="30" fill="var(--primary-fixed)" opacity=".22" />
        <text x={center.x} y={center.y - 4} textAnchor="middle" className="fill-white text-[11px] font-bold">CARTERA</text>
        <text x={center.x} y={center.y + 12} textAnchor="middle" className="fill-[var(--primary-fixed-dim)] text-[9px]">RIESGO</text>
        {satellites.map((node) => {
          const isActive = hoveredClaim?.id_siniestro === node.claim.id_siniestro
          const puntaje = Math.round(num(node.claim.score_final))
          return (
            <g
              key={node.claim.id_siniestro}
              className="cursor-pointer"
              onClick={() => onAnalyze(node.claim)}
              onMouseEnter={() => setHoveredClaim(node.claim)}
              onMouseLeave={() => setHoveredClaim(null)}
            >
              <circle cx={node.x} cy={node.y} r={isActive ? '30' : '26'} fill="none" stroke={node.color} opacity={isActive ? '.58' : '.35'} strokeWidth="6" />
              <circle cx={node.x} cy={node.y} r={isActive ? '23' : '20'} fill={node.color} opacity=".95" />
              <text x={node.x} y={node.y - 2} textAnchor="middle" className="fill-white text-[7px] font-bold">
                {node.claim.id_siniestro.replace('SIN-', 'SIN')}
              </text>
              <text x={node.x} y={node.y + 9} textAnchor="middle" className="fill-white text-[8px] font-bold">
                {puntaje}/100
              </text>
            </g>
          )
        })}
      </svg>
      <div className="absolute left-4 top-4">
        <p className="dark-panel-kicker label-mono-md uppercase">Mapa global de relaciones</p>
        <p className="dark-panel-muted mt-1 max-w-xs text-xs">Cada punto representa un siniestro prioritario. Pase el cursor para ver detalles o haga clic para analizar.</p>
      </div>
      {activeClaim && (
        <div className="dark-panel-card absolute right-4 top-4 w-[240px] rounded-lg p-4 shadow-xl backdrop-blur">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="dark-panel-muted label-mono">CASO EN FOCO</p>
              <p className="font-display text-xl font-semibold">{activeClaim.id_siniestro}</p>
            </div>
            <RiskBadge level={normalizeRisk(activeClaim.nivel_riesgo)}>
              {Math.round(num(activeClaim.score_final))}
            </RiskBadge>
          </div>
          <div className="dark-panel-muted mt-3 grid grid-cols-2 gap-2 text-xs">
            <div><span className="label-mono block text-white/60">RAMO</span>{activeClaim.ramo || 'N/D'}</div>
            <div><span className="label-mono block text-white/60">CIUDAD</span>{activeClaim.ciudad || 'N/D'}</div>
            <div className="col-span-2"><span className="label-mono block text-white/60">PROVEEDOR</span>{activeClaim.id_proveedor || activeClaim.beneficiario || 'N/D'}</div>
            <div><span className="label-mono block text-white/60">MONTO</span>{formatCurrency(activeClaim.monto_reclamado)}</div>
            <div><span className="label-mono block text-white/60">NIVEL</span>{getRiskLabel(normalizeRisk(activeClaim.nivel_riesgo))}</div>
          </div>
          <p className="dark-panel-muted mt-3 text-[11px]">Haga clic en el punto para abrir el análisis de este caso.</p>
        </div>
      )}
      <div className="dark-panel-muted absolute bottom-4 left-4 flex gap-3 text-xs">
        <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-[var(--risk-rojo)]" /> Alto/Crítico</span>
        <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-[var(--risk-amarillo)]" /> Medio</span>
        <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-[var(--risk-verde)]" /> Bajo</span>
      </div>
    </div>
  )
}

export function StepCommandCenter() {
  const { claims, loadClaims, isLoadingClaims, apiError, apiHint, setCurrentStep, setSelectedClaimId, setIsDataLoaded, userRole, analystSubmittedCases, analystSavedAnalyses } = useAppState()
  const [providerRanking, setProviderRanking] = useState<RiskAggregateRow[] | null>(null)
  const [cityRanking, setCityRanking] = useState<RiskAggregateRow[] | null>(null)
  const [branchRanking, setBranchRanking] = useState<RiskAggregateRow[] | null>(null)
  const [report, setReport] = useState<ExecutiveReport | null>(null)
  const [reportLoading, setReportLoading] = useState(false)
  const [historyCode, setHistoryCode] = useState('')
  const [historyError, setHistoryError] = useState<string | null>(null)

  useEffect(() => {
    if (!claims.length) void loadClaims()
  }, [claims.length, loadClaims])

  const loadCommandCenterData = async () => {
    setReportLoading(true)
    try {
      const [providers, cities, branches, executiveReport] = await Promise.all([
        getProviderRiskRanking(10).catch(() => null),
        getCityRiskDistribution().catch(() => null),
        getBranchRiskDistribution().catch(() => null),
        getExecutiveReport(10).catch(() => null),
      ])
      setProviderRanking(providers)
      setCityRanking(cities)
      setBranchRanking(branches)
      setReport(executiveReport)
    } finally {
      setReportLoading(false)
    }
  }

  useEffect(() => {
    void loadCommandCenterData()
  }, [])

  const analytics = useMemo(() => {
    const summary = report?.summary
    const providerRows = normalizeBackendRows(providerRanking, 'id_proveedor')
    const branchRows = normalizeBackendRows(branchRanking, 'ramo')
    const cityRows = normalizeBackendRows(cityRanking, 'ciudad')
    const riskDistribution = summary
      ? [
          { name: 'Crítico', risk: 'critico', total: summary.casos_rojos || 0, fill: getRiskColor('rojo') },
          { name: 'Medio', risk: 'medio', total: summary.casos_amarillos || 0, fill: getRiskColor('amarillo') },
          { name: 'Bajo', risk: 'bajo', total: summary.casos_verdes || 0, fill: getRiskColor('verde') },
        ].filter((row) => row.total > 0)
      : []
    const topCases = claims.slice(0, 10)
    return {
      total: summary?.total_siniestros ?? 0,
      totalAmount: summary?.monto_total_reclamado ?? 0,
      averagePuntaje: Math.round(Number(summary?.score_promedio_portafolio ?? 0)),
      riskDistribution,
      providerRows,
      branchRows,
      cityRows,
      topCases,
      criticalCount: summary?.casos_rojos ?? 0,
      mediumCount: summary?.casos_amarillos ?? 0,
      topProvider: providerRows[0]?.name || 'N/D',
      savingsEstimate: report?.ahorro_potencial_estimado?.ahorro_potencial_estimado ?? 0,
    }
  }, [claims, branchRanking, cityRanking, providerRanking, report])

  const analyzeClaim = (claim: ClaimSummary) => {
    setSelectedClaimId(claim.id_siniestro)
    setIsDataLoaded(true)
    setCurrentStep(userRole === 'executive' ? 5 : 2)
  }

  const searchInHistory = () => {
    const query = normalizeClaimCode(historyCode)
    if (!query) return
    const found = claims.find((c) => normalizeClaimCode(String(c.id_siniestro || '')) === query)
    if (!found) {
      setHistoryError(`No se encontró ${query}`)
      return
    }
    setHistoryError(null)
    analyzeClaim(found)
  }


  const submittedCaseRows = useMemo(() => {
    return analystSubmittedCases.slice(0, 6).map((submitted) => {
      const claim = claims.find((item) => item.id_siniestro === submitted.id) || null
      return { submitted, claim }
    })
  }, [analystSubmittedCases, claims])

  const savedAnalysisRows = useMemo(() => {
    return analystSavedAnalyses.slice(0, 6).map((saved) => {
      const claim = claims.find((item) => item.id_siniestro === saved.id) || null
      return { saved, claim }
    })
  }, [analystSavedAnalyses, claims])

  const isAnalyst = userRole === 'analyst'

  const kpis = [
    { label: 'Siniestros evaluados', value: analytics.total.toString(), note: 'Cartera priorizada', Icon: FileSearch },
    { label: 'Casos alto/crítico', value: analytics.criticalCount.toString(), note: 'Revisión prioritaria', Icon: AlertTriangle },
    { label: 'Monto expuesto', value: formatCurrency(analytics.totalAmount), note: 'Total reclamado', Icon: CircleDollarSign },
    { label: 'Puntaje medio', value: `${analytics.averagePuntaje}/100`, note: 'Riesgo global', Icon: Target },
    { label: 'Ahorro potencial', value: formatCurrency(analytics.savingsEstimate), note: 'Estimación ilustrativa', Icon: CircleDollarSign },
  ]

  return (
    <section className="px-3 py-5 lg:px-6">
      <div className="mx-auto max-w-7xl space-y-4">
        <header className="grid gap-4 lg:grid-cols-[1.4fr_.6fr]">
          <div className="dark-panel dark-panel-border border p-6">
            <div className="dark-panel-kicker flex items-center gap-2">
              <GitBranch className="h-5 w-5" />
              <span className="label-mono-md uppercase">Revisión de alertas</span>
            </div>
            <h1 className="dark-panel-heading display-heading mt-3 text-3xl lg:text-4xl">Centro de control de alertas</h1>
            <p className="dark-panel-muted mt-2 max-w-2xl text-sm">
              {isAnalyst ? 'Bandeja operativa de riesgo, carga de datos y casos prioritarios para revisión con el asistente.' : 'Panorama ejecutivo de riesgo, recurrencia de alertas e impacto para decisión gerencial.'}
            </p>
            <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center">
              {isAnalyst ? (
                <Button onClick={() => setCurrentStep(1)} className="dark-panel-cta h-auto px-4 py-2 text-[13px] font-semibold">
                  Cargar datos e iniciar análisis <ArrowRight className="h-4 w-4" />
                </Button>
              ) : (
                <span className="inline-flex items-center justify-center gap-2 rounded-md border border-[var(--primary-fixed-dim)] px-4 py-2 text-[13px] font-semibold text-[var(--primary-fixed-dim)]">
                  Datos gestionados por el analista
                </span>
              )}
              <Button variant="outline-inverse" onClick={() => { void loadClaims(); void loadCommandCenterData() }} className="h-auto px-4 py-2 text-[13px] font-semibold">
                Sincronizar datos
              </Button>
              <ReportDialog report={report} loading={reportLoading} onLoad={() => void loadCommandCenterData()} />
              <SimulatorDialog />
            </div>
          </div>
          <div className="institutional-card p-4">
            <div className="flex items-start gap-3">
              <ShieldCheck className="h-8 w-8 text-[var(--risk-verde)]" />
              <div>
                <p className="label-mono-md font-bold uppercase">Marco ético</p>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                  La solución genera alertas explicables para revisión humana. No acusa fraude, no rechaza reclamos y no sustituye al analista.
                </p>
              </div>
            </div>
            <div className="mt-4 grid grid-cols-2 gap-2">
              <div className="bg-[var(--surface-low)] p-3"><p className="label-mono text-muted-foreground">Proveedor foco</p><p className="truncate font-semibold">{analytics.topProvider}</p></div>
              <div className="bg-[var(--surface-low)] p-3"><p className="label-mono text-muted-foreground">Casos medios</p><p className="font-semibold">{analytics.mediumCount}</p></div>
            </div>
          </div>
        </header>

        {apiError && (
          <div className="border border-destructive bg-[var(--error-container)] p-4 text-[var(--on-error-container)]">
            <p className="font-semibold">{apiError}</p>
            {apiHint && <p className="mt-1 text-sm">{apiHint}</p>}
          </div>
        )}

        {!claims.length && !isLoadingClaims ? (
          <div className="institutional-card flex min-h-[240px] flex-col items-center justify-center gap-3 p-6 text-center">
            <UploadCloud className="h-12 w-12 text-muted-foreground" />
            <div>
              <h2 className="font-display text-xl font-semibold">Sin datos para visualizar</h2>
              <p className="mt-2 text-sm text-muted-foreground">Carga la información para activar el centro de control.</p>
            </div>
            {isAnalyst ? (
              <Button onClick={() => setCurrentStep(1)} className="h-auto px-4 py-2 text-[13px] font-semibold">Ir a carga de datos</Button>
            ) : (
              <p className="max-w-md text-sm text-muted-foreground">Solicita al analista cargar los datos para que esta vista muestre los indicadores, impacto y casos críticos.</p>
            )}
          </div>
        ) : (
          <>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
              {kpis.map((kpi, i) => {
                const Icon = kpi.Icon
                return (
                  <div key={kpi.label} className="institutional-card stagger-item p-4" style={{ '--i': i } as Record<string, number>}>
                    <div className="flex items-center justify-between">
                      <p className="label-mono-md uppercase text-muted-foreground">{kpi.label}</p>
                      <Icon className="h-5 w-5 text-[var(--brand)]" />
                    </div>
                    <p className="mt-2 font-display text-2xl font-semibold">{kpi.value}</p>
                    <p className="mt-1 text-sm text-muted-foreground">{kpi.note}</p>
                  </div>
                )
              })}
            </div>

            <div className="grid grid-cols-12 gap-4">
              <div className="institutional-card col-span-12 overflow-hidden xl:col-span-7">
                <div className="section-header flex items-center gap-2"><GitBranch className="h-4 w-4" />Red de relaciones de casos</div>
                <GlobalRelationshipMap claims={claims} onAnalyze={analyzeClaim} />
              </div>
              <div className="institutional-card col-span-12 overflow-hidden xl:col-span-5">
                <div className="section-header flex items-center gap-2"><BarChart3 className="h-4 w-4" />Distribución por semáforo</div>
                <div className="relative p-4">
                  <AIChartExplainButton
                    prompt={`Explica el gráfico "Distribución por semáforo" del Centro de Control. Resume qué significa la proporción de casos críticos, medios y bajos, qué tan urgente es la cartera y qué acciones recomendarías. Datos: ${analytics.riskDistribution.map((row) => `${row.name}: ${row.total}`).join(', ') || 'sin datos'}. Total cartera: ${analytics.total}.`}
                  />
                  <ChartContainer config={{ total: { label: 'Casos', color: 'var(--chart-1)' } }} className="h-[220px] w-full">
                    <PieChart>
                      <ChartTooltip content={<ChartTooltipContent nameKey="name" />} />
                      <Pie data={analytics.riskDistribution} dataKey="total" nameKey="name" innerRadius={62} outerRadius={96} paddingAngle={4}>
                        {analytics.riskDistribution.map((entry) => <Cell key={entry.risk} fill={entry.fill} />)}
                      </Pie>
                    </PieChart>
                  </ChartContainer>
                  <div className="grid grid-cols-3 gap-2">
                    {analytics.riskDistribution.map((row) => (
                      <div key={row.risk} className="bg-[var(--surface-low)] p-2 text-center">
                        <p className="label-mono" style={{ color: row.fill }}>{row.name}</p>
                        <p className="font-display text-lg font-semibold">{row.total}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-12 gap-4">
              <div className="institutional-card col-span-12 overflow-hidden lg:col-span-4">
                <div className="section-header flex items-center gap-2"><Building2 className="h-4 w-4" />Riesgo por proveedor</div>
                <div className="relative p-3">
                  <AIChartExplainButton
                    prompt={`Explica el gráfico "Riesgo por proveedor". Identifica proveedores con mayor puntaje promedio, concentración de casos rojos y posibles acciones de auditoría. Datos principales: ${analytics.providerRows.slice(0, 6).map((row) => `${row.name}: puntaje ${row.avgRisk}, ${row.total} casos, ${row.casosRojos} rojos`).join('; ') || 'sin datos'}.`}
                  />
                  <ChartContainer config={{ avgRisk: { label: 'Puntaje medio', color: 'var(--chart-4)' } }} className="h-[200px] w-full">
                    <BarChart data={analytics.providerRows} layout="vertical" margin={{ left: 8, right: 8 }}>
                      <CartesianGrid horizontal={false} />
                      <XAxis type="number" domain={[0, 100]} hide />
                      <YAxis dataKey="name" type="category" tickLine={false} axisLine={false} width={82} fontSize={10} />
                      <ChartTooltip content={<ChartTooltipContent />} />
                      <Bar dataKey="avgRisk" radius={4} fill="var(--color-avgRisk)" />
                    </BarChart>
                  </ChartContainer>
                </div>
              </div>
              <div className="institutional-card col-span-12 overflow-hidden lg:col-span-4">
                <div className="section-header flex items-center gap-2"><UsersRound className="h-4 w-4" />Riesgo por ramo</div>
                <div className="relative p-3">
                  <AIChartExplainButton
                    prompt={`Explica el gráfico "Riesgo por ramo". Indica qué ramos concentran más riesgo, cómo interpretarlo sin acusar fraude y qué priorización sugieres. Datos principales: ${analytics.branchRows.slice(0, 6).map((row) => `${row.name}: puntaje ${row.avgRisk}, ${row.total} casos, ${row.casosRojos} rojos`).join('; ') || 'sin datos'}.`}
                  />
                  <ChartContainer config={{ avgRisk: { label: 'Puntaje medio', color: 'var(--chart-3)' } }} className="h-[200px] w-full">
                    <BarChart data={analytics.branchRows} margin={{ left: 4, right: 4 }}>
                      <CartesianGrid vertical={false} />
                      <XAxis dataKey="name" tickLine={false} axisLine={false} fontSize={10} />
                      <YAxis domain={[0, 100]} tickLine={false} axisLine={false} fontSize={10} />
                      <ChartTooltip content={<ChartTooltipContent />} />
                      <Bar dataKey="avgRisk" radius={4} fill="var(--color-avgRisk)" />
                    </BarChart>
                  </ChartContainer>
                </div>
              </div>
              <div className="institutional-card col-span-12 overflow-hidden lg:col-span-4">
                <div className="section-header flex items-center gap-2"><MapPin className="h-4 w-4" />Riesgo por ciudad</div>
                <div className="relative p-3">
                  <AIChartExplainButton
                    prompt={`Explica el gráfico "Riesgo por ciudad". Señala ciudades con mayor exposición, posibles sesgos/limitaciones y siguientes pasos de revisión humana. Datos principales: ${analytics.cityRows.slice(0, 6).map((row) => `${row.name}: puntaje ${row.avgRisk}, ${row.total} casos, ${row.casosRojos} rojos`).join('; ') || 'sin datos'}.`}
                  />
                  <ChartContainer config={{ avgRisk: { label: 'Puntaje medio', color: 'var(--chart-1)' } }} className="h-[200px] w-full">
                    <BarChart data={analytics.cityRows} margin={{ left: 4, right: 4 }}>
                      <CartesianGrid vertical={false} />
                      <XAxis dataKey="name" tickLine={false} axisLine={false} fontSize={10} />
                      <YAxis domain={[0, 100]} tickLine={false} axisLine={false} fontSize={10} />
                      <ChartTooltip content={<ChartTooltipContent />} />
                      <Bar dataKey="avgRisk" radius={4} fill="var(--color-avgRisk)" />
                    </BarChart>
                  </ChartContainer>
                </div>
              </div>
            </div>


            {(
              <div className="institutional-card overflow-hidden">
                <div className="section-header flex flex-col gap-1 md:flex-row md:items-center md:justify-between">
                  <span className="flex items-center gap-2"><Inbox className="h-4 w-4" />{isAnalyst ? 'Mis siniestros analizados' : 'Análisis cerrados por el analista'}</span>
                  <span>{isAnalyst ? 'Guardados en este navegador · clic para reabrir el reporte' : 'Guardados en este navegador para revisión ejecutiva'}</span>
                </div>
                {savedAnalysisRows.length ? (
                  <div className="grid gap-3 p-3 lg:grid-cols-3">
                    {savedAnalysisRows.map(({ saved, claim }) => {
                      const risk = normalizeRisk(saved.riskLevel || claim?.nivel_riesgo)
                      const score = saved.score ?? claim?.score_final
                      return (
                        <button
                          key={`${saved.id}-${saved.savedAt}`}
                          type="button"
                          onClick={() => {
                            setSelectedClaimId(saved.id)
                            setIsDataLoaded(true)
                            setCurrentStep(5)
                          }}
                          className="group flex min-h-[260px] flex-col border border-border bg-[var(--surface-low)] p-3 text-left transition-colors hover:border-primary hover:bg-[var(--surface-high)]"
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <p className="label-mono text-muted-foreground">Análisis cerrado · {formatSubmittedAt(saved.savedAt)}</p>
                              <p className="mt-1 font-mono text-sm font-bold text-foreground">{saved.id}</p>
                            </div>
                            <RiskBadge level={risk} size="sm" />
                          </div>
                          <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                            <div><span className="label-mono block">Ramo</span>{saved.branch || claim?.ramo || 'Pendiente'}</div>
                            <div><span className="label-mono block">Ciudad</span>{saved.city || claim?.ciudad || 'Pendiente'}</div>
                            <div><span className="label-mono block">Monto</span>{formatCurrency(saved.amount ?? claim?.monto_reclamado)}</div>
                            <div><span className="label-mono block">Puntaje</span>{score != null ? `${Math.round(num(score))}/100` : '—'}</div>
                          </div>
                          <p className="mt-3 line-clamp-3 text-sm text-foreground">{saved.summary || 'Resumen del análisis no disponible.'}</p>
                          <div className="mt-3 rounded border border-border bg-background p-2 text-xs text-muted-foreground">
                            <span className="label-mono block text-foreground">Recomendación</span>
                            <span className="line-clamp-2">{saved.recommendation || 'Revisión humana sugerida.'}</span>
                          </div>
                          {saved.topAlerts.length ? (
                            <p className="mt-2 line-clamp-2 text-xs text-muted-foreground">Señales: {saved.topAlerts.slice(0, 2).join(' · ')}</p>
                          ) : null}
                          <p className="mt-auto pt-3 text-xs font-semibold text-primary opacity-90 group-hover:underline">{isAnalyst ? 'Abrir reporte →' : 'Abrir reporte ejecutivo →'}</p>
                        </button>
                      )
                    })}
                  </div>
                ) : submittedCaseRows.length ? (
                  <div className="grid gap-3 p-3 lg:grid-cols-3">
                    {submittedCaseRows.map(({ submitted, claim }) => {
                      const risk = normalizeRisk(claim?.nivel_riesgo)
                      return (
                        <button
                          key={`${submitted.id}-${submitted.submittedAt}`}
                          type="button"
                          onClick={() => {
                            setSelectedClaimId(submitted.id)
                            setIsDataLoaded(true)
                            setCurrentStep(5)
                          }}
                          className="group border border-border bg-[var(--surface-low)] p-3 text-left transition-colors hover:border-primary hover:bg-[var(--surface-high)]"
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <p className="label-mono text-muted-foreground">{sourceLabel(submitted.source)} · {formatSubmittedAt(submitted.submittedAt)}</p>
                              <p className="mt-1 font-mono text-sm font-bold text-foreground">{submitted.id}</p>
                            </div>
                            {claim ? <RiskBadge level={risk} size="sm" /> : <span className="label-mono rounded border border-border px-2 py-1 text-[10px] text-muted-foreground">Sin detalle</span>}
                          </div>
                          <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                            <div><span className="label-mono block">Ramo</span>{claim?.ramo || 'Pendiente'}</div>
                            <div><span className="label-mono block">Ciudad</span>{claim?.ciudad || 'Pendiente'}</div>
                            <div><span className="label-mono block">Monto</span>{claim ? formatCurrency(claim.monto_reclamado) : '—'}</div>
                            <div><span className="label-mono block">Puntaje</span>{claim?.score_final != null ? `${Math.round(num(claim.score_final))}/100` : '—'}</div>
                          </div>
                          {submitted.filename ? <p className="mt-3 truncate text-[11px] text-muted-foreground">Origen: {submitted.filename}</p> : null}
                          <p className="mt-3 text-xs font-semibold text-primary opacity-90 group-hover:underline">{isAnalyst ? 'Abrir reporte →' : 'Abrir reporte ejecutivo →'}</p>
                        </button>
                      )
                    })}
                  </div>
                ) : (
                  <div className="p-4 text-sm text-muted-foreground">
                    {isAnalyst
                      ? 'Aún no has cerrado análisis en este navegador. Cuando uses “Guardar y cerrar” en Resultado y motivos, el siniestro quedará aquí con su resumen, recomendación y señales clave.'
                      : 'Todavía no hay análisis cerrados por el analista en este navegador. Cuando el analista use “Guardar y cerrar” en Resultado y motivos, aparecerán aquí con resumen, recomendación y señales clave.'}
                  </div>
                )}
              </div>
            )}

            <div className="institutional-card overflow-hidden">
              <div className="section-header flex flex-col gap-3 md:flex-row md:items-center md:justify-between"><span>10 casos prioritarios (Historial)</span><span>{isLoadingClaims ? 'Sincronizando...' : 'Ordenado por nivel de prioridad'}</span></div>
              <div className="border-b border-border bg-[var(--surface-low)] p-3">
                <div className="flex flex-col gap-2 md:flex-row md:items-center">
                  <Input
                    value={historyCode}
                    onChange={(e) => setHistoryCode(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && searchInHistory()}
                    placeholder="Buscar en historial por código (SIN-046)"
                    className="md:max-w-sm"
                  />
                  <Button variant="outline" onClick={searchInHistory} className="label-mono-md">Buscar</Button>
                </div>
                {historyError && <p className="mt-2 text-xs text-destructive">{historyError}</p>}
              </div>
              <div className="overflow-x-auto">
                <table className="zebra w-full text-left">
                  <thead>
                    <tr className="border-b border-border bg-[var(--surface-low)]">
                      {['ID', 'Ramo', 'Ciudad', 'Proveedor', 'Monto', 'Puntaje', 'Nivel', 'Alertas', 'Acción'].map((header) => (
                        <th key={header} className="label-mono px-4 py-2 text-muted-foreground">{header}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {analytics.topCases.map((claim) => {
                      const risk = normalizeRisk(claim.nivel_riesgo)
                      return (
                        <tr key={claim.id_siniestro} className="border-b border-border transition-colors last:border-b-0 hover:bg-[var(--surface-low)]">
                          <td className="px-4 py-3 font-mono text-sm font-semibold">{claim.id_siniestro}</td>
                          <td className="px-4 py-3 text-sm">{claim.ramo || 'N/D'}</td>
                          <td className="px-4 py-3 text-sm">{claim.ciudad || 'N/D'}</td>
                          <td className="px-4 py-3 font-mono text-xs">{claim.id_proveedor || claim.beneficiario || 'N/D'}</td>
                          <td className="px-4 py-3 font-mono text-xs">{formatCurrency(claim.monto_reclamado)}</td>
                          <td className="px-4 py-3"><span className="font-display text-lg font-semibold">{Math.round(num(claim.score_final))}</span></td>
                          <td className="px-4 py-3"><RiskBadge level={risk} /></td>
                          <td className="px-4 py-3 text-sm">{countAlerts(claim)}</td>
                          <td className="px-4 py-3"><Button size="sm" onClick={() => analyzeClaim(claim)} className="label-mono">Analizar</Button></td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              {[
                { title: 'Priorización rápida', text: 'Ordena casos por riesgo para enfocar revisión humana.' },
                { title: 'Patrones visibles', text: 'Expone recurrencia por proveedor, ramo y ciudad.' },
                { title: 'Explicabilidad', text: 'Conecta la vista ejecutiva con el análisis verificable por caso.' },
              ].map((item) => (
                <div key={item.title} className="institutional-card p-4">
                  <Bot className="h-5 w-5 text-[var(--on-secondary-container)]" />
                  <h3 className="mt-2 font-display text-lg font-semibold">{item.title}</h3>
                  <p className="mt-2 text-sm text-muted-foreground">{item.text}</p>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </section>
  )
}
