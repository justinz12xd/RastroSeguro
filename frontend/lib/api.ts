'use client'

import { assignIncrementalSinIds, extractCsvClaimIds } from '@/lib/csv-id-normalizer'

export type FrontendRiskLevel = 'bajo' | 'medio' | 'alto' | 'critico'

export interface ApiEnvelope<T> {
  ok: boolean
  data: T | null
  error: {
    message: string
    hint?: string | null
    details?: unknown
  } | null
}

export interface ClaimSummary {
  id_siniestro: string
  ramo?: string | null
  cobertura?: string | null
  ciudad?: string | null
  id_proveedor?: string | null
  beneficiario?: string | null
  monto_reclamado?: number | null
  suma_asegurada?: number | null
  score_reglas?: number | null
  score_modelo?: number | null
  score_anomalia?: number | null
  score_nlp?: number | null
  score_grafo?: number | null
  score_categorico?: number | null
  score_final?: number | null
  nivel_riesgo?: string | null
  alertas_activadas?: unknown
  explicacion?: string | null
  accion_sugerida?: string | null
  narrativa?: string | null
  descripcion?: string | null
  fecha_ocurrencia?: string | null
  fecha_reporte?: string | null
  dias_desde_inicio_poliza?: number | null
  dias_desde_fin_poliza?: number | null
  dias_entre_ocurrencia_reporte?: number | null
  documentos_completos?: string | boolean | null
  documentos_inconsistentes?: string | boolean | null
}

export interface ClaimExplanation {
  id_siniestro: string
  score_final?: number | null
  nivel_riesgo?: string | null
  alertas?: unknown[]
  explicacion?: string | null
  accion_sugerida?: string | null
  componentes_score?: {
    reglas?: number | null
    modelo?: number | null
    anomalia?: number | null
    nlp?: number | null
    grafo?: number | null
    categorico?: number | null
  }
  detalles_avanzados?: Record<string, unknown>
}


export interface ClaimDossier {
  id_siniestro: string
  headline: string
  risk: {
    score_final?: number | null
    nivel_riesgo?: string | null
    accion_sugerida?: string | null
    decision_automatica?: string | null
    revision_humana_requerida?: string | null
  }
  claim: {
    ramo?: string | null
    cobertura?: string | null
    ciudad?: string | null
    id_asegurado?: string | null
    id_proveedor?: string | null
    beneficiario?: string | null
    monto_reclamado?: number | null
    suma_asegurada?: number | null
    ratio_monto_suma?: number | null
    fecha_ocurrencia?: string | null
    fecha_reporte?: string | null
  }
  evidence: Array<{
    codigo?: string | null
    senal?: string | null
    puntos?: number | null
    severidad?: string | null
    mensaje?: string | null
    evidencia?: Record<string, unknown>
  }>
  score_components: Record<string, number | null | undefined>
  main_driver?: { componente?: string | null; valor?: number | null }
  investigation_summary?: string | null
  timeline?: Array<{
    title: string
    date?: string | null
    detail?: string | null
    tone?: 'neutral' | 'info' | 'success' | 'warning' | 'critical' | string | null
  }>
  signal_radar?: Array<{
    component: string
    score?: number | null
    label?: string | null
    description?: string | null
  }>
  similar_cases_summary?: {
    headline?: string | null
    similar_cases?: Array<{
      id_siniestro?: string | null
      similarity?: number | null
      reason?: string | null
    }>
    recurring_entities?: Array<{
      entity?: string | null
      type?: string | null
      count?: number | null
    }>
    connections_count?: number | null
  }
  executive_takeaway?: string | null
  advanced_evidence?: {
    nlp?: { explicacion?: string | null; similares?: unknown[] }
    grafo?: { explicacion?: string | null; conexiones?: unknown[]; entidades_recurrentes?: unknown[] }
  }
  recommended_review: string[]
  ethical_guardrail: string
  explanation?: string | null
}

