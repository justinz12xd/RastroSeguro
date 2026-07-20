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
