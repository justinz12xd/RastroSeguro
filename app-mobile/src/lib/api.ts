import { Platform } from 'react-native'

export interface ClaimSummary {
  id_siniestro: string
  ramo?: string | null
  ciudad?: string | null
  id_proveedor?: string | null
  monto_reclamado?: number | null
  score_final?: number | null
  nivel_riesgo?: string | null
  alertas_activadas?: unknown
  accion_sugerida?: string | null
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

export interface SavingsEstimate {
  casos_rojos: number
  monto_expuesto_rojos: number
  tasa_prevencion_asumida: number
  ahorro_potencial_estimado: number
  nota_etica?: string
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

interface ApiEnvelope<T> {
  ok: boolean
  data?: T
  error?: { message?: string; hint?: string; details?: unknown }
}

export class ApiClientError extends Error {
  hint?: string | null
  status?: number

  constructor(message: string, options: { hint?: string | null; status?: number } = {}) {
    super(message)
    this.name = 'ApiClientError'
    this.hint = options.hint
    this.status = options.status
  }
}

/**
 * Android emulator maps host loopback to 10.0.2.2.
 * Physical device: set EXPO_PUBLIC_API_URL to your LAN IP (e.g. http://192.168.x.x:8000).
 */
function resolveDefaultApiUrl(): string {
  const fromEnv = process.env.EXPO_PUBLIC_API_URL
  if (fromEnv) return fromEnv.replace(/\/$/, '')
  if (Platform.OS === 'android') return 'http://10.0.2.2:8000'
  return 'http://localhost:8000'
}

const API_URL = resolveDefaultApiUrl()

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
      hint: `Verifica que FastAPI esté activo en ${API_URL}. En dispositivo físico usa EXPO_PUBLIC_API_URL con la IP de tu PC.`,
    })
  }

  const payload = (await response.json().catch(() => null)) as ApiEnvelope<T> | null
  if (!payload) {
    throw new ApiClientError('El API respondió con un formato inválido.', { status: response.status })
  }
  if (!response.ok || !payload.ok) {
    throw new ApiClientError(payload.error?.message || 'El API no pudo completar la solicitud.', {
      hint: payload.error?.hint,
      status: response.status,
    })
  }
  return payload.data as T
}

export function getApiBaseUrl() {
  return API_URL
}

export function getHealth() {
  return apiRequest<{ service: string; status: string }>('/api/health')
}

export function getExecutiveReport(topLimit = 10) {
  return apiRequest<ExecutiveReport>(`/api/report?format=dict&top_limit=${topLimit}`)
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
  }>
  score_components: Record<string, number | null | undefined>
  main_driver?: { componente?: string | null; valor?: number | null }
  investigation_summary?: string | null
  executive_takeaway?: string | null
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

export function getClaimDossier(idSiniestro: string) {
  return apiRequest<ClaimDossier>(`/api/claims/${encodeURIComponent(idSiniestro)}/dossier`)
}

export function getStarCases() {
  return apiRequest<StarCasesResponse>('/api/reports/star-cases')
}

export function getBusinessImpact(reviewPercent = 0.1) {
  return apiRequest<BusinessImpact>(`/api/reports/business-impact?review_percent=${reviewPercent}`)
}
