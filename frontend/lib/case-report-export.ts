import { alertToText, ClaimDossier, ClaimExplanation, ClaimSummary, ExecutiveReport } from '@/lib/api'
import { formatCurrency, getRiskLabel } from '@/lib/claims-data'
import { buildChartInsights } from '@/lib/graph-insights'
import { buildContributionRows } from '@/lib/score-weights'
import { ClaimGraphPayload } from '@/components/graph/graph-types'
import { UI_COPY } from '@/lib/human-labels'
import { sanitizeAiText } from '@/lib/utils'

const num = (v: unknown) => Number(v ?? 0)

type ReportChatMessage = {
  id?: string
  role: 'user' | 'assistant'
  content: string
  sectionId?: string | null
  response?: unknown
}

export interface CaseReportChatQa {
  question: string
  answer: string
}

function yes(value: unknown) {
  return ['si', 'sí', 'true', '1', 'yes', 'completo'].includes(String(value ?? '').trim().toLowerCase()) || value === true
}

function truncateText(text: string, max: number): string {
  const clean = sanitizeAiText(text).replace(/\s+/g, ' ').trim()
  if (clean.length <= max) return clean
  return `${clean.slice(0, max - 1).trim()}…`
}

function messageMatchesClaim(message: ReportChatMessage, claimId: string): boolean {
  const needle = claimId.toUpperCase()
  const body = `${message.content || ''} ${JSON.stringify(message.response ?? '')}`.toUpperCase()
  return body.includes(needle)
}

export function buildClaimChatSummary(messages: ReportChatMessage[] = [], claimId: string, limit = 6): CaseReportChatQa[] {
  if (!claimId || !messages.length) return []

  const claimSections = new Set(
    messages
      .filter((message) => message.sectionId && messageMatchesClaim(message, claimId))
      .map((message) => message.sectionId as string),
  )

  const seen = new Set<string>()
  const relevant = messages.filter((message) => {
    if (!message.content?.trim()) return false
    const matches = messageMatchesClaim(message, claimId) || Boolean(message.sectionId && claimSections.has(message.sectionId))
    if (!matches) return false
    const key = message.id || `${message.role}|${message.sectionId || ''}|${message.content}`
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })

  const pairs: CaseReportChatQa[] = []
  let pendingQuestion: string | null = null

  for (const message of relevant) {
    if (message.role === 'user') {
      pendingQuestion = truncateText(message.content, 180)
      continue
    }

    if (message.role === 'assistant' && pendingQuestion) {
      pairs.push({
        question: pendingQuestion,
        answer: truncateText(message.content, 360),
      })
      pendingQuestion = null
      if (pairs.length >= limit) break
    }
  }

  return pairs
}

export interface CaseReportExportInput {
  claim: ClaimSummary
  explanation?: ClaimExplanation | null
  dossier?: ClaimDossier | null
  graphPayload: ClaimGraphPayload
  claims: ClaimSummary[]
  uploadedFileName?: string | null
  portfolioReport?: ExecutiveReport | null
  portfolioMarkdown?: string | null
  chatMessages?: ReportChatMessage[]
}

export interface CaseReportData {
  claimId: string
  generatedAt: string
  scoreFinal: number
  nivelRiesgo: string
  accion: string
  explicacion: string
  rows: ReturnType<typeof buildContributionRows>
  insights: ReturnType<typeof buildChartInsights>
  alertas: string[]
  uploadedFileName?: string | null
  claimsCount: number
  ramo: string
  cobertura: string
  montoReclamado: string
  documentosCompletos: boolean
  dossier?: ClaimDossier | null
  portfolioReport?: ExecutiveReport | null
  portfolioMarkdown?: string | null
  chatSummary: CaseReportChatQa[]
}

export function collectCaseReportData(input: CaseReportExportInput): CaseReportData {
  const { claim, explanation, dossier, graphPayload, claims, uploadedFileName, portfolioReport, portfolioMarkdown, chatMessages } = input
  const scoreFinal = num(explanation?.score_final ?? claim.score_final)
  const nivelRiesgo = explanation?.nivel_riesgo || claim.nivel_riesgo || 'Sin clasificar'
  const explicacion = sanitizeAiText(explanation?.explicacion || claim.explicacion || '')
  const accion = sanitizeAiText(explanation?.accion_sugerida || claim.accion_sugerida || '')

  const rawComponents = explanation?.componentes_score ?? {
    reglas: claim.score_reglas,
    modelo: claim.score_modelo,
    anomalia: claim.score_anomalia,
    nlp: claim.score_nlp,
    grafo: claim.score_grafo,
    categorico: claim.score_categorico,
  }

  const components = {
    score_reglas: rawComponents.reglas ?? claim.score_reglas,
    score_modelo: rawComponents.modelo ?? claim.score_modelo,
    score_anomalia: rawComponents.anomalia ?? claim.score_anomalia,
    score_nlp: rawComponents.nlp ?? claim.score_nlp,
    score_grafo: rawComponents.grafo ?? claim.score_grafo,
    score_categorico: rawComponents.categorico ?? claim.score_categorico,
  }

  const alertasRaw = (explanation?.alertas?.length
    ? explanation.alertas
    : claim.alertas_activadas instanceof Array
      ? claim.alertas_activadas
      : []) as unknown[]

  return {
    claimId: claim.id_siniestro,
    generatedAt: new Date().toLocaleString('es-EC'),
    scoreFinal,
    nivelRiesgo: getRiskLabel(nivelRiesgo),
    accion: accion || 'Revisión humana',
    explicacion,
    rows: buildContributionRows(components),
    insights: buildChartInsights(claim, claims, graphPayload),
    alertas: alertasRaw.map((a) => alertToText(a)),
    uploadedFileName,
    claimsCount: claims.length,
    ramo: claim.ramo ?? 'N/D',
    cobertura: claim.cobertura ?? 'N/D',
    montoReclamado: formatCurrency(claim.monto_reclamado),
    documentosCompletos: yes(claim.documentos_completos),
    dossier,
    portfolioReport,
    portfolioMarkdown,
    chatSummary: buildClaimChatSummary(chatMessages, claim.id_siniestro),
  }
}

