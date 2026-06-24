'use client'

import { createContext, useCallback, useContext, useEffect, useMemo, useState, ReactNode } from 'react'
import { ApiClientError, type AgentResponse, ClaimExplanation, ClaimSummary, getClaimExplanation, getClaims, getHealth, uploadClaimsCsv } from '@/lib/api'

export type UserRole = 'analyst' | 'executive'

export interface AnalystSubmittedCase {
  id: string
  submittedAt: string
  source: 'csv' | 'pdf' | 'txt' | 'document' | 'analysis'
  filename?: string | null
}

export interface AnalystSavedAnalysis {
  id: string
  savedAt: string
  score?: number | null
  riskLevel?: string | null
  summary: string
  recommendation: string
  topAlerts: string[]
  amount?: number | null
  branch?: string | null
  city?: string | null
  provider?: string | null
}

export interface PendingChatPrompt {
  id: string
  text: string
}

interface AppState {
  currentStep: number
  setCurrentStep: (step: number) => void
  userRole: UserRole | null
  selectUserRole: (role: UserRole) => void
  resetUserRole: () => void
  claims: ClaimSummary[]
  loadClaims: () => Promise<ClaimSummary[]>
  loadClaimExplanation: (id: string) => Promise<ClaimExplanation | null>
  uploadCsvAndRefresh: (file: File) => Promise<boolean>
  analystSubmittedCases: AnalystSubmittedCase[]
  markAnalystSubmittedCases: (cases: Array<{ id: string; source: AnalystSubmittedCase['source']; filename?: string | null }>) => void
  analystSavedAnalyses: AnalystSavedAnalysis[]
  saveAnalystCaseAnalysis: (analysis: Omit<AnalystSavedAnalysis, 'savedAt'>) => void
  selectedClaimId: string | null
  setSelectedClaimId: (id: string | null) => void
  selectedClaim: ClaimSummary | null
  selectedExplanation: ClaimExplanation | null
  isApiReady: boolean
  isLoadingClaims: boolean
  isLoadingExplanation: boolean
  apiError: string | null
  apiHint: string | null
  isDataLoaded: boolean
  setIsDataLoaded: (loaded: boolean) => void
  uploadedFile: File | null
  setUploadedFile: (file: File | null) => void
  chatMessages: ChatMessage[]
  addChatMessage: (message: ChatMessage) => void
  replaceChatMessages: (messages: ChatMessage[]) => void
  clearChatMessages: () => void
  pendingChatPrompt: PendingChatPrompt | null
  requestChatPrompt: (prompt: string) => void
  consumeChatPrompt: () => void
  showChat: boolean
  setShowChat: (show: boolean) => void
  showCommandBar: boolean
  setShowCommandBar: (show: boolean) => void
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  sectionId?: string | null
  /** Structured agent payload, when present the assistant renders the rich result. */
  response?: AgentResponse
}

const ANALYST_SUBMITTED_CASES_KEY = 'rastroseguro:analystSubmittedCases'
const ANALYST_SAVED_ANALYSES_KEY = 'rastroseguro:analystSavedAnalyses'

const AppContext = createContext<AppState | undefined>(undefined)

