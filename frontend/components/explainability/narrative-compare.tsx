'use client'

import { Fragment, useMemo, useState } from 'react'
import { cn } from '@/lib/utils'
import { FileText, GitCompareArrows } from 'lucide-react'

export interface SimilarMatch {
  target_id: string
  similarity: number
}

const STOPWORDS = new Set([
  'para', 'pero', 'como', 'este', 'esta', 'esto', 'esos', 'esas', 'unos', 'unas', 'desde', 'sobre', 'entre',
  'cuando', 'donde', 'porque', 'segun', 'segund', 'tras', 'hacia', 'hasta', 'con', 'sin', 'los', 'las', 'una',
  'del', 'que', 'por', 'una', 'sus', 'fue', 'han', 'hay', 'mas',
])

function normalizeToken(token: string): string {
  return token
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]/g, '')
}

function tokenSet(text: string): Set<string> {
  const set = new Set<string>()
  for (const raw of text.split(/\s+/)) {
    const t = normalizeToken(raw)
    if (t.length >= 4 && !STOPWORDS.has(t)) set.add(t)
  }
  return set
}

function HighlightedText({ text, shared }: { text: string; shared: Set<string> }) {
  const parts = text.split(/(\s+)/)
  return (
    <p className="text-sm leading-relaxed text-foreground/90">
      {parts.map((part, i) => {
        const norm = normalizeToken(part)
        if (norm.length >= 4 && shared.has(norm)) {
          return (
            <mark key={i} className="rounded bg-[var(--risk-amarillo)]/30 px-0.5 text-foreground">
              {part}
            </mark>
          )
        }
        return <Fragment key={i}>{part}</Fragment>
      })}
    </p>
  )
}

interface NarrativeCompareProps {
  currentId: string
  currentNarrative: string
  matches: SimilarMatch[]
  lookupNarrative: (id: string) => string | undefined
}

export function NarrativeCompare({ currentId, currentNarrative, matches, lookupNarrative }: NarrativeCompareProps) {
  const ranked = useMemo(
    () => [...matches].filter((m) => m.target_id).sort((a, b) => b.similarity - a.similarity).slice(0, 5),
    [matches],
  )
  const [selectedId, setSelectedId] = useState(ranked[0]?.target_id ?? '')

  const active = ranked.find((m) => m.target_id === selectedId) ?? ranked[0]
  const targetNarrative = active ? lookupNarrative(active.target_id) : undefined

  const shared = useMemo(() => {
    if (!targetNarrative) return new Set<string>()
    const a = tokenSet(currentNarrative)
    const b = tokenSet(targetNarrative)
    const inter = new Set<string>()
    for (const t of a) if (b.has(t)) inter.add(t)
    return inter
  }, [currentNarrative, targetNarrative])

  if (!ranked.length) return null

  return (
    <div className="space-y-4">
      <div className="flex flex-col justify-between gap-3 md:flex-row md:items-end">
        <div>
          <h2 className="flex items-center gap-2 label-mono-md font-bold uppercase">
            <GitCompareArrows className="h-4 w-4" />
            Comparador de narrativas
          </h2>
          <p className="text-sm text-muted-foreground">
            Resaltamos los términos compartidos. La similitud textual alimenta la regla RF-07 (narrativa clonada).
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {ranked.map((m) => (
            <button
              key={m.target_id}
              type="button"
              onClick={() => setSelectedId(m.target_id)}
              className={cn(
                'focus-ring rounded-full border px-3 py-1.5 label-mono text-xs transition-colors',
                m.target_id === active?.target_id
                  ? 'border-primary bg-[var(--secondary-container)] text-[var(--on-secondary-container)]'
                  : 'border-border bg-[var(--surface-low)] text-muted-foreground hover:border-primary',
              )}
            >
              {m.target_id} · {Math.round(m.similarity * 100)}%
            </button>
          ))}
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-lg border border-border bg-[var(--surface-low)] p-4">
          <div className="mb-2 flex items-center justify-between">
            <span className="flex items-center gap-1.5 label-mono text-xs text-muted-foreground">
              <FileText className="h-3.5 w-3.5" /> Caso actual
            </span>
            <span className="label-mono text-xs text-foreground">{currentId}</span>
          </div>
          <HighlightedText text={currentNarrative || 'Sin narrativa disponible para este caso.'} shared={shared} />
        </div>

        <div className="rounded-lg border border-border bg-[var(--surface-low)] p-4">
          <div className="mb-2 flex items-center justify-between">
            <span className="flex items-center gap-1.5 label-mono text-xs text-muted-foreground">
              <FileText className="h-3.5 w-3.5" /> Caso similar
            </span>
            <span className="label-mono text-xs text-foreground">{active?.target_id}</span>
          </div>
          {targetNarrative ? (
            <HighlightedText text={targetNarrative} shared={shared} />
          ) : (
            <p className="text-sm text-muted-foreground">
              La narrativa de {active?.target_id} no está en el lote cargado. Similitud detectada por el motor:{' '}
              <span className="font-semibold text-foreground">{Math.round((active?.similarity ?? 0) * 100)}%</span>.
            </p>
          )}
        </div>
      </div>

      {targetNarrative && (
        <p className="flex items-center gap-2 text-xs text-muted-foreground">
          <span className="inline-block h-3 w-3 rounded bg-[var(--risk-amarillo)]/30" />
          {shared.size} términos compartidos · similitud del motor {Math.round((active?.similarity ?? 0) * 100)}%.
        </p>
      )}
    </div>
  )
}