export interface StarCase {
  tipo: string
  id_siniestro: string
  nivel_riesgo?: string | null
  score_final?: number | null
  ramo?: string | null
  ciudad?: string | null
  id_proveedor?: string | null
  monto_reclamado?: number | null
  por_que_destaca: string
  explicacion_demo?: string | null
}

export interface StarCasesResponse {
  count: number
  cases: StarCase[]
}

export interface BusinessImpact {
  total_siniestros: number
  casos_rojos: number
  casos_a_revisar_top_percent: number
  porcentaje_revision: number
  monto_total_reclamado: number
  monto_en_casos_rojos: number
  monto_priorizado_top_percent: number
  mensaje: string
}

export interface AgentResponse {
  ok?: boolean
  intent?: string
  message?: string
  data?: unknown
  source?: string
  metadata?: unknown
  llm?: Record<string, unknown>
  runtime?: Record<string, unknown>
  context?: Record<string, unknown>
}

export interface ExtractedClaimDraft {
  id_siniestro?: string | null
  id_poliza?: string | null
  id_asegurado?: string | null
  ramo?: string | null
  cobertura?: string | null
  fecha_ocurrencia?: string | null
  fecha_reporte?: string | null
  monto_reclamado?: number | string | null
  monto_estimado?: number | string | null
  suma_asegurada?: number | string | null
  estado?: string | null
  sucursal?: string | null
  ciudad?: string | null
  descripcion?: string | null
  documentos_completos?: boolean | string | null
  beneficiario?: string | null
  id_proveedor?: string | null
  [key: string]: string | number | boolean | null | undefined
}

export interface FieldEvidence {
  field: string
  value?: string | number | boolean | null
  page?: number | null
  source_text?: string | null
  confidence?: number | null
  inferred?: boolean | null
  agent?: string | null
  method?: string | null
}

export interface ExtractionQuality {
  score: number
  verdict: 'confiable' | 'requiere_revision' | 'baja_confianza' | string
  critical_fields_present: number
  critical_fields_total: number
  fields_present: number
  fields_expected: number
  evidence_coverage: number
  completeness: number
  consistency_score: number
  security_score: number
  average_field_confidence: number
  messages: string[]
}

export interface DocumentProfile {
  document_type: string
  text_chars?: number
  line_count?: number
  has_text_layer?: boolean
  has_table_headers?: boolean
  has_split_column_blocks?: boolean
  requires_ocr?: boolean
  methods_attempted?: string[]
}

export interface ExtractedClaimCandidate {
  row_index: number
  label: string
  claim: ExtractedClaimDraft
  field_evidence: FieldEvidence[]
  confidence: number
  method?: string | null
  quality?: ExtractionQuality
}

export interface SecurityFinding {
  code?: string | null
  severity?: string | null
  message: string
}

export interface ConsistencyFinding {
  field?: string | null
  severity?: string | null
  message: string
}

export interface DocumentExtractionReview {
  document_id: string
  filename: string
  file_type: 'pdf' | 'txt' | string
  document_profile?: DocumentProfile | null
  preview_base64?: string | null
  preview_url?: string | null
  extracted_claim: ExtractedClaimDraft
  field_evidence: FieldEvidence[]
  candidate_claims?: ExtractedClaimCandidate[]
  security_findings: SecurityFinding[]
  consistency_findings: ConsistencyFinding[]
  overall_confidence: number
  extraction_quality?: ExtractionQuality | null
  requires_human_review: boolean
  pipeline_agents?: Array<{ name: string; status: string; detail?: string | null }>
}

export interface UploadResult {
  uploaded: boolean
  filename?: string | null
  rows_processed?: number
  selected_claim_id?: string | null
  uploaded_claim_ids?: string[]
  scored_output_path?: string
}

export class ApiClientError extends Error {
  hint?: string | null
  details?: unknown
  status?: number

  constructor(message: string, options: { hint?: string | null; details?: unknown; status?: number } = {}) {
    super(message)
    this.name = 'ApiClientError'
    this.hint = options.hint
    this.details = options.details
    this.status = options.status
  }
}

