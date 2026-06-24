'use client'

import { useState, useRef, useEffect, useMemo } from 'react'
import { useAppState } from '@/lib/app-context'
import { AgentChatMessage, AgentChatSection, AgentChatSessionSummary, ApiClientError, chatAgent, getAgentSessions, getAgentThread, getQuickQuestions } from '@/lib/api'
import { AgentResult } from '@/components/agent/agent-result'
import { getExecutiveStepTitle, getStepContext, getStepQuickQuestions, getStepGuideMessage } from '@/lib/demo-step-context'
import { History, MessageCircle, Plus, X, Send, Bot, User } from 'lucide-react'
import { cn, sanitizeAiText } from '@/lib/utils'
import { renderMarkdownBlocks } from '@/lib/markdown'
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'

const THREAD_STORAGE_KEY = 'rastroseguro-agent-thread-id'
const USER_STORAGE_KEY = 'rastroseguro-agent-user-id'
const DEVICE_STORAGE_KEY = 'rastroseguro-agent-device-id'

function shortenQuestion(text: string, max = 72): string {
  const trimmed = text.trim()
  if (trimmed.length <= max) return trimmed
  return `${trimmed.slice(0, max - 1)}...`
}

function normalizeAssistantText(text: string): string {
  return sanitizeAiText(
    text
      .replace(/^#{1,6}\s*/gm, '')
      .replace(/\*\*(.*?)\*\*/g, '$1')
      .replace(/__(.*?)__/g, '$1')
      .replace(/`([^`]+)`/g, '$1')
      .replace(/^\s*[-*]\s+/gm, '• ')
      .replace(/\n{3,}/g, '\n\n')
      .trim(),
  )
}

function toUiMessage(message: AgentChatMessage) {
  const normalizedContent = message.role === 'assistant'
    ? normalizeAssistantText(message.content)
    : message.content
  const response = message.role === 'assistant' && (message.intent || message.data !== undefined)
    ? {
        ok: typeof message.metadata?.ok === 'boolean' ? Boolean(message.metadata.ok) : true,
        intent: message.intent || undefined,
        message: normalizedContent,
        data: message.data,
        source: message.source || undefined,
        llm: typeof message.metadata?.llm === 'object' ? message.metadata.llm as Record<string, unknown> : undefined,
        runtime: typeof message.metadata?.runtime === 'object' ? message.metadata.runtime as Record<string, unknown> : undefined,
      }
    : undefined
  return {
    id: message.id,
    sectionId: message.section_id || null,
    role: message.role,
    content: normalizedContent,
    timestamp: new Date(message.timestamp),
    response,
  } as const
}

function ensureLocalDeviceId(): string {
  try {
    const saved = window.localStorage.getItem(DEVICE_STORAGE_KEY) || window.localStorage.getItem(USER_STORAGE_KEY)
    if (saved) {
      window.localStorage.setItem(DEVICE_STORAGE_KEY, saved)
      return saved
    }
    const generated = crypto.randomUUID()
    window.localStorage.setItem(DEVICE_STORAGE_KEY, generated)
    return generated
  } catch {
    return 'anonymous'
  }
}

function scopedChatUserId(deviceId: string, role: 'analyst' | 'executive' | null): string {
  if (!role) return deviceId || 'anonymous'
  return `${deviceId || 'anonymous'}:${role}`
}

function roleLabel(role: 'analyst' | 'executive' | null): string {
  if (role === 'analyst') return 'Analista'
  if (role === 'executive') return 'Ejecutivo'
  return 'Usuario'
}

type AssistantVariant = 'sidebar' | 'floating'

export function AIAssistant({ variant = 'floating' }: { variant?: AssistantVariant }) {
  const {
    showChat,
    setShowChat,
    selectedClaimId,
    setSelectedClaimId,
    setIsDataLoaded,
    setCurrentStep,
    userRole,
    currentStep,
    chatMessages,
    addChatMessage,
    replaceChatMessages,
    pendingChatPrompt,
    consumeChatPrompt,
  } = useAppState()
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [apiQuickQuestions, setApiQuickQuestions] = useState<string[]>([])
  const [userId, setUserId] = useState('anonymous')
  const [threadId, setThreadId] = useState<string | null>(null)
  const [sessions, setSessions] = useState<AgentChatSessionSummary[]>([])
  const [sections, setSections] = useState<AgentChatSection[]>([])
  const [showSessionHistory, setShowSessionHistory] = useState(false)
  const [isDesktopViewport, setIsDesktopViewport] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const lastConsumedPromptIdRef = useRef<string | null>(null)
  const lastGuideStepRef = useRef<number | null>(null)
  const prevClaimRef = useRef<string | null | undefined>(undefined)
  const isRestoringSessionRef = useRef(false)
  const reduceMotion = useReducedMotion()
  const stepContext = getStepContext(currentStep)
  const isExecutive = userRole === 'executive'
  const activeClaimId = isExecutive ? null : selectedClaimId
  const currentContextTitle = isExecutive ? getExecutiveStepTitle(currentStep) : stepContext.title
  // Both variants stay mounted at once (floating for mobile, sidebar for
  // desktop). Only the one visible at the current viewport may write guide
  // messages to the shared chat state, otherwise the message is duplicated.
  const isActiveVariant = isDesktopViewport ? variant === 'sidebar' : variant === 'floating'

  const quickQuestions = useMemo(() => {
    const base = userRole === 'executive'
      ? [
          'Genera un resumen ejecutivo de la cartera priorizada.',
          '¿Cuál es el impacto de negocio de los casos más urgentes?',
          '¿Qué proveedores o ramos concentran mayor exposición?',
          '¿Qué decisión recomiendas para priorizar la revisión?',
        ]
      : getStepQuickQuestions(currentStep, activeClaimId)
    if (!apiQuickQuestions.length) return base
    const merged = [...base]
    for (const q of apiQuickQuestions) {
      if (!merged.includes(q)) merged.push(q)
    }
    return merged.slice(0, 5)
  }, [activeClaimId, apiQuickQuestions, currentStep, userRole])

  useEffect(() => {
    const media = window.matchMedia('(min-width: 1024px)')
    const apply = () => setIsDesktopViewport(media.matches)
    apply()
    media.addEventListener('change', apply)
    return () => media.removeEventListener('change', apply)
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMessages, isTyping])

  useEffect(() => {
    const resolvedUserId = scopedChatUserId(ensureLocalDeviceId(), userRole)
    setUserId(resolvedUserId)
    setSections([])
    setSessions([])
    setShowSessionHistory(false)
    lastGuideStepRef.current = null
    replaceChatMessages([])
    try {
      setThreadId(window.localStorage.getItem(`${THREAD_STORAGE_KEY}:${resolvedUserId}`))
    } catch {
      setThreadId(null)
    }
  }, [userRole, replaceChatMessages])

  useEffect(() => {
    try {
      if (threadId) {
        window.localStorage.setItem(`${THREAD_STORAGE_KEY}:${userId}`, threadId)
      } else {
        window.localStorage.removeItem(`${THREAD_STORAGE_KEY}:${userId}`)
      }
    } catch {
      // Ignore storage restrictions.
    }
  }, [threadId, userId])

  // Switching to a different claim must start a fresh conversation: the chat is
  // scoped to the case in focus, so the previous case's thread (and the history
  // sent to the LLM) should not bleed into the new one.
  useEffect(() => {
    if (isExecutive) {
      prevClaimRef.current = selectedClaimId
      return
    }
    if (isRestoringSessionRef.current) {
      prevClaimRef.current = selectedClaimId
      isRestoringSessionRef.current = false
      return
    }
    if (prevClaimRef.current === undefined) {
      prevClaimRef.current = selectedClaimId
      return
    }
    if (prevClaimRef.current === selectedClaimId) return
    prevClaimRef.current = selectedClaimId
    setThreadId(null)
    setSections([])
    setShowSessionHistory(false)
    lastGuideStepRef.current = null
    replaceChatMessages([])
  }, [isExecutive, replaceChatMessages, selectedClaimId])

  const refreshSessions = () => {
    void getAgentSessions(userId)
      .then(setSessions)
      .catch(() => setSessions([]))
  }

  useEffect(() => {
    if (!showChat) return
    void getQuickQuestions(userRole || 'analyst')
      .then((questions) => setApiQuickQuestions(questions.slice(0, 3)))
      .catch(() => setApiQuickQuestions([]))
    refreshSessions()
  }, [showChat, userId, userRole])

  useEffect(() => {
    if (!showChat || !threadId) return
    void getAgentThread(threadId, userId)
      .then((session) => {
        const restoredClaimId = session.context.selected_claim_id || null
        if (restoredClaimId !== selectedClaimId) {
          isRestoringSessionRef.current = true
          setSelectedClaimId(restoredClaimId)
          if (restoredClaimId) {
            setCurrentStep(userRole === 'executive' ? 5 : 3)
          } else if (userRole === 'executive') {
            setCurrentStep(0)
          }
        }
        setSections(session.sections)
        replaceChatMessages(session.history.map(toUiMessage))
      })
      .catch(() => {
        setThreadId(null)
        setSections([])
        replaceChatMessages([])
      })
  }, [showChat, threadId, userId, replaceChatMessages, selectedClaimId, setCurrentStep, setSelectedClaimId, userRole])

  useEffect(() => {
    if (!showChat) {
      lastGuideStepRef.current = null
    }
  }, [showChat])

  useEffect(() => {
    if (!showChat || threadId || !isActiveVariant) return

    const guide = getStepGuideMessage(currentStep, activeClaimId, userRole || 'analyst')
    const stepChanged = lastGuideStepRef.current !== currentStep
    const hasUserMessages = chatMessages.some((m) => m.role === 'user')

    if (chatMessages.length === 0) {
      addChatMessage({
        id: `step-guide-${currentStep}`,
        role: 'assistant',
        content: guide,
        timestamp: new Date(),
        sectionId: `step-${currentStep}`,
      })
      lastGuideStepRef.current = currentStep
      return
    }

    if (!hasUserMessages) {
      const onlyAssistant = chatMessages.every((m) => m.role === 'assistant')
      if (onlyAssistant && (stepChanged || chatMessages[0]?.content !== guide)) {
        replaceChatMessages([{
          id: chatMessages[0]?.id ?? `step-guide-${currentStep}`,
          role: 'assistant',
          content: guide,
          timestamp: new Date(),
          sectionId: `step-${currentStep}`,
        }])
        lastGuideStepRef.current = currentStep
      }
      return
    }

    if (stepChanged && lastGuideStepRef.current !== null) {
      addChatMessage({
        id: `step-guide-${currentStep}-${Date.now()}`,
        role: 'assistant',
        content: guide,
        timestamp: new Date(),
        sectionId: `step-${currentStep}`,
      })
      lastGuideStepRef.current = currentStep
    } else if (lastGuideStepRef.current === null) {
      lastGuideStepRef.current = currentStep
    }
  }, [
    currentStep,
    activeClaimId,
    showChat,
    threadId,
    chatMessages,
    addChatMessage,
    replaceChatMessages,
    isActiveVariant,
    userRole,
  ])

  const openClaim = (id: string) => {
    setSelectedClaimId(id)
    setIsDataLoaded(true)
    setCurrentStep(userRole === 'executive' ? 5 : 3)
    if (variant === 'floating') setShowChat(false)
  }

  const startNewSession = () => {
    setThreadId(null)
    setSections([])
    setShowSessionHistory(false)
    lastGuideStepRef.current = null
    replaceChatMessages([])
  }

  const openSession = (sessionId: string) => {
    setThreadId(sessionId)
    setShowSessionHistory(false)
  }

  const handleSend = async (text: string = input) => {
    if (!text.trim() || isTyping) return

    addChatMessage({
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    })

    setInput('')
    setIsTyping(true)

    try {
      const session = await chatAgent({
        message: text,
        userId,
        threadId,
        selectedClaimId: activeClaimId,
        runtime: 'langgraph',
        userRole,
        uiContext: { step: currentStep, step_title: currentContextTitle },
      })
      setThreadId(session.thread_id)
      setSections(session.sections)
      replaceChatMessages(session.history.map((message) => {
        const mapped = toUiMessage(message)
        if (message.id === session.history[session.history.length - 1]?.id && mapped.role === 'assistant') {
          return {
            ...mapped,
            response: session.reply,
          }
        }
        return mapped
      }))
      refreshSessions()
    } catch (error) {
      const message = error instanceof ApiClientError
        ? `${error.message}${error.hint ? `\n\n${error.hint}` : ''}`
        : 'No se pudo consultar al asistente.'
      addChatMessage({
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: message,
        timestamp: new Date(),
      })
    } finally {
      setIsTyping(false)
    }
  }

  useEffect(() => {
    if (!showChat || !pendingChatPrompt || isTyping) return
    const isActiveInstance = variant === 'sidebar' ? isDesktopViewport : !isDesktopViewport
    if (!isActiveInstance) return
    if (lastConsumedPromptIdRef.current === pendingChatPrompt.id) return
    lastConsumedPromptIdRef.current = pendingChatPrompt.id
    const prompt = pendingChatPrompt.text
    consumeChatPrompt()
    void handleSend(prompt)
  }, [showChat, pendingChatPrompt, isTyping, consumeChatPrompt, variant, isDesktopViewport])

  const sectionTitleById = useMemo(() => {
    return new Map(sections.map((section) => [section.section_id, section.title]))
  }, [sections])

  function resolveSectionTitle(sectionId: string | null | undefined): string {
    if (!sectionId) return 'Conversación'
    if (sectionId.startsWith('step-')) {
      const stepNum = Number(sectionId.replace('step-', ''))
      if (!Number.isNaN(stepNum)) {
        return isExecutive ? getExecutiveStepTitle(stepNum) : `${stepNum > 0 ? `Paso ${stepNum}` : 'Inicio'} · ${getStepContext(stepNum).title}`
      }
    }
    return sectionTitleById.get(sectionId) || 'Conversación'
  }

  const panelClassName = variant === 'sidebar'
    ? 'flex h-full w-full flex-col overflow-hidden bg-card text-card-foreground'
    : cn(
        'fixed bottom-[calc(9rem+env(safe-area-inset-bottom,0px))] right-3 z-[110] flex flex-col overflow-hidden border border-border bg-card text-card-foreground shadow-2xl ring-1 ring-border/60 dark:shadow-black/40 lg:hidden',
        'h-[min(56vh,460px)] w-[min(94vw,420px)] rounded-xl',
      )

  if (variant === 'floating' && showChat) {
    // floating only on mobile
  }

  const renderPanel = () => (
    <div role="dialog" aria-label="Asistente" className={panelClassName}>
      <div className="flex shrink-0 items-center justify-between gap-3 border-b border-border bg-[var(--surface-container)] px-3 py-2.5 text-foreground">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[var(--secondary-container)] text-[var(--on-secondary-container)]">
            <Bot className="h-4 w-4" />
          </div>
          <div className="min-w-0">
            <p className="truncate font-semibold">Asistente · {roleLabel(userRole)}</p>
            <p className="label-mono truncate text-xs text-muted-foreground">
              {isExecutive ? currentContextTitle : `Paso ${currentStep > 0 ? currentStep : 'inicio'} · ${currentContextTitle}`}
              {selectedClaimId ? ` · ${selectedClaimId}` : ''}
            </p>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-1">
          <button
            type="button"
            onClick={() => setShowSessionHistory((value) => !value)}
            className="focus-ring rounded-lg p-2 text-muted-foreground transition-colors hover:bg-[var(--surface-high)] hover:text-foreground"
            aria-label="Historial de conversaciones"
            title="Historial"
          >
            <History className="h-5 w-5" />
          </button>
          <button
            type="button"
            onClick={startNewSession}
            className="focus-ring rounded-lg p-2 text-muted-foreground transition-colors hover:bg-[var(--surface-high)] hover:text-foreground"
            aria-label="Nueva conversación"
            title="Nueva conversación"
          >
            <Plus className="h-5 w-5" />
          </button>
          <button
            type="button"
            onClick={() => setShowChat(false)}
            className="focus-ring rounded-lg p-2 text-muted-foreground transition-colors hover:bg-[var(--surface-high)] hover:text-foreground"
            aria-label="Cerrar asistente"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
      </div>

      <div className="flex min-h-0 flex-1 flex-col">
        {showSessionHistory && (
          <div className="shrink-0 border-b border-border bg-card px-3 py-2">
            <div className="flex max-h-24 gap-2 overflow-x-auto">
              {sessions.map((session) => (
                <button
                  key={session.thread_id}
                  type="button"
                  onClick={() => openSession(session.thread_id)}
                  className={cn(
                    'focus-ring min-w-[180px] rounded-md border px-3 py-2 text-left text-xs transition-colors',
                    session.thread_id === threadId
                      ? 'border-primary bg-primary/10 text-foreground'
                      : 'border-border bg-[var(--surface-low)] text-muted-foreground hover:text-foreground',
                  )}
                >
                  <span className="block truncate font-medium">{session.title}</span>
                  <span className="label-mono mt-1 block text-[10px]">{session.message_count} mensajes</span>
                </button>
              ))}
            </div>
          </div>
        )}
        <div className="min-h-0 flex-1 space-y-3 overflow-y-auto bg-[var(--surface-low)] p-3">
          {chatMessages.map((message, index) => {
            const previous = chatMessages[index - 1]
            const shouldShowSection = message.sectionId && message.sectionId !== previous?.sectionId
            return (
              <div key={message.id} className="space-y-3">
                {shouldShowSection && (
                  <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    <div className="h-px flex-1 bg-border" />
                    <span className="max-w-[70%] truncate label-mono">
                            {resolveSectionTitle(message.sectionId)}
                    </span>
                    <div className="h-px flex-1 bg-border" />
                  </div>
                )}
                <div className={cn('flex gap-2.5', message.role === 'user' ? 'flex-row-reverse' : '')}>
                  <div
                    className={cn(
                      'flex h-8 w-8 shrink-0 items-center justify-center rounded-full',
                      message.role === 'assistant' ? 'bg-[var(--secondary-container)]' : 'bg-primary text-primary-foreground',
                    )}
                  >
                    {message.role === 'assistant' ? (
                      <Bot className="h-4 w-4 text-[var(--on-secondary-container)]" />
                    ) : (
                      <User className="h-4 w-4" />
                    )}
                  </div>
                  <div
                    className={cn(
                      'rounded-lg px-3 py-2 text-xs leading-relaxed',
                      message.role === 'assistant'
                        ? 'border border-border bg-card text-card-foreground'
                        : 'max-w-[85%] bg-primary text-primary-foreground',
                      message.role === 'assistant' && message.response ? 'w-full max-w-[92%]' : 'max-w-[85%]',
                    )}
                  >
                    {message.role === 'assistant' && message.response ? (
                      <AgentResult response={message.response} onOpenClaim={openClaim} />
                    ) : message.role === 'assistant' ? (
                      renderMarkdownBlocks(message.content)
                    ) : (
                      <p className="whitespace-pre-wrap break-words">{message.content}</p>
                    )}
                  </div>
                </div>
              </div>
            )
          })}

          {isTyping && (
            <div className="flex gap-2.5">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[var(--secondary-container)]">
                <Bot className="h-4 w-4 text-[var(--on-secondary-container)]" />
              </div>
              <div className="rounded-lg border border-border bg-card px-4 py-3">
                <div className="flex gap-1">
                  <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/50" style={{ animationDelay: '0ms' }} />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/50" style={{ animationDelay: '150ms' }} />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/50" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="shrink-0 border-t border-border bg-card">
          <div className="max-h-[64px] overflow-y-auto px-3 pt-2">
            <div className="flex gap-2 overflow-x-auto pb-1">
              {quickQuestions.slice(0, 3).map((q) => (
                <button
                  key={q}
                  type="button"
                  title={q}
                  onClick={() => handleSend(q)}
                  disabled={isTyping}
                  className="focus-ring shrink-0 rounded-full border border-border bg-[var(--surface-low)] px-3 py-1.5 text-xs text-foreground transition-colors hover:border-primary disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {shortenQuestion(q, 42)}
                </button>
              ))}
            </div>
          </div>

          <div className="p-3">
            <div className="rounded-xl border border-border bg-[var(--surface-low)] px-3 py-2.5">
              <textarea
                name="agent_question"
                aria-label="Pregunta para el asistente"
                rows={2}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    void handleSend()
                  }
                }}
                placeholder="¿Qué quieres consultar?"
                className="min-h-[36px] max-h-20 w-full resize-none bg-transparent text-xs text-foreground placeholder:text-muted-foreground focus:outline-none"
              />

              <div className="mt-2 flex items-center justify-between">
                <span className="label-mono text-[10px] text-muted-foreground">
                  Enter envía · Shift+Enter nueva línea
                </span>
                <button
                  type="button"
                  onClick={() => void handleSend()}
                  disabled={!input.trim() || isTyping}
                  className={cn(
                    'focus-ring flex h-8 w-8 items-center justify-center rounded-md border border-border bg-background text-foreground transition-colors hover:bg-[var(--surface-high)]',
                    (!input.trim() || isTyping) && 'cursor-not-allowed opacity-50',
                  )}
                  aria-label="Enviar mensaje"
                >
                  <Send className="h-4 w-4" />
                </button>
              </div>
            </div>
            <p className="mt-2 text-center text-xs text-muted-foreground">
              Ayuda a priorizar la revisión humana; no acusa fraude automáticamente.
            </p>
          </div>
        </div>
      </div>
    </div>
  )

  if (variant === 'sidebar') {
    if (!showChat) return null
    return renderPanel()
  }

  return (
    <>
      <AnimatePresence>
        {!showChat && (
          <>
            <motion.button
              type="button"
              initial={reduceMotion ? false : { y: 12, opacity: 0, scale: 0.95 }}
              animate={reduceMotion ? undefined : {
                y: 0,
                opacity: 1,
                scale: [1, 1.06, 1],
                boxShadow: ['0 0 0 0 rgba(79,70,229,0.35)', '0 0 0 12px rgba(79,70,229,0)', '0 0 0 0 rgba(79,70,229,0)'],
              }}
              transition={reduceMotion ? undefined : { duration: 2, repeat: Infinity, repeatDelay: 1.2 }}
              exit={reduceMotion ? undefined : { y: 12, opacity: 0 }}
              onClick={() => setShowChat(true)}
              className="focus-ring fixed bottom-[calc(5rem+env(safe-area-inset-bottom,0px))] right-4 z-[110] flex h-12 w-12 items-center justify-center rounded-full border border-primary/40 bg-primary text-primary-foreground shadow-lg lg:hidden"
              aria-label="Abrir asistente"
            >
              <MessageCircle className="h-5 w-5" />
            </motion.button>

            <motion.button
              type="button"
              initial={reduceMotion ? false : { x: 12, opacity: 0 }}
              animate={reduceMotion ? undefined : { x: 0, opacity: 1 }}
              exit={reduceMotion ? undefined : { x: 12, opacity: 0 }}
              onClick={() => setShowChat(true)}
              className="focus-ring fixed right-0 top-1/2 z-[110] hidden -translate-y-1/2 flex-col items-center gap-2 rounded-l-md border border-r-0 border-primary/30 bg-primary px-2.5 py-4 text-primary-foreground shadow-lg hover:opacity-95 lg:flex"
              aria-label="Abrir chat lateral"
              title="Abrir asistente lateral"
            >
              <MessageCircle className="h-5 w-5" />
              <span className="label-mono-md text-[10px] font-bold uppercase tracking-wider [writing-mode:vertical-rl]">
                Asistente
              </span>
            </motion.button>
          </>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showChat && (
          <motion.div
            initial={reduceMotion ? false : { opacity: 0, y: 16, scale: 0.98 }}
            animate={reduceMotion ? undefined : { opacity: 1, y: 0, scale: 1 }}
            exit={reduceMotion ? undefined : { opacity: 0, y: 16, scale: 0.98 }}
            transition={{ duration: reduceMotion ? 0 : 0.2 }}
            className="lg:hidden"
          >
            {renderPanel()}
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
