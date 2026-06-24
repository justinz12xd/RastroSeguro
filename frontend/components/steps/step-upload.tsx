'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import { useAppState } from '@/lib/app-context'
import { ApiClientError, confirmExtractedClaim, extractClaimDocument, type DocumentExtractionReview, type ExtractedClaimDraft, type FieldEvidence } from '@/lib/api'
import { AlertTriangle, CheckCircle2, CloudUpload, FileText, Gavel, History, Loader2, ServerCrash, ShieldCheck, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import { RiskBadge } from '@/components/ui/risk-badge'
import { formatCurrency } from '@/lib/claims-data'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

const REVIEW_FIELDS: Array<{ key: keyof ExtractedClaimDraft; label: string; required?: boolean; type?: 'number' | 'date' | 'textarea' | 'boolean' }> = [
  { key: 'id_siniestro', label: 'ID siniestro', required: true },
  { key: 'id_poliza', label: 'ID póliza' },
  { key: 'id_asegurado', label: 'ID asegurado' },
  { key: 'ramo', label: 'Ramo', required: true },
  { key: 'cobertura', label: 'Cobertura' },
  { key: 'fecha_ocurrencia', label: 'Fecha ocurrencia', required: true, type: 'date' },
  { key: 'fecha_reporte', label: 'Fecha reporte', required: true, type: 'date' },
  { key: 'monto_reclamado', label: 'Monto reclamado', required: true, type: 'number' },
  { key: 'monto_estimado', label: 'Monto estimado', type: 'number' },
  { key: 'suma_asegurada', label: 'Suma asegurada', type: 'number' },
  { key: 'estado', label: 'Estado' },
  { key: 'ciudad', label: 'Ciudad' },
  { key: 'sucursal', label: 'Sucursal' },
  { key: 'id_proveedor', label: 'ID proveedor' },
  { key: 'beneficiario', label: 'Beneficiario' },
  { key: 'documentos_completos', label: 'Documentos completos', type: 'boolean' },
  { key: 'descripcion', label: 'Descripción', type: 'textarea' },
]

const MAX_UPLOAD_MB = 5
const MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

function extensionOf(file: File) {
  return extensionOfName(file.name)
}

function extensionOfName(filename: string) {
  return filename.split('.').pop()?.toLowerCase() || ''
}

function evidenceFor(evidence: FieldEvidence[], field: string) {
  return evidence.find((item) => item.field === field)
}

function formatConfidence(value?: number | null) {
  if (value == null) return 'sin confianza'
  return `${Math.round(value * 100)}% confianza`
}

export function StepUpload() {
  const {
    claims,
    selectedClaimId,
    setCurrentStep,
    setSelectedClaimId,
    setIsDataLoaded,
    uploadedFile,
    setUploadedFile,
    uploadCsvAndRefresh,
    markAnalystSubmittedCases,
    loadClaims,
    isApiReady,
    isLoadingClaims,
    apiError,
    apiHint,
    analystSavedAnalyses,
  } = useAppState()
  const [status, setStatus] = useState<'idle' | 'validating' | 'reviewing' | 'valid'>('idle')
  const [drag, setDrag] = useState(false)
  const [processing, setProcessing] = useState(false)
  const [csvHeaders, setCsvHeaders] = useState<string[]>([])
  const [csvRows, setCsvRows] = useState<string[][]>([])
  const [localError, setLocalError] = useState<string | null>(null)
  const [localHint, setLocalHint] = useState<string | null>(null)
  const [review, setReview] = useState<DocumentExtractionReview | null>(null)
  const [draft, setDraft] = useState<ExtractedClaimDraft>({})
  const [selectedCandidateIndex, setSelectedCandidateIndex] = useState(0)

  // Re-mark the step valid whenever claims are already loaded (uploaded file or
  // demo data) and we're not mid-review. Lets the user return here from step 5
  // to pick another claim without re-uploading.
  useEffect(() => {
    if (claims.length > 0 && !review) setStatus('valid')
  }, [claims.length, review])

  useEffect(() => {
    if (isApiReady || isLoadingClaims || review || claims.length > 0) return
    void loadClaims()
  }, [claims.length, isApiReady, isLoadingClaims, loadClaims, review])

  const buildCsvPreview = async (file: File) => {
    const text = await file.text()
    const lines = text
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean)
      .slice(0, 8)
    if (!lines.length) return
    const splitLine = (line: string) => line.split(',').map((value) => value.trim().replace(/^"|"$/g, ''))
    const headers = splitLine(lines[0]).slice(0, 5)
    const rows = lines.slice(1, 4).map((line) => splitLine(line).slice(0, 5))
    if (headers.length) setCsvHeaders(headers)
    if (rows.length) setCsvRows(rows)
  }

  const selectClaim = (id: string) => {
    setSelectedClaimId(id)
    setStatus('valid')
  }

  // Last analyses closed in this browser (localStorage). Shown here so the user
  // can reopen a previous case's report without re-running the flow.
  const recentAnalyses = useMemo(() => {
    return analystSavedAnalyses.slice(0, 6).map((saved) => ({
      saved,
      claim: claims.find((c) => c.id_siniestro === saved.id) || null,
    }))
  }, [analystSavedAnalyses, claims])

  const reopenAnalysis = (id: string) => {
    setSelectedClaimId(id)
    setIsDataLoaded(true)
    setCurrentStep(5)
  }

  const rememberLocalError = (error: unknown) => {
    if (error instanceof ApiClientError) {
      setLocalError(error.message)
      setLocalHint(error.hint || null)
      return
    }
    setLocalError('No se pudo procesar el documento.')
    setLocalHint(null)
  }

  const resetReview = () => {
    setReview(null)
    setDraft({})
    setSelectedCandidateIndex(0)
  }

  const handleFileUpload = useCallback((files: FileList | null) => {
    const file = files?.[0]
    if (!file) return
    const extension = extensionOf(file)
    setLocalError(null)
    setLocalHint(null)

    // Step 1 is online claim reception, not bulk dataset ingestion. Large files
    // trigger a full-portfolio re-score (O(N²) NLP) that pegs the worker and the
    // platform recycles the container. Reject big files client-side with a clear
    // hint instead of letting the request time out.
    if (file.size > MAX_UPLOAD_BYTES) {
      setLocalError(`El archivo (${Math.round(file.size / (1024 * 1024))} MB) supera el máximo de ${MAX_UPLOAD_MB} MB para evaluación en línea.`)
      setLocalHint('Sube un lote más pequeño. Para el dataset completo usa el pipeline offline.')
      setStatus('idle')
      return
    }

    resetReview()
    setUploadedFile(file)
    setCsvHeaders([])
    setCsvRows([])

    if (extension === 'csv') {
      setStatus('validating')
      void buildCsvPreview(file)
      void uploadCsvAndRefresh(file).then((ok) => {
        setStatus(ok ? 'valid' : 'idle')
      })
      return
    }

    if (extension === 'pdf' || extension === 'txt') {
      setStatus('validating')
      void extractClaimDocument(file)
        .then((payload) => {
          setReview(payload)
          setDraft(payload.extracted_claim || {})
          setSelectedCandidateIndex(0)
          setStatus('reviewing')
        })
        .catch((error) => {
          rememberLocalError(error)
          setStatus('idle')
        })
      return
    }

    setLocalError('Formato no permitido. Sube un archivo de datos, documento PDF o texto.')
    setStatus('idle')
  }, [setUploadedFile, uploadCsvAndRefresh])

  const missingRequired = useMemo(
    () => REVIEW_FIELDS.filter((field) => field.required && !draft[field.key]).map((field) => field.label),
    [draft],
  )

  const updateDraft = (key: keyof ExtractedClaimDraft, value: string | boolean) => {
    setDraft((prev) => ({ ...prev, [key]: value }))
  }

  const selectCandidate = (index: number) => {
    if (!review?.candidate_claims?.[index]) return
    setSelectedCandidateIndex(index)
    setDraft(review.candidate_claims[index].claim || {})
  }

  const selectedCandidate = review?.candidate_claims?.[selectedCandidateIndex]
  const selectedEvidence = selectedCandidate?.field_evidence || review?.field_evidence || []
  const activeQuality = selectedCandidate?.quality || review?.extraction_quality || null

  const handleConfirmExtracted = async () => {
    if (!review || missingRequired.length) return
    setProcessing(true)
    setLocalError(null)
    setLocalHint(null)
    try {
      const result = await confirmExtractedClaim({
        document_id: review.document_id,
        filename: review.filename,
        claim: draft,
      })
      await loadClaims()
      const newId = result?.selected_claim_id || String(draft.id_siniestro || '')
      if (newId) {
        setSelectedClaimId(newId)
        markAnalystSubmittedCases([{
          id: newId,
          source: extensionOfName(review.filename || uploadedFile?.name || '') === 'txt' ? 'txt' : 'pdf',
          filename: review.filename || uploadedFile?.name || null,
        }])
      }
      setUploadedFile(uploadedFile)
      setIsDataLoaded(true)
      resetReview()
      setStatus('valid')
    } catch (error) {
      rememberLocalError(error)
    } finally {
      setProcessing(false)
    }
  }

  const handleNext = () => {
    if (status !== 'valid' || !selectedClaimId) return
    setProcessing(true)
    setIsDataLoaded(true)
    setTimeout(() => {
      setProcessing(false)
      setCurrentStep(2)
    }, 500)
  }

  const handleUseDemo = async () => {
    setProcessing(true)
    setLocalError(null)
    setLocalHint(null)
    try {
      const records = await loadClaims()
      if (!records.length) {
        setStatus('idle')
        setSelectedClaimId(null)
        return
      }
      setSelectedClaimId(records[0].id_siniestro)
      setIsDataLoaded(true)
      setStatus('valid')
    } finally {
      setProcessing(false)
    }
  }

  const clearAll = () => {
    setCsvHeaders([])
    setCsvRows([])
    setUploadedFile(null)
    setStatus('idle')
    setSelectedClaimId(null)
    setLocalError(null)
    setLocalHint(null)
    resetReview()
  }

  const previewHeaders = csvHeaders.length
    ? csvHeaders
    : ['ID_SINIESTRO', 'RAMO', 'CIUDAD', 'PROVEEDOR', 'PUNTAJE']

  const showPreview = csvRows.length > 0
  const isUploading = status === 'validating' || isLoadingClaims
  const uploadComplete = status === 'valid' && uploadedFile && !isUploading
  const effectiveError = localError || apiError
  const effectiveHint = localHint || apiHint
  const systemStatus = isUploading
    ? 'Actualizando datos...'
    : isApiReady
      ? 'Sistema listo'
      : 'API disponible para cargar o usar demo'

  return (
    <section className="px-4 py-8 lg:px-8">
      <Dialog open={!!review} onOpenChange={(open) => { if (!open) { resetReview(); setStatus('idle') } }}>
        <DialogContent
          showCloseButton={false}
          className="flex h-[80vh] max-h-[80vh] w-[calc(100%-1rem)] max-w-[900px] flex-col gap-0 overflow-hidden p-0 sm:max-w-[900px]"
        >
          {review && (<>
            <DialogHeader className="flex flex-row items-start justify-between gap-4 space-y-0 border-b border-border p-5 text-left">
              <div className="min-w-0">
                <p className="label-mono-md uppercase text-primary">Revisión humana obligatoria</p>
                <DialogTitle className="mt-1 truncate font-display text-2xl font-semibold">
                  Documento extraído: {review.filename}
                </DialogTitle>
                <DialogDescription className="mt-1 text-sm text-muted-foreground">
                  Confianza global {formatConfidence(activeQuality?.score ?? review.overall_confidence)} · {activeQuality?.verdict || 'revisión humana'} · confirme antes de pasar al Paso 2.
                </DialogDescription>
              </div>
              <DialogClose className="focus-ring shrink-0 rounded-md border border-border p-2 text-muted-foreground transition-colors hover:text-foreground" aria-label="Cerrar revisión">
                <X className="h-5 w-5" />
              </DialogClose>
            </DialogHeader>

            <div className="grid min-h-0 flex-1 grid-cols-1 overflow-y-auto lg:grid-cols-2 lg:overflow-hidden">
              <div className="flex min-h-0 flex-col border-b border-border bg-[var(--surface-low)] p-4 lg:border-b-0 lg:border-r">
                <div className="mb-3 flex items-center gap-2">
                  <FileText className="h-5 w-5 text-primary" />
                  <h3 className="font-display text-lg font-semibold">Previsualización</h3>
                </div>
                {review.preview_base64 ? (
                  <iframe title="Previsualización del documento" src={review.preview_base64} className="min-h-0 flex-1 rounded-lg border border-border bg-white" />
                ) : (
                  <pre className="min-h-0 flex-1 overflow-auto whitespace-pre-wrap rounded-lg border border-border bg-background p-3 text-sm text-foreground">
                    {(() => {
                      const description = String(draft.descripcion || '')
                      return description || 'Vista previa TXT no disponible.'
                    })()}
                  </pre>
                )}
              </div>

              <div className="min-h-0 space-y-3 p-3 lg:overflow-y-auto">
                <div className="rounded-lg border border-border bg-[var(--surface-low)] p-3">
                  <div className="mb-2 flex items-center justify-between gap-3">
                    <span className="label-mono-md uppercase">Calidad de extracción</span>
                    <span className={cn(
                      'rounded-full px-2 py-1 text-xs font-semibold uppercase',
                      (activeQuality?.score || 0) >= 0.85 ? 'bg-green-100 text-green-800' : (activeQuality?.score || 0) >= 0.65 ? 'bg-amber-100 text-amber-900' : 'bg-red-100 text-red-800',
                    )}>
                      {Math.round((activeQuality?.score || review.overall_confidence || 0) * 100)}%
                    </span>
                  </div>
                  <div className="grid gap-2 text-xs text-muted-foreground sm:grid-cols-3">
                    <div><b className="text-foreground">Tipo:</b> {review.document_profile?.document_type || 'no clasificado'}</div>
                    <div><b className="text-foreground">Críticos:</b> {activeQuality?.critical_fields_present ?? 0}/{activeQuality?.critical_fields_total ?? 5}</div>
                    <div><b className="text-foreground">Evidencia:</b> {Math.round((activeQuality?.evidence_coverage || 0) * 100)}%</div>
                  </div>
                  {activeQuality?.messages?.length ? (
                    <ul className="mt-2 list-disc space-y-1 pl-4 text-xs text-muted-foreground">
                      {activeQuality.messages.map((message) => <li key={message}>{message}</li>)}
                    </ul>
                  ) : null}
                </div>

                {(review.candidate_claims?.length || 0) > 1 && (
                  <label className="grid gap-1 rounded-lg border border-border bg-background p-3">
                    <span className="label-mono-md uppercase">Siniestro detectado en el documento</span>
                    <select
                      value={selectedCandidateIndex}
                      onChange={(event) => selectCandidate(Number(event.target.value))}
                      className="rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary"
                    >
                      {review.candidate_claims?.map((candidate, index) => (
                        <option key={`${candidate.row_index}-${candidate.label}`} value={index}>
                          {candidate.label} · {Math.round((candidate.quality?.score || candidate.confidence || 0) * 100)}%
                        </option>
                      ))}
                    </select>
                    <span className="text-xs text-muted-foreground">Si el documento contiene varios siniestros, selecciona cuál se confirmará para la evaluación.</span>
                  </label>
                )}

                <div className="rounded-lg border border-border bg-[var(--surface-low)] p-3">
                  <div className="mb-2 flex items-center gap-2">
                    <ShieldCheck className="h-4 w-4 text-primary" />
                    <span className="label-mono-md uppercase">Agentes de verificación</span>
                  </div>
                  <div className="grid gap-2 sm:grid-cols-2">
                    {(review.pipeline_agents || []).map((agent) => (
                      <div key={agent.name} className="rounded border border-border bg-background p-2 text-xs">
                        <p className="font-semibold text-foreground">{agent.name}</p>
                        <p className="mt-1 text-muted-foreground">{agent.detail}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {(review.security_findings.length > 0 || review.consistency_findings.length > 0 || missingRequired.length > 0) && (
                  <div className="rounded-lg border border-amber-300 bg-amber-50 p-3 text-amber-950 dark:bg-amber-950/25 dark:text-amber-100">
                    <div className="mb-2 flex items-center gap-2 font-semibold">
                      <AlertTriangle className="h-4 w-4" /> Alertas antes de confirmar
                    </div>
                    <ul className="space-y-1 text-sm">
                      {missingRequired.map((field) => <li key={field}>Falta campo crítico: {field}</li>)}
                      {review.security_findings.map((finding, index) => <li key={`s-${index}`}>{finding.message}</li>)}
                      {review.consistency_findings.map((finding, index) => <li key={`c-${index}`}>{finding.message}</li>)}
                    </ul>
                  </div>
                )}

                <div className="grid gap-3">
                  {REVIEW_FIELDS.map((field) => {
                    const value = draft[field.key]
                    const evidence = evidenceFor(selectedEvidence, String(field.key))
                    return (
                      <label key={String(field.key)} className="grid gap-1">
                        <span className="text-sm font-semibold text-foreground">
                          {field.label} {field.required && <span className="text-destructive">*</span>}
                        </span>
                        {field.type === 'textarea' ? (
                          <textarea
                            value={String(value ?? '')}
                            onChange={(event) => updateDraft(field.key, event.target.value)}
                            className="min-h-24 rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary"
                          />
                        ) : field.type === 'boolean' ? (
                          <select
                            value={String(value ?? true)}
                            onChange={(event) => updateDraft(field.key, event.target.value === 'true')}
                            className="rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary"
                          >
                            <option value="true">Sí</option>
                            <option value="false">No</option>
                          </select>
                        ) : (
                          <input
                            type={field.type || 'text'}
                            value={String(value ?? '')}
                            onChange={(event) => updateDraft(field.key, event.target.value)}
                            className="rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary"
                          />
                        )}
                        <span className="text-xs text-muted-foreground">
                          {evidence ? (
                            <>Pág. {evidence.page || 1} · {formatConfidence(evidence.confidence)}{evidence.inferred ? ' · inferido' : ''} · “{(evidence.source_text || '').slice(0, 120)}”</>
                          ) : (
                            'Sin evidencia directa; validar manualmente.'
                          )}
                        </span>
                      </label>
                    )
                  })}
                </div>
              </div>
            </div>

            <DialogFooter className="gap-3 border-t border-border p-4">
              <button type="button" onClick={() => { resetReview(); setStatus('idle') }} className="border border-border bg-[var(--surface-container)] px-5 py-2 label-mono-md text-foreground">
                Cancelar
              </button>
              <button type="button" onClick={() => uploadedFile && handleFileUpload({ 0: uploadedFile, length: 1, item: () => uploadedFile } as unknown as FileList)} disabled={processing} className="border border-border bg-background px-5 py-2 label-mono-md text-foreground disabled:opacity-50">
                Reprocesar
              </button>
              <button type="button" onClick={handleConfirmExtracted} disabled={processing || missingRequired.length > 0} className="bg-primary px-5 py-2 label-mono-md text-primary-foreground disabled:cursor-not-allowed disabled:opacity-50">
                {processing ? 'Procesando…' : 'Confirmar y procesar'}
              </button>
            </DialogFooter>
          </>)}
        </DialogContent>
      </Dialog>

      <div className="mx-auto max-w-6xl space-y-6">
        <header className="space-y-2">
          <div className="flex items-center gap-2 text-[var(--on-secondary-container)]">
            <span className="label-mono-md uppercase">Protocolo v4.2</span>
            <span className="text-border">/</span>
            <span className="label-mono-md text-muted-foreground">Recepción</span>
          </div>
          <h1 className="display-heading text-3xl lg:text-4xl">Paso 1: Recepción de Información del Siniestro</h1>
          <p className="max-w-2xl text-base text-readable text-muted-foreground">
            Cargue un archivo de datos para evaluación directa, o un documento PDF o texto para extracción con verificación humana antes del Paso 2.
          </p>
        </header>

        <div className="grid grid-cols-12 gap-4">
          <label
            onDragOver={(e) => {
              if (isUploading) return
              e.preventDefault()
              setDrag(true)
            }}
            onDragLeave={() => setDrag(false)}
            onDrop={(e) => {
              if (isUploading) return
              e.preventDefault()
              setDrag(false)
              handleFileUpload(e.dataTransfer.files)
            }}
            className={cn(
              'institutional-card group relative col-span-12 flex min-h-[160px] flex-col items-center justify-center gap-3 overflow-hidden p-6 transition-colors lg:col-span-8',
              isUploading && 'cursor-wait border-2 border-primary bg-[var(--secondary-container)]/40',
              uploadComplete && 'border-2 border-[var(--tertiary-fixed-dim)] bg-[var(--success-container)]/30',
              !isUploading && !uploadComplete && (drag ? 'cursor-copy border-2 border-primary bg-[var(--secondary-container)]' : 'cursor-pointer hover:border-primary'),
            )}
            aria-busy={isUploading}
          >
            <input
              className="absolute inset-0 opacity-0 disabled:pointer-events-none"
              type="file"
              name="claims_file"
              aria-label="Subir archivo de datos, documento PDF o texto de siniestros"
              accept=".csv,text/csv,.pdf,application/pdf,.txt,text/plain"
              disabled={isUploading}
              onChange={(e) => handleFileUpload(e.target.files)}
            />

            {isUploading && (
              <div className="pointer-events-none absolute inset-0 z-10 flex flex-col items-center justify-center gap-4 bg-[var(--surface-lowest)]/85 backdrop-blur-[2px]" aria-live="polite">
                <div className="absolute inset-0 overflow-hidden">
                  <div className="upload-shimmer absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-primary/10 to-transparent" />
                </div>
                <div className="relative flex h-16 w-16 items-center justify-center rounded-lg border-2 border-primary bg-[var(--secondary-container)]">
                  <Loader2 className="h-8 w-8 animate-spin text-primary motion-reduce:animate-none" aria-hidden />
                </div>
                <div className="relative text-center">
                  <p className="font-display text-lg font-semibold text-foreground">Cargando archivo…</p>
                  <p className="mt-1 text-sm text-muted-foreground">Validando estructura y conectando con agentes de extracción</p>
                </div>
                <div className="relative h-1.5 w-48 overflow-hidden rounded-full bg-[var(--surface-container)]">
                  <div className="upload-progress h-full rounded-full bg-primary motion-reduce:animate-none" />
                </div>
              </div>
            )}

            {uploadComplete && (
              <div className="pointer-events-none absolute right-3 top-3 z-10 flex items-center gap-1.5 rounded-md bg-[var(--tertiary-fixed)] px-2.5 py-1 text-xs font-semibold text-[var(--on-tertiary-fixed)]">
                <CheckCircle2 className="h-3.5 w-3.5" aria-hidden />
                Listo
              </div>
            )}

            <div className={cn('flex h-20 w-20 items-center justify-center rounded-lg transition-colors', uploadComplete ? 'bg-[var(--tertiary-fixed)]' : 'bg-[var(--surface-container)] group-hover:bg-[var(--primary-container)]', isUploading && 'opacity-40')}>
              {uploadComplete ? <CheckCircle2 className="h-10 w-10 text-[var(--on-tertiary-fixed)]" aria-hidden /> : <CloudUpload className="h-10 w-10 text-muted-foreground group-hover:text-white" aria-hidden />}
            </div>
            <div className={cn('text-center', isUploading && 'opacity-30')}>
              <h3 className="font-display text-xl font-semibold">{uploadComplete ? 'Archivo recibido' : 'Carga Inteligente de Datos'}</h3>
              {uploadComplete && uploadedFile ? (
                <div className="mt-2 flex flex-col items-center gap-1">
                  <span className="inline-flex items-center gap-2 label-mono-md font-bold uppercase text-[var(--on-tertiary-fixed)]">
                    <CheckCircle2 className="h-4 w-4" aria-hidden /> Archivo cargado
                  </span>
                  <p className="text-sm text-muted-foreground">{uploadedFile.name} ({Math.round(uploadedFile.size / 1024)} KB)</p>
                </div>
              ) : (
                <>
                  <p className="text-sm leading-relaxed text-muted-foreground">Arrastre el archivo o haga clic para explorarlo desde su equipo.</p>
                  <p className="label-mono mt-1 text-muted-foreground">Formatos: archivo de datos, PDF o texto (máx. {MAX_UPLOAD_MB} MB)</p>
                </>
              )}
            </div>
          </label>

          <div className="dark-panel col-span-12 flex flex-col justify-between p-8 lg:col-span-4">
            <Gavel className="h-8 w-8 text-[var(--primary-fixed-dim)]" />
            <div className="space-y-3">
              <p className="dark-panel-kicker label-mono-md uppercase">Protocolo de Integridad</p>
              <p className="dark-panel-muted text-sm leading-relaxed">El archivo de datos mantiene el flujo directo. PDF o texto pasa por revisión con evidencia por campo.</p>
              <ul className="dark-panel-muted space-y-2 text-xs leading-relaxed">
                <li>1. Recibe archivo de datos, PDF o texto.</li>
                <li>2. Extrae y verifica campos con agentes.</li>
                <li>3. Solo tras confirmar se procesa la evaluación de riesgo.</li>
              </ul>
            </div>
          </div>

          {effectiveError && (
            <div className="institutional-card col-span-12 flex gap-3 border border-destructive bg-[var(--error-container)] p-4 text-[var(--on-error-container)]">
              <ServerCrash className="mt-0.5 h-5 w-5 shrink-0" />
              <div>
                <p className="font-semibold">{effectiveError}</p>
                {effectiveHint && <p className="mt-1 text-sm">{effectiveHint}</p>}
              </div>
            </div>
          )}

          {recentAnalyses.length > 0 && (
            <div className="institutional-card col-span-12 overflow-hidden">
              <div className="section-header flex items-center gap-2">
                <History className="h-4 w-4" />
                Siniestros que ya analizaste
                <span className="ml-auto font-normal normal-case text-muted-foreground">Guardados en este navegador · clic para reabrir el reporte</span>
              </div>
              <div className="flex gap-3 overflow-x-auto p-3">
                {recentAnalyses.map(({ saved, claim }) => {
                  const score = saved.score ?? claim?.score_final
                  return (
                    <button
                      key={`${saved.id}-${saved.savedAt}`}
                      type="button"
                      onClick={() => reopenAnalysis(saved.id)}
                      className="group flex w-[230px] shrink-0 flex-col border border-border bg-[var(--surface-low)] p-3 text-left transition-colors hover:border-primary hover:bg-[var(--surface-high)]"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <p className="font-mono text-sm font-bold text-foreground">{saved.id}</p>
                        <RiskBadge level={saved.riskLevel || claim?.nivel_riesgo || 'medio'} size="sm" />
                      </div>
                      <div className="mt-2 grid grid-cols-2 gap-1 text-xs text-muted-foreground">
                        <div><span className="label-mono block">Ramo</span>{saved.branch || claim?.ramo || '—'}</div>
                        <div><span className="label-mono block">Puntaje</span>{score != null ? `${Math.round(Number(score))}/100` : '—'}</div>
                        <div><span className="label-mono block">Monto</span>{formatCurrency(saved.amount ?? claim?.monto_reclamado)}</div>
                        <div><span className="label-mono block">Ciudad</span>{saved.city || claim?.ciudad || '—'}</div>
                      </div>
                      <p className="mt-2 line-clamp-2 text-xs text-foreground">{saved.summary || 'Sin resumen.'}</p>
                      <p className="mt-auto pt-2 text-xs font-semibold text-primary opacity-90 group-hover:underline">Abrir reporte →</p>
                    </button>
                  )
                })}
              </div>
            </div>
          )}

          {claims.length > 0 && status === 'valid' && (
            <div className="institutional-card col-span-12 bg-[var(--surface-low)] p-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <h4 className="label-mono-md font-bold uppercase">Siniestro a procesar</h4>
                  <p className="mt-1 text-sm text-muted-foreground">{claims.length} registro(s) disponibles para revisión</p>
                </div>
                <Select value={selectedClaimId || undefined} onValueChange={selectClaim}>
                  <SelectTrigger className="w-full sm:w-[320px]"><SelectValue placeholder="Seleccione un siniestro" /></SelectTrigger>
                  <SelectContent>
                    {claims.map((claim) => (
                      <SelectItem key={claim.id_siniestro} value={claim.id_siniestro}>{claim.id_siniestro} · {claim.ramo || 'Sin ramo'} · Puntaje {Math.round(Number(claim.score_final || 0))}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}

          <div className="institutional-card col-span-12 overflow-hidden">
            <div className="section-header flex justify-between">
              <span>Previsualización de Estructura</span>
              <span className="rounded-sm border border-border bg-background px-2 py-1 text-xs uppercase text-muted-foreground">{status === 'reviewing' ? 'Revisión pendiente' : 'Mapeo automático'}</span>
            </div>
            {showPreview ? (
              <div className="overflow-x-auto">
                <table className="zebra w-full border-collapse text-left">
                  <thead>
                    <tr className="border-b border-border bg-[var(--surface-low)]">
                      {previewHeaders.map((h) => <th key={h} className="label-mono border-r border-border px-4 py-2.5 text-foreground last:border-r-0">{h}</th>)}
                    </tr>
                  </thead>
                  <tbody>
                    {csvRows.map((row) => (
                      <tr key={row.join('-')} className="border-b border-border last:border-b-0">
                        {row.map((cell, i) => <td key={`${row[0]}-${i}`} className="label-mono-md border-r border-border px-4 py-2.5 text-sm last:border-r-0">{cell}</td>)}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="p-6 text-sm text-muted-foreground">{isLoadingClaims || status === 'validating' ? 'Procesando archivo...' : 'Cargue un archivo para ver columnas, o use los datos demo para entrar directo al flujo.'}</p>
            )}
          </div>
        </div>

        <footer className="flex flex-col gap-4 border-t border-border pt-6 md:flex-row md:items-center md:justify-between">
          <div className="flex min-w-0 items-center gap-2">
            <span className={cn('h-2 w-2 rounded-full', isApiReady ? 'bg-[var(--tertiary-fixed-dim)]' : 'bg-amber-500')} />
            <span className="label-mono truncate text-foreground">{systemStatus}</span>
            {(status === 'validating' || isLoadingClaims) && <Loader2 className="h-4 w-4 animate-spin" />}
          </div>
          <div className="flex flex-col gap-3 sm:flex-row">
            <button type="button" onClick={clearAll} className="focus-ring border border-border bg-[var(--surface-container)] px-8 py-2 label-mono-md text-foreground">Limpiar</button>
            <button type="button" onClick={() => void handleUseDemo()} disabled={processing || isUploading} className="focus-ring border border-border bg-background px-8 py-2 label-mono-md text-foreground disabled:cursor-not-allowed disabled:opacity-50">
              {processing && status !== 'valid' ? 'Preparando demo...' : 'Usar datos demo'}
            </button>
            <button type="button" disabled={status !== 'valid' || processing || !selectedClaimId} onClick={handleNext} className="focus-ring bg-primary px-8 py-2 label-mono-md text-primary-foreground disabled:cursor-not-allowed disabled:opacity-50">
              {processing ? 'Procesando...' : selectedClaimId ? `Continuar con ${selectedClaimId}` : 'Selecciona un siniestro'}
            </button>
          </div>
        </footer>
      </div>
    </section>
  )
}