export function AppProvider({ children }: { children: ReactNode }) {
  const [currentStep, setCurrentStep] = useState(0)
  const [userRole, setUserRole] = useState<UserRole | null>(null)
  const [claims, setClaims] = useState<ClaimSummary[]>([])
  const [selectedClaimId, setSelectedClaimIdState] = useState<string | null>(null)
  const [selectedExplanation, setSelectedExplanation] = useState<ClaimExplanation | null>(null)
  const [isApiReady, setIsApiReady] = useState(false)
  const [isLoadingClaims, setIsLoadingClaims] = useState(false)
  const [isLoadingExplanation, setIsLoadingExplanation] = useState(false)
  const [apiError, setApiError] = useState<string | null>(null)
  const [apiHint, setApiHint] = useState<string | null>(null)
  const [isDataLoaded, setIsDataLoaded] = useState(false)
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [pendingChatPrompt, setPendingChatPrompt] = useState<PendingChatPrompt | null>(null)
  const [showChat, setShowChat] = useState(false)
  const [showCommandBar, setShowCommandBar] = useState(false)
  const [analystSubmittedCases, setAnalystSubmittedCases] = useState<AnalystSubmittedCase[]>([])
  const [analystSavedAnalyses, setAnalystSavedAnalyses] = useState<AnalystSavedAnalysis[]>([])

  useEffect(() => {
    if (typeof window === 'undefined') return
    try {
      const raw = window.localStorage.getItem(ANALYST_SUBMITTED_CASES_KEY)
      if (raw) {
        const parsed = JSON.parse(raw) as AnalystSubmittedCase[]
        if (Array.isArray(parsed)) setAnalystSubmittedCases(parsed.filter((item) => item?.id).slice(0, 20))
      }
      const savedRaw = window.localStorage.getItem(ANALYST_SAVED_ANALYSES_KEY)
      if (savedRaw) {
        const parsedSaved = JSON.parse(savedRaw) as AnalystSavedAnalysis[]
        if (Array.isArray(parsedSaved)) setAnalystSavedAnalyses(parsedSaved.filter((item) => item?.id).slice(0, 20))
      }
    } catch {
      // Ignore malformed local history; it is only a UX convenience.
    }
  }, [])

  const persistAnalystSubmittedCases = (items: AnalystSubmittedCase[]) => {
    if (typeof window === 'undefined') return
    window.localStorage.setItem(ANALYST_SUBMITTED_CASES_KEY, JSON.stringify(items.slice(0, 20)))
  }

  const persistAnalystSavedAnalyses = (items: AnalystSavedAnalysis[]) => {
    if (typeof window === 'undefined') return
    window.localStorage.setItem(ANALYST_SAVED_ANALYSES_KEY, JSON.stringify(items.slice(0, 20)))
  }

  const selectUserRole = useCallback((role: UserRole) => {
    setUserRole(role)
    setCurrentStep(role === 'analyst' ? 1 : 0)
  }, [])

  const resetUserRole = useCallback(() => {
    setUserRole(null)
    setCurrentStep(0)
  }, [])

  const selectedClaim = useMemo(
    () => selectedClaimId ? claims.find(c => c.id_siniestro === selectedClaimId) || null : null,
    [claims, selectedClaimId]
  )

  const setSelectedClaimId = useCallback((id: string | null) => {
    setSelectedClaimIdState(id)
    setSelectedExplanation(null)
  }, [])

  const rememberApiError = (error: unknown) => {
    if (error instanceof ApiClientError) {
      setApiError(error.message)
      setApiHint(error.hint || null)
      return
    }
    setApiError('Ocurrió un error inesperado conectando con RastroSeguro.')
    setApiHint(null)
  }

  const loadClaims = useCallback(async () => {
    setIsLoadingClaims(true)
    setApiError(null)
    setApiHint(null)
    try {
      await getHealth()
      const records = await getClaims(200)
      setIsApiReady(true)
      setClaims(records)
      setIsDataLoaded(records.length > 0)
      setSelectedClaimIdState((prev) => {
        if (!records.length) return null
        if (prev && records.some((claim) => claim.id_siniestro === prev)) return prev
        return records[0].id_siniestro
      })
      if (records.length === 0) {
        setApiError('El API respondió sin siniestros priorizados.')
        setApiHint('Verifica que la evaluación de riesgo haya generado datos procesados.')
      }
      return records
    } catch (error) {
      setIsApiReady(false)
      setClaims([])
      setIsDataLoaded(false)
      rememberApiError(error)
      return []
    } finally {
      setIsLoadingClaims(false)
    }
  }, [])

  const loadClaimExplanation = useCallback(async (id: string) => {
    setIsLoadingExplanation(true)
    setApiError(null)
    setApiHint(null)
    try {
      const explanation = await getClaimExplanation(id)
      setSelectedExplanation(explanation)
      return explanation
    } catch (error) {
      rememberApiError(error)
      return null
    } finally {
      setIsLoadingExplanation(false)
    }
  }, [])


  const markAnalystSubmittedCases = useCallback((cases: Array<{ id: string; source: AnalystSubmittedCase['source']; filename?: string | null }>) => {
    const clean = cases
      .map((item) => ({ ...item, id: String(item.id || '').trim() }))
      .filter((item) => item.id)
    if (!clean.length) return

    setAnalystSubmittedCases((prev) => {
      const now = new Date().toISOString()
      const next = [
        ...clean.map((item) => ({
          id: item.id,
          source: item.source,
          filename: item.filename || null,
          submittedAt: now,
        })),
        ...prev,
      ]
      const deduped: AnalystSubmittedCase[] = []
      const seen = new Set<string>()
      for (const item of next) {
        if (seen.has(item.id)) continue
        seen.add(item.id)
        deduped.push(item)
      }
      const limited = deduped.slice(0, 20)
      persistAnalystSubmittedCases(limited)
      return limited
    })
  }, [])


  const saveAnalystCaseAnalysis = useCallback((analysis: Omit<AnalystSavedAnalysis, 'savedAt'>) => {
    const cleanId = String(analysis.id || '').trim()
    if (!cleanId) return

    setAnalystSavedAnalyses((prev) => {
      const next: AnalystSavedAnalysis[] = [
        {
          ...analysis,
          id: cleanId,
          summary: String(analysis.summary || '').trim(),
          recommendation: String(analysis.recommendation || '').trim(),
          topAlerts: (analysis.topAlerts || []).map((item) => String(item)).filter(Boolean).slice(0, 5),
          savedAt: new Date().toISOString(),
        },
        ...prev.filter((item) => item.id !== cleanId),
      ].slice(0, 20)
      persistAnalystSavedAnalyses(next)
      return next
    })

    markAnalystSubmittedCases([{ id: cleanId, source: 'analysis' }])
  }, [markAnalystSubmittedCases])

  const uploadCsvAndRefresh = useCallback(async (file: File) => {
    setApiError(null)
    setApiHint(null)
    setIsLoadingClaims(true)
    try {
      const result = await uploadClaimsCsv(file)
      await loadClaims()
      markAnalystSubmittedCases((result.uploaded_claim_ids || []).map((id) => ({ id, source: 'csv', filename: file.name })))
      setUploadedFile(file)
      setIsDataLoaded(true)
      return true
    } catch (error) {
      rememberApiError(error)
      return false
    } finally {
      setIsLoadingClaims(false)
    }
  }, [loadClaims, markAnalystSubmittedCases])

  const addChatMessage = useCallback((message: ChatMessage) => {
    setChatMessages((prev) => {
      // Guard against duplicate appends: the assistant mounts twice (floating +
      // sidebar) and React Strict Mode double-invokes effects, so the same
      // stable-id guide message can be pushed more than once.
      if (prev.some((m) => m.id === message.id)) return prev
      return [...prev, message]
    })
  }, [])

  const replaceChatMessages = useCallback((messages: ChatMessage[]) => {
    setChatMessages(messages)
  }, [])

  const clearChatMessages = useCallback(() => {
    setChatMessages([])
  }, [])

  const requestChatPrompt = useCallback((prompt: string) => {
    const text = prompt.trim()
    if (!text) return
    setPendingChatPrompt({ id: `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`, text })
    setShowChat(true)
  }, [])

  const consumeChatPrompt = useCallback(() => {
    setPendingChatPrompt(null)
  }, [])

  return (
    <AppContext.Provider
      value={{
        currentStep,
        setCurrentStep,
        userRole,
        selectUserRole,
        resetUserRole,
        claims,
        loadClaims,
        loadClaimExplanation,
        uploadCsvAndRefresh,
        analystSubmittedCases,
        markAnalystSubmittedCases,
        analystSavedAnalyses,
        saveAnalystCaseAnalysis,
        selectedClaimId,
        setSelectedClaimId,
        selectedClaim,
        selectedExplanation,
        isApiReady,
        isLoadingClaims,
        isLoadingExplanation,
        apiError,
        apiHint,
        isDataLoaded,
        setIsDataLoaded,
        uploadedFile,
        setUploadedFile,
        chatMessages,
        addChatMessage,
        replaceChatMessages,
        clearChatMessages,
        pendingChatPrompt,
        requestChatPrompt,
        consumeChatPrompt,
        showChat,
        setShowChat,
        showCommandBar,
        setShowCommandBar,
      }}
    >
      {children}
    </AppContext.Provider>
  )
}

export function useAppState() {
  const context = useContext(AppContext)
  if (context === undefined) {
    throw new Error('useAppState must be used within an AppProvider')
  }
  return context
}