const API_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '')

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        ...(init?.headers ?? {}),
      },
    })
  } catch {
    throw new ApiClientError('No se pudo conectar con el API de RastroSeguro.', {
      hint: 'Verifica que FastAPI esté activo en http://localhost:8000.',
    })
  }

  const payload = (await response.json().catch(() => null)) as ApiEnvelope<T> | null
  if (!payload) {
    throw new ApiClientError('El API respondió con un formato inválido.', { status: response.status })
  }
  if (!response.ok || !payload.ok) {
    throw new ApiClientError(payload.error?.message || 'El API no pudo completar la solicitud.', {
      hint: payload.error?.hint,
      details: payload.error?.details,
      status: response.status,
    })
  }
  return payload.data as T
}

export function getHealth() {
  return apiRequest<{ service: string; status: string }>('/api/health')
}

export function getClaims(limit = 50) {
  return apiRequest<ClaimSummary[]>(`/api/claims?limit=${limit}`)
}

export function getClaimExplanation(idSiniestro: string) {
  return apiRequest<ClaimExplanation>(`/api/claims/${encodeURIComponent(idSiniestro)}/explanation`)
}

export function getQuickQuestions(userRole: 'analyst' | 'executive' = 'analyst') {
  return apiRequest<string[]>(`/api/agent/quick-questions?user_role=${encodeURIComponent(userRole)}`)
}

export interface ChatTurn {
  role: 'user' | 'assistant'
  content: string
}

export interface AgentChatMessage {
  id: string
  section_id?: string | null
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  intent?: string | null
  source?: string | null
  metadata?: Record<string, unknown>
  data?: unknown
}

export interface AgentChatSection {
  section_id: string
  thread_id: string
  user_id: string
  title: string
  kind: string
  created_at: string
  updated_at: string
  message_count: number
  metadata?: Record<string, unknown>
}

export interface AgentChatSessionSummary {
  thread_id: string
  user_id: string
  title: string
  created_at: string
  updated_at: string
  selected_claim_id?: string | null
  last_claim_id?: string | null
  last_intent?: string | null
  runtime?: string | null
  message_count: number
}

export interface AgentChatThread {
  thread_id: string
  user_id: string
  title: string
  history: AgentChatMessage[]
  sections: AgentChatSection[]
  context: {
    selected_claim_id?: string | null
    last_claim_id?: string | null
    last_intent?: string | null
    current_section_id?: string | null
    runtime?: string | null
    state?: Record<string, unknown>
  }
  created_at: string
  updated_at: string
}

export interface AgentChatSession extends AgentChatThread {
  reply: AgentResponse
}

export function askAgent(
  question: string,
  history?: ChatTurn[],
  userRole: 'analyst' | 'executive' = 'analyst',
  selectedClaimId?: string | null,
) {
  return apiRequest<AgentResponse>('/api/agent/ask', {
    method: 'POST',
    body: JSON.stringify(
      history && history.length
        ? { question, history, user_role: userRole, selected_claim_id: selectedClaimId || null }
        : { question, user_role: userRole, selected_claim_id: selectedClaimId || null },
    ),
  })
}

export function getAgentThread(threadId: string, userId = 'anonymous') {
  return apiRequest<AgentChatThread>(
    `/api/agent/threads/${encodeURIComponent(threadId)}?user_id=${encodeURIComponent(userId)}`,
  )
}

export function getAgentSessions(userId = 'anonymous', limit = 25) {
  return apiRequest<AgentChatSessionSummary[]>(
    `/api/agent/sessions?user_id=${encodeURIComponent(userId)}&limit=${limit}`,
  )
}

export function chatAgent(payload: {
  message: string
  userId?: string | null
  threadId?: string | null
  selectedClaimId?: string | null
  runtime?: 'classic' | 'langgraph'
  userRole?: 'analyst' | 'executive' | null
  uiContext?: { step?: number; step_title?: string } | null
}) {
  return apiRequest<AgentChatSession>('/api/agent/chat', {
    method: 'POST',
    body: JSON.stringify({
      message: payload.message,
      user_id: payload.userId || 'anonymous',
      thread_id: payload.threadId || null,
      selected_claim_id: payload.selectedClaimId || null,
      runtime: payload.runtime || 'langgraph',
      user_role: payload.userRole || 'analyst',
      ui_context: payload.uiContext || null,
    }),
  })
}