export function buildCaseReportMarkdown(input: CaseReportExportInput): string {
  const data = collectCaseReportData(input)

  const lines: string[] = [
    '# Reporte demo — RastroSeguro',
    '',
    `**Caso:** ${data.claimId}`,
    `**Generado:** ${data.generatedAt}`,
    '',
    `## ${UI_COPY.scoreObjective}`,
    '',
    `- Puntaje final: **${Math.round(data.scoreFinal)}/100**`,
    `- Nivel: **${data.nivelRiesgo}**`,
    `- Recomendación: ${data.accion}`,
    '',
    `### ${UI_COPY.contribution}`,
    '',
    `| ${UI_COPY.whatInfluenced} | Valor | ${UI_COPY.weight} | ${UI_COPY.contribution} |`,
    '| --- | --- | --- | --- |',
    ...data.rows.map((r) => `| ${r.label} | ${Math.round(r.value)} | ${r.weightPct}% | ${r.contribution} |`),
    '',
    data.explicacion ? `**Explicación:** ${data.explicacion}` : '',
    '',
    '## Recorrido por etapas',
    '',
    '### Paso 1 — Carga',
    data.uploadedFileName ? `- Archivo cargado: \`${data.uploadedFileName}\`` : '- Cartera activa en el sistema.',
    `- Total casos en sesión: ${data.claimsCount}`,
    '',
    '### Paso 2 — Resumen del caso',
    `- Ramo: ${data.ramo} | Cobertura: ${data.cobertura}`,
    `- Monto reclamado: ${data.montoReclamado}`,
    `- Documentos completos: ${data.documentosCompletos ? 'Sí' : 'Pendiente o incompleto'}`,
    '',
    '### Paso 3 — Resultado y motivos',
    ...(data.alertas.length
      ? data.alertas.slice(0, 5).map((a) => `- ${a}`)
      : ['- Sin alertas principales registradas.']),
    '',
    '### Paso 4 — Conexiones y gráficos',
    `- Red: ${data.insights.graph}`,
    `- Recurrencias: ${data.insights.recurrence}`,
    `- Comparación con la cartera: ${data.insights.spider}`,
    '',
    '## Gráficos explicados',
    '',
    `- **Red del caso:** ${data.insights.graph}`,
    `- **Elementos que se repiten:** ${data.insights.recurrence}`,
    `- **Comparación con la cartera:** ${data.insights.spider}`,
    '',
  ]

  if (data.dossier) {
    lines.push(
      '## Evidencias del expediente',
      '',
      data.dossier.headline || '',
      '',
      ...(data.dossier.evidence?.slice(0, 5).map((e, i) => `${i + 1}. **${e.senal || e.codigo}:** ${e.mensaje || ''} (+${Math.round(num(e.puntos))})`) ?? []),
      '',
      data.dossier.ethical_guardrail || '',
      '',
    )
  }

  if (data.chatSummary.length) {
    lines.push(
      '## Resumen del chat sobre este siniestro',
      '',
      ...data.chatSummary.flatMap((item, i) => [
        `${i + 1}. **Pregunta:** ${item.question}`,
        `   **Respuesta:** ${item.answer}`,
      ]),
      '',
    )
  }

  if (data.portfolioReport?.summary) {
    const s = data.portfolioReport.summary
    lines.push(
      '## Anexo — Portafolio',
      '',
      `- Total siniestros: ${s.total_siniestros}`,
      `- Casos rojos: ${s.casos_rojos} (${s.porcentaje_rojo}%)`,
      `- Monto en casos rojos: ${formatCurrency(s.monto_reclamado_casos_rojos)}`,
      '',
      data.portfolioReport.ethics_note || '',
      '',
    )
  } else if (data.portfolioMarkdown) {
    lines.push('## Anexo — Portafolio', '', data.portfolioMarkdown, '')
  }

  lines.push(
    '---',
    '',
    'Documento generado por RastroSeguro. Este resultado solo apoya la revisión humana y no toma decisiones automáticas.',
  )

  return lines.filter((line, i, arr) => !(line === '' && arr[i - 1] === '')).join('\n')
}

export function downloadCaseReportMarkdown(content: string, claimId: string) {
  const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `reporte-demo-${claimId}.md`
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

export async function downloadCaseReportPdf(input: CaseReportExportInput): Promise<void> {
  const { downloadCaseReportPdfFromData } = await import('@/lib/case-report-pdf')
  const data = collectCaseReportData(input)
  await downloadCaseReportPdfFromData(data)
}

