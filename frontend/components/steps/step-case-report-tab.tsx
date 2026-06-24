'use client'

import { useEffect, useMemo, useState } from 'react'
import {
  ArrowRight,
  Bot,
  ClipboardList,
  Download,
  FileText,
  GitBranch,
  Loader2,
  UploadCloud,
} from 'lucide-react'
import { useAppState } from '@/lib/app-context'
import {
  ClaimDossier,
  ExecutiveReport,
  type AgentChatMessage,
  getAgentThread,
  getClaimDossier,
  getExecutiveReport,
} from '@/lib/api'
import { formatCurrency } from '@/lib/claims-data'
import { safeGraphPayload, buildClaimGraph } from '@/components/graph/graph-utils'
import { ClaimNetworkMini } from '@/components/graph/claim-network-mini'
import { RecurringEntitiesList } from '@/components/graph/recurring-entities-list'
import { RecurrenceTopChart } from '@/components/graph/recurrence-top-chart'
import { RiskSpiderChart } from '@/components/graph/risk-spider-chart'
import { buildChartInsights } from '@/lib/graph-insights'
import { buildCaseReportMarkdown, downloadCaseReportMarkdown, downloadCaseReportPdf } from '@/lib/case-report-export'
import { ScoreObjectiveCard } from '@/components/report/score-objective-card'
import { ChartInsight } from '@/components/report/chart-insight'
import { alertToText } from '@/lib/api'
import { sanitizeAiText } from '@/lib/utils'
import { UI_COPY } from '@/lib/human-labels'

const num = (v: unknown) => Number(v ?? 0)
const THREAD_STORAGE_KEY = 'rastroseguro-agent-thread-id'
const USER_STORAGE_KEY = 'rastroseguro-agent-user-id'
const DEVICE_STORAGE_KEY = 'rastroseguro-agent-device-id'

type ReportChatMessage = {
  id?: string
  role: 'user' | 'assistant'
  content: string
  sectionId?: string | null
  response?: unknown
}

function yes(value: unknown) {
  return ['si', 'sí', 'true', '1', 'yes', 'completo'].includes(String(value ?? '').trim().toLowerCase()) || value === true
}

function getScopedChatIdentity(role: 'analyst' | 'executive' | null): { userId: string; threadId: string | null } {
  try {
    const deviceId = window.localStorage.getItem(DEVICE_STORAGE_KEY) || window.localStorage.getItem(USER_STORAGE_KEY) || 'anonymous'
    const userId = role ? `${deviceId}:${role}` : deviceId
    return {
      userId,
      threadId: window.localStorage.getItem(`${THREAD_STORAGE_KEY}:${userId}`),
    }
  } catch {
    return { userId: 'anonymous', threadId: null }
  }
}

function toReportChatMessage(message: AgentChatMessage): ReportChatMessage {
  return {
    id: message.id,
    role: message.role,
    content: message.content,
    sectionId: message.section_id || null,
    response: message.role === 'assistant'
      ? { intent: message.intent, data: message.data, message: message.content }
      : undefined,
  }
}

function mergeReportChatMessages(
  persistedMessages: ReportChatMessage[],
  liveMessages: ReportChatMessage[],
): ReportChatMessage[] {
  const seen = new Set<string>()
  const merged: ReportChatMessage[] = []

  for (const message of [...persistedMessages, ...liveMessages]) {
    const key = message.id || `${message.role}|${message.sectionId || ''}|${message.content}`
    if (seen.has(key)) continue
    seen.add(key)
    merged.push(message)
  }

  return merged
}