export async function uploadClaimsCsv(file: File) {
  const normalizedFile = await assignIncrementalSinIds(file)
  const uploadedClaimIds = await extractCsvClaimIds(normalizedFile)
  const form = new FormData()
  form.append('file', normalizedFile)

  let response: Response
  try {
    response = await fetch(`${API_URL}/api/claims/upload-csv`, {
      method: 'POST',
      body: form,
    })
  } catch {
    throw new ApiClientError('No se pudo conectar con el API de RastroSeguro.', {
      hint: 'Verifica que FastAPI esté activo en http://localhost:8000.',
    })
  }

  const payload = (await response.json().catch(() => null)) as ApiEnvelope<{
    uploaded: boolean
    filename?: string
    rows_processed?: number
    scored_output_path?: string
  }> | null

  if (!payload) {
    throw new ApiClientError('El API respondió con un formato inválido.', { status: response.status })
  }
  if (!response.ok || !payload.ok) {
    throw new ApiClientError(payload.error?.message || 'No se pudo procesar el archivo de datos.', {
      hint: payload.error?.hint,
      details: payload.error?.details,
      status: response.status,
    })
  }
  return { ...payload.data, uploaded_claim_ids: uploadedClaimIds }
}

async function multipartRequest<T>(path: string, file: File, fallbackMessage: string): Promise<T> {
  const form = new FormData()
  form.append('file', file)

  let response: Response
  try {
    response = await fetch(`${API_URL}${path}`, {
      method: 'POST',
      body: form,
    })
  } catch {
    throw new ApiClientError('No se pudo conectar con el API de RastroSeguro.', {
      hint: 'Verifica que FastAPI esté activo en http://localhost:8000.',
    })
  }

  const payload = (await response.json().catch(() => null)) as ApiEnvelope<T> | null
  if (!payload) throw new ApiClientError('El API respondió con un formato inválido.', { status: response.status })
  if (!response.ok || !payload.ok) {
    throw new ApiClientError(payload.error?.message || fallbackMessage, {
      hint: payload.error?.hint,
      details: payload.error?.details,
      status: response.status,
    })
  }
  return payload.data as T
}

export function extractClaimDocument(file: File) {
  return multipartRequest<DocumentExtractionReview>('/api/claims/extract-document', file, 'No se pudo extraer el documento.')
}

