'use client'

import { useEffect, useReducer, useRef } from 'react'
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'
import { CheckCircle2, FileText, Info, Loader2, ShieldAlert } from 'lucide-react'
import { useIsMobile } from '@/hooks/use-mobile'

// Strong ease-out curve per Emil Kowalski's design engineering principles
const EASE_OUT: [number, number, number, number] = [0.23, 1, 0.32, 1]

// ─── types ───────────────────────────────────────────────────────────────────

type Phase = 'receiving' | 'analyzing' | 'result' | 'pause'

interface State {
  phase: Phase
  bar: number        // 0-100 upload bar
  signals: number[]  // 0-100 each of 4 signal bars
  count: number      // animated score counter
}

type Action =
  | { type: 'SET_PHASE'; phase: Phase }
  | { type: 'SET_BAR'; bar: number }
  | { type: 'SET_SIGNALS'; signals: number[] }
  | { type: 'SET_COUNT'; count: number }
  | { type: 'RESET' }

// ─── constants ───────────────────────────────────────────────────────────────

const SIGNAL_TARGETS = [92, 81, 76, 88]
const SIGNAL_LABELS  = ['Reglas de negocio', 'Patrones del modelo', 'Narrativa similar', 'Red de relaciones']
const SCORE_TARGET   = 87
const REASONS        = ['Narrativa similar', 'Proveedor recurrente', 'Monto sensible']

const PHASE_DURATIONS: Record<Phase, number> = {
  receiving: 2600,
  analyzing: 3200,
  result:    4000,
  pause:     2000,
}

// ─── reducer ─────────────────────────────────────────────────────────────────

function init(): State {
  return { phase: 'receiving', bar: 0, signals: [0, 0, 0, 0], count: 0 }
}

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'SET_PHASE':   return { ...state, phase: action.phase }
    case 'SET_BAR':     return { ...state, bar: action.bar }
    case 'SET_SIGNALS': return { ...state, signals: action.signals }
    case 'SET_COUNT':   return { ...state, count: action.count }
    case 'RESET':       return init()
    default:            return state
  }
}

// ─── helpers ─────────────────────────────────────────────────────────────────

function useAnimFrame(cb: (elapsed: number) => void, active: boolean) {
  const cbRef  = useRef(cb)
  const rafRef = useRef<number>(0)
  const startRef = useRef<number | null>(null)

  cbRef.current = cb

  useEffect(() => {
    if (!active) {
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
      startRef.current = null
      return
    }
    startRef.current = null
    const loop = (ts: number) => {
      if (startRef.current === null) startRef.current = ts
      cbRef.current(ts - startRef.current)
      rafRef.current = requestAnimationFrame(loop)
    }
    rafRef.current = requestAnimationFrame(loop)
    return () => cancelAnimationFrame(rafRef.current)
  }, [active])
}

// ─── component ───────────────────────────────────────────────────────────────