export function StepCaseReportTab({ compact = false }: { compact?: boolean }) {
  const {
    selectedClaim,
    selectedClaimId,
    selectedExplanation,
    loadClaimExplanation,
    claims,
    uploadedFile,
    isDataLoaded,
    userRole,
    chatMessages,
    setShowChat,
  } = useAppState()

  const [dossier, setDossier] = useState<ClaimDossier | null>(null)
  const [portfolio, setPortfolio] = useState<ExecutiveReport | null>(null)
  const [loading, setLoading] = useState(false)
  const [exportingMd, setExportingMd] = useState(false)
  const [exportingPdf, setExportingPdf] = useState(false)
  const [persistedChatMessages, setPersistedChatMessages] = useState<ReportChatMessage[]>([])

  const isExecutive = userRole === 'executive'

  useEffect(() => {
    if (selectedClaimId && selectedExplanation?.id_siniestro !== selectedClaimId) {
      void loadClaimExplanation(selectedClaimId)
    }
  }, [loadClaimExplanation, selectedClaimId, selectedExplanation?.id_siniestro])

  useEffect(() => {
    if (!selectedClaimId) return
    setLoading(true)
    Promise.all([getClaimDossier(selectedClaimId), getExecutiveReport(10)])
      .then(([dossierData, reportData]) => {
        setDossier(dossierData)
        setPortfolio(reportData)
      })
      .catch(() => {
        setDossier(null)
        setPortfolio(null)
      })
      .finally(() => setLoading(false))
  }, [selectedClaimId])


  useEffect(() => {
    if (!selectedClaimId) {
      setPersistedChatMessages([])
      return
    }

    const { userId, threadId } = getScopedChatIdentity(userRole)
    if (!threadId) {
      setPersistedChatMessages([])
      return
    }

    let cancelled = false
    void getAgentThread(threadId, userId)
      .then((thread) => {
        if (!cancelled) setPersistedChatMessages(thread.history.map(toReportChatMessage))
      })
      .catch(() => {
        if (!cancelled) setPersistedChatMessages([])
      })

    return () => {
      cancelled = true
    }
  }, [selectedClaimId, userRole])

  const graphPayload = useMemo(() => {
    const hasCurrentExplanation = selectedExplanation?.id_siniestro === selectedClaimId
    const details = hasCurrentExplanation
      ? (selectedExplanation?.detalles_avanzados as Record<string, unknown> | undefined)?.grafo
      : null
    return safeGraphPayload(
      details
        ? { ...(details as Record<string, unknown>), id_siniestro: selectedClaim?.id_siniestro, score_grafo: selectedClaim?.score_grafo }
        : null,
      selectedClaim?.id_siniestro || 'SIN-NA',
    )
  }, [selectedClaim, selectedClaimId, selectedExplanation])

  const chartInsights = useMemo(
    () => buildChartInsights(selectedClaim, claims, graphPayload),
    [selectedClaim, claims, graphPayload],
  )

  const claimGraph = useMemo(
    () => buildClaimGraph(graphPayload),
    [graphPayload],
  )

  const reportChatMessages = useMemo(
    () => mergeReportChatMessages(persistedChatMessages, chatMessages),
    [persistedChatMessages, chatMessages],
  )

  if (!selectedClaim || !selectedClaimId) {
    return (
      <div className="flex min-h-[40vh] flex-col items-center justify-center gap-4 text-muted-foreground">
        <FileText className="h-12 w-12" />
        <p>Selecciona un caso para generar el reporte.</p>
      </div>
    )
  }

  const alertas = (selectedExplanation?.alertas?.length
    ? selectedExplanation.alertas
    : selectedClaim.alertas_activadas instanceof Array
      ? selectedClaim.alertas_activadas
      : []) as unknown[]

  const handleExportMarkdown = async () => {
    setExportingMd(true)
    try {
      const markdown = buildCaseReportMarkdown({
        claim: selectedClaim,
        explanation: selectedExplanation,
        dossier,
        graphPayload,
        claims,
        uploadedFileName: uploadedFile?.name ?? null,
        portfolioReport: portfolio,
        chatMessages: reportChatMessages,
      })
      downloadCaseReportMarkdown(markdown, selectedClaim.id_siniestro)
    } finally {
      setExportingMd(false)
    }
  }

  const handleExportPdf = async () => {
    setExportingPdf(true)
    try {
      await downloadCaseReportPdf({
        claim: selectedClaim,
        explanation: selectedExplanation,
        dossier,
        graphPayload,
        claims,
        uploadedFileName: uploadedFile?.name ?? null,
        portfolioReport: portfolio,
        chatMessages: reportChatMessages,
      })
    } finally {
      setExportingPdf(false)
    }
  }

  const executiveTakeaway = sanitizeAiText(
    dossier?.executive_takeaway || dossier?.investigation_summary || selectedExplanation?.explicacion || '',
  )

  return (
    <div className="space-y-4">
      {loading && (
        <div className="institutional-card flex items-center gap-2 p-4 text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          Consolidando reporte...
        </div>
      )}

      {isExecutive && executiveTakeaway && (
        <section className="dark-panel dark-panel-border border p-5">
          <p className="label-mono-md uppercase text-white/70">Lectura ejecutiva</p>
          <p className="dark-panel-heading mt-2 text-lg text-white">{executiveTakeaway}</p>
        </section>
      )}

      <ScoreObjectiveCard
        claim={selectedClaim}
        explanation={selectedExplanation}
        mainDriverComponent={dossier?.main_driver?.componente}
        mainDriverValue={dossier?.main_driver?.valor}
        compact={compact || isExecutive}
      />


      <section className="institutional-card overflow-hidden">
        <div className="section-header">Gráficos del caso</div>
        <div className="space-y-5 p-4">
          <div className="space-y-2 rounded-lg border border-border bg-[var(--surface-low)] p-4">
            <p className="label-mono-md font-bold uppercase text-muted-foreground">Red de relaciones</p>
            <ClaimNetworkMini nodes={claimGraph.nodes} edges={claimGraph.edges} />
            <ChartInsight text={chartInsights.graph} />
          </div>

          <div className="space-y-2">
            <p className="label-mono-md font-bold uppercase text-muted-foreground px-1">
              {UI_COPY.comparePortfolio}
            </p>
            <RiskSpiderChart selectedClaim={selectedClaim} claims={claims} />
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <div className="space-y-2 rounded-lg border border-border bg-[var(--surface-low)] p-4">
              <p className="label-mono-md font-bold uppercase text-muted-foreground">Elementos repetidos en la cartera</p>
              <RecurrenceTopChart claims={claims} currentClaimId={selectedClaimId} limit={isExecutive ? 6 : 8} />
              <ChartInsight text={chartInsights.recurrence} />
            </div>

            <div className="space-y-2 rounded-lg border border-border bg-[var(--surface-low)] p-4">
              <p className="label-mono-md font-bold uppercase text-muted-foreground">
                {UI_COPY.repeatingElements} (este caso)
              </p>
              <RecurringEntitiesList entities={graphPayload.recurring_entities} limit={isExecutive ? 5 : 8} />
            </div>
          </div>
        </div>
      </section>

      {portfolio?.summary && (
        <section className="institutional-card overflow-hidden">
          <div className="section-header">Contexto de la cartera</div>
          <div className="grid gap-3 p-4 md:grid-cols-4">
            <Kpi label="Total" value={portfolio.summary.total_siniestros.toLocaleString()} />
            <Kpi label="Casos rojos" value={portfolio.summary.casos_rojos.toLocaleString()} />
            <Kpi label="% rojo" value={`${portfolio.summary.porcentaje_rojo}%`} />
            <Kpi label="Monto rojo" value={formatCurrency(portfolio.summary.monto_reclamado_casos_rojos)} />
          </div>
          {portfolio.top_casos?.length ? (
            <div className="border-t border-border px-4 pb-4">
              <p className="label-mono-md mb-2 font-bold uppercase text-muted-foreground">Principales casos de la cartera</p>
              <div className="flex flex-wrap gap-2">
                {portfolio.top_casos.slice(0, 5).map((c) => (
                  <span key={String(c.id_siniestro)} className="rounded-md border border-border bg-[var(--surface-low)] px-2 py-1 font-mono text-xs">
                    {String(c.id_siniestro)} · {Math.round(num(c.score_final))}
                  </span>
                ))}
              </div>
            </div>
          ) : null}
        </section>
      )}

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={() => void handleExportPdf()}
          disabled={exportingPdf || exportingMd}
          className="focus-ring inline-flex items-center gap-2 bg-primary px-5 py-2.5 label-mono-md text-primary-foreground"
        >
          {exportingPdf ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
          Descargar PDF
        </button>
        <button
          type="button"
          onClick={() => void handleExportMarkdown()}
          disabled={exportingPdf || exportingMd}
          className="focus-ring inline-flex items-center gap-2 border border-border px-5 py-2.5 label-mono-md text-foreground hover:bg-[var(--surface-container)]"
        >
          {exportingMd ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
          Descargar resumen (.md)
        </button>
        <button
          type="button"
          onClick={() => setShowChat(true)}
          className="focus-ring inline-flex items-center gap-2 border border-border px-5 py-2.5 label-mono-md text-foreground hover:bg-[var(--surface-container)]"
        >
          <Bot className="h-4 w-4" />
          Preguntar al asistente
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}

function StageCard({
  step,
  icon: Icon,
  title,
  text,
}: {
  step?: number
  icon: typeof UploadCloud
  title: string
  text: string
}) {
  return (
    <div className="rounded-md border border-border bg-[var(--surface-low)] p-3">
      <div className="mb-2 flex items-center gap-2">
        {step != null && <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">{step}</span>}
        <Icon className="h-4 w-4 text-muted-foreground" />
        <p className="label-mono-md font-bold uppercase">{title}</p>
      </div>
      <p className="text-sm text-muted-foreground">{text}</p>
    </div>
  )
}

function Kpi({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border bg-[var(--surface-low)] p-3">
      <p className="label-mono text-muted-foreground">{label}</p>
      <p className="font-display text-xl font-semibold">{value}</p>
    </div>
  )
}