export function confirmExtractedClaim(payload: {
  document_id?: string | null
  filename?: string | null
  claim: ExtractedClaimDraft
}) {
  return apiRequest<UploadResult>('/api/claims/confirm-extracted-document', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function toFrontendRiskLevel(level?: string | null): FrontendRiskLevel {
  const normalized = String(level || '').trim().toLowerCase()
  if (['verde', 'bajo', 'low'].includes(normalized)) return 'bajo'
  if (['amarillo', 'medio', 'medium'].includes(normalized)) return 'medio'
  if (['alto', 'high'].includes(normalized)) return 'alto'
  if (['rojo', 'critico', 'crítico', 'critical'].includes(normalized)) return 'critico'
  return 'medio'
}

export function alertToText(alert: unknown): string {
  if (typeof alert === 'string') return alert
  if (alert && typeof alert === 'object') {
    const item = alert as Record<string, unknown>
    return String(item.message || item.name || item.code || 'Alerta de riesgo activada')
  }
  return 'Alerta de riesgo activada'
}

export interface RiskAggregateRow {
  name?: string
  id_proveedor?: string
  ramo?: string
  ciudad?: string
  total_siniestros: number
  casos_rojos?: number
  score_promedio: number
}

export interface ExecutiveReport {
  generated_at: string
  summary: {
    total_siniestros: number
    casos_verdes: number
    casos_amarillos: number
    casos_rojos: number
    porcentaje_rojo: number
    mix_riesgo_pct: Record<string, number>
    monto_total_reclamado: number
    monto_reclamado_casos_rojos: number
    score_promedio_portafolio?: number
  }
  top_casos: ClaimSummary[]
  riesgo_por_ramo: RiskAggregateRow[]
  top_proveedores: RiskAggregateRow[]
  top_ciudades: RiskAggregateRow[]
  ethics_note: string
  ahorro_potencial_estimado?: SavingsEstimate
}

export interface SavingsEstimate {
  casos_rojos: number
  monto_expuesto_rojos: number
  tasa_prevencion_asumida: number
  ahorro_potencial_estimado: number
  desglose_por_ramo?: Array<{ ramo: string; monto_expuesto: number; ahorro_estimado: number }>
  nota_etica?: string
}

export interface SimulationResponse extends ClaimExplanation {
  ok?: boolean
  simulated?: boolean
  source?: string
  input_normalizado?: Record<string, unknown>
  risk?: {
    score_final?: number | null
    nivel_riesgo?: string | null
    accion_sugerida?: string | null
  }
  signals?: Record<string, unknown>
  ui?: {
    priority_badge?: string
    summary_cards?: Array<{ label: string; value: unknown }>
    recommended_next_steps?: string[]
  }
  context?: Record<string, unknown>
}

export function getProviderRiskRanking(limit = 10) {
  return apiRequest<RiskAggregateRow[]>(`/api/rankings/providers?limit=${limit}`)
}

export function getCityRiskDistribution() {
  return apiRequest<RiskAggregateRow[]>('/api/risk/cities')
}

export function getBranchRiskDistribution() {
  return apiRequest<RiskAggregateRow[]>('/api/risk/branches')
}

export function getExecutiveReport(topLimit = 10) {
  return apiRequest<ExecutiveReport>(`/api/report?format=dict&top_limit=${topLimit}`)
}

export function getExecutiveReportMarkdown(topLimit = 10) {
  return apiRequest<{ format: string; content: string }>(`/api/report?format=markdown&top_limit=${topLimit}`)
}

export function getSavingsEstimate() {
  return apiRequest<SavingsEstimate>('/api/report/savings')
}

export function simulateClaim(claimData: Record<string, unknown>) {
  return apiRequest<SimulationResponse>('/api/simulator/claim', {
    method: 'POST',
    body: JSON.stringify(claimData),
  })
}


export function getClaimDossier(idSiniestro: string) {
  return apiRequest<ClaimDossier>(`/api/claims/${encodeURIComponent(idSiniestro)}/dossier`)
}

export function getStarCases() {
  return apiRequest<StarCasesResponse>('/api/reports/star-cases')
}

export function getBusinessImpact(reviewPercent = 0.1) {
  return apiRequest<BusinessImpact>(`/api/reports/business-impact?review_percent=${reviewPercent}`)
}

export interface FraudRingSharedEntity {
  type: string
  value: string
  key: string
  siniestros_vinculados: number
  siniestros_relacionados: string[]
}

export interface FraudRingClaimSummary {
  id_siniestro: string
  ramo?: string | null
  nivel_riesgo?: string | null
  score_final?: number | null
  monto_reclamado?: number | null
  id_proveedor?: string | null
  beneficiario?: string | null
}

export interface FraudRing {
  id_anillo: string
  siniestros: string[]
  tamano: number
  casos_rojos: number
  pct_rojos: number
  monto_expuesto: number
  score_promedio: number
  ring_risk_score: number
  entidades_compartidas: FraudRingSharedEntity[]
  explicacion: string
  claims_resumen: FraudRingClaimSummary[]
}

export interface FraudRingsResponse {
  total_anillos: number
  anillos: FraudRing[]
  explicacion_global: string
}

export function getFraudRings(limit = 10) {
  return apiRequest<FraudRingsResponse>(`/api/graph/fraud-rings?limit=${limit}`)
}