export function LiveDemo() {
  const prefersReduced = useReducedMotion()
  const isMobile = useIsMobile()
  const shouldReduceMotion = prefersReduced && !isMobile
  const [state, dispatch] = useReducer(reducer, undefined, init)
  const phaseRef = useRef<Phase>('receiving')

  // When reduced motion: always show result, no loop.
  useEffect(() => {
    if (shouldReduceMotion) {
      dispatch({ type: 'SET_PHASE', phase: 'result' })
      dispatch({ type: 'SET_SIGNALS', signals: SIGNAL_TARGETS })
      dispatch({ type: 'SET_COUNT', count: SCORE_TARGET })
      dispatch({ type: 'SET_BAR', bar: 100 })
    }
  }, [shouldReduceMotion])

  // Phase scheduler (not reduced motion)
  useEffect(() => {
    if (shouldReduceMotion) return

    phaseRef.current = state.phase
    const duration = PHASE_DURATIONS[state.phase]
    const next: Record<Phase, Phase> = {
      receiving: 'analyzing',
      analyzing: 'result',
      result:    'pause',
      pause:     'receiving',
    }

    const id = setTimeout(() => {
      const nextPhase = next[phaseRef.current]
      if (nextPhase === 'receiving') {
        dispatch({ type: 'RESET' })
      } else {
        dispatch({ type: 'SET_PHASE', phase: nextPhase })
      }
    }, duration)

    return () => clearTimeout(id)
  }, [state.phase, shouldReduceMotion])

  // Upload bar animation (receiving phase)
  useAnimFrame((elapsed) => {
    const progress = Math.min(elapsed / PHASE_DURATIONS.receiving, 1)
    // ease-out cubic
    const eased = 1 - Math.pow(1 - progress, 3)
    dispatch({ type: 'SET_BAR', bar: Math.round(eased * 100) })
  }, !shouldReduceMotion && state.phase === 'receiving')

  // Signal bars animation (analyzing phase)
  useAnimFrame((elapsed) => {
    const progress = Math.min(elapsed / PHASE_DURATIONS.analyzing, 1)
    const eased = 1 - Math.pow(1 - progress, 2)
    const stagger = 0.18
    const filled = SIGNAL_TARGETS.map((target, i) => {
      const localProgress = Math.min(Math.max((eased - i * stagger) / (1 - (SIGNAL_TARGETS.length - 1) * stagger), 0), 1)
      return Math.round(localProgress * target)
    })
    dispatch({ type: 'SET_SIGNALS', signals: filled })
  }, !shouldReduceMotion && state.phase === 'analyzing')

  // Count-up animation for the risk score (result phase)
  useAnimFrame((elapsed) => {
    const progress = Math.min(elapsed / (PHASE_DURATIONS.result * 0.45), 1)
    const eased = 1 - Math.pow(1 - progress, 2)
    dispatch({ type: 'SET_COUNT', count: Math.round(eased * SCORE_TARGET) })
  }, !shouldReduceMotion && state.phase === 'result')

  const { phase, bar, signals, count } = state

  return (
    <div
      className="landing-product-shot landing-spotlight institutional-card relative overflow-hidden"
      aria-label="Demostración del proceso de análisis de siniestros"
      aria-live="polite"
    >
      {/* Header */}
      <div className="landing-shot-header section-header flex items-center justify-between">
        <span className="flex items-center gap-2">
          <ShieldAlert className="h-4 w-4" aria-hidden />
          RastroSeguro — Análisis en vivo
        </span>
        <span className="label-mono landing-tabular">SIN-045</span>
      </div>

      <div className="min-h-[320px] space-y-4 p-5">
        {/* ── Phase: receiving ── */}
        <AnimatePresence mode="wait">
          {phase === 'receiving' && (
            <motion.div
              key="receiving"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.28, ease: EASE_OUT }}
              className="space-y-4"
            >
              <div className="landing-shot-tile flex items-center gap-3 p-4">
                <FileText className="h-8 w-8 shrink-0 text-primary" aria-hidden />
                <div className="min-w-0 flex-1">
                  <p className="landing-shot-label label-mono">Recibiendo expediente</p>
                  <p className="font-display text-base font-semibold landing-shot-value">expediente-SIN-045.csv</p>
                </div>
                <Loader2 className="landing-demo-spin h-5 w-5 shrink-0 text-primary" aria-hidden />
              </div>

              <div>
                <div className="mb-1.5 flex items-center justify-between">
                  <span className="landing-shot-label label-mono-md">Procesando archivo</span>
                  <span className="landing-shot-value label-mono-md landing-tabular">{bar}%</span>
                </div>
                <div className="landing-shot-bar h-2.5 overflow-hidden rounded-full">
                  <div
                    className="landing-shot-bar-fill h-full w-full rounded-full"
                    style={{
                      transform: `scaleX(${bar / 100})`,
                      transformOrigin: 'left',
                      transition: 'transform 80ms linear',
                    }}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                {['Proveedor', 'Monto reclamado', 'Ciudad', 'Fecha'].map((label) => (
                  <div key={label} className="landing-shot-tile p-3">
                    <p className="landing-shot-label label-mono text-xs">{label}</p>
                    <div className="landing-demo-pulse landing-shot-skeleton mt-1 h-3 w-3/4 rounded" />
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {/* ── Phase: analyzing ── */}
          {phase === 'analyzing' && (
            <motion.div
              key="analyzing"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.28, ease: EASE_OUT }}
              className="space-y-4"
            >
              <div className="landing-shot-tile flex items-center gap-3 p-4">
                <Loader2 className="landing-demo-spin h-6 w-6 shrink-0 text-primary" aria-hidden />
                <div>
                  <p className="landing-shot-label label-mono">Analizando señales del caso</p>
                  <p className="font-display text-base font-semibold landing-shot-value">Cruzando patrones y relaciones...</p>
                </div>
              </div>

              <div className="space-y-3">
                {SIGNAL_LABELS.map((label, i) => (
                  <div key={label}>
                    <div className="mb-1 flex items-center justify-between">
                      <span className="landing-shot-label label-mono-md">{label}</span>
                      <span className="landing-shot-value label-mono-md landing-tabular">{signals[i]}</span>
                    </div>
                    <div className="landing-shot-bar h-2 overflow-hidden">
                      <div
                        className="landing-shot-bar-fill h-full w-full"
                        style={{
                          transform: `scaleX(${signals[i] / 100})`,
                          transformOrigin: 'left',
                          transition: 'transform 60ms linear',
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {/* ── Phase: result ── */}
          {(phase === 'result' || phase === 'pause') && (
            <motion.div
              key="result"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.32, ease: EASE_OUT }}
              className="space-y-4"
            >
              <div className="grid gap-3 sm:grid-cols-3">
                <div className="landing-shot-tile p-3">
                  <p className="landing-shot-label label-mono">Puntaje de riesgo</p>
                  <p className="landing-metric-value landing-tabular landing-shot-value">{count}</p>
                </div>
                <div className="landing-shot-tile p-3">
                  <p className="landing-shot-label label-mono">Nivel</p>
                  <p className="landing-shot-danger font-display text-3xl font-semibold">Alto</p>
                </div>
                <div className="landing-shot-tile p-3">
                  <p className="landing-shot-label label-mono">Acción sugerida</p>
                  <p className="font-display text-base font-semibold landing-shot-value leading-tight">Revisar evidencia</p>
                </div>
              </div>

              <div className="space-y-2">
                {SIGNAL_LABELS.map((label, i) => (
                  <div key={label}>
                    <div className="mb-1 flex items-center justify-between">
                      <span className="landing-shot-label label-mono-md">{label}</span>
                      <span className="landing-shot-value label-mono-md landing-tabular">{SIGNAL_TARGETS[i]}</span>
                    </div>
                    <div className="landing-shot-bar h-2 overflow-hidden">
                      <div
                        className="landing-shot-bar-fill h-full w-full"
                        style={{
                          transform: `scaleX(${SIGNAL_TARGETS[i] / 100})`,
                          transformOrigin: 'left',
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>

              <div className="landing-evidence-grid grid gap-2 sm:grid-cols-3">
                {REASONS.map((reason) => (
                  <div
                    key={reason}
                    className="landing-shot-evidence landing-shot-border flex items-center gap-2 border px-3 py-2 label-mono-md"
                  >
                    <CheckCircle2 className="h-3.5 w-3.5 shrink-0" aria-hidden />
                    {reason}
                  </div>
                ))}
              </div>

              <div className="landing-shot-note flex items-start gap-3 rounded border border-[#e2e8f0] p-4 text-sm leading-6">
                <Info className="mt-0.5 h-4 w-4 shrink-0 landing-shot-label" aria-hidden />
                <span>Esta alerta orienta la revisión humana. RastroSeguro no acusa fraude ni decide el reclamo.</span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Phase indicator dots */}
        {!shouldReduceMotion && (
          <div className="flex items-center justify-center gap-2 pt-2" aria-hidden>
            {(['receiving', 'analyzing', 'result'] as Phase[]).map((p) => (
              <span
                key={p}
                className="h-1.5 rounded-full transition-all duration-300"
                style={{
                  width: phase === p || (phase === 'pause' && p === 'result') ? '1.5rem' : '0.375rem',
                  background: phase === p || (phase === 'pause' && p === 'result') ? '#0f172a' : '#cbd5e1',
                }}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
