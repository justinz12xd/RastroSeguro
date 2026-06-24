'use client'

import { useCallback, useEffect, useState } from 'react'
import { AppProvider, useAppState } from '@/lib/app-context'
import { Sidebar } from '@/components/sidebar'
import { Header } from '@/components/header'
import { StepCommandCenter } from '@/components/steps/step-command-center'
import { StepUpload } from '@/components/steps/step-upload'
import { StepSummary } from '@/components/steps/step-summary'
import { StepAnalysis } from '@/components/steps/step-analysis'
import { StepIntelligence } from '@/components/steps/step-intelligence'
import { StepCaseClosure } from '@/components/steps/step-case-closure'
import { StepExecutiveDemo } from '@/components/steps/step-executive-demo'
import { AIAssistant } from '@/components/ai-assistant'
import { CommandBar } from '../../components/command-bar'
import { RoleSelector } from '@/components/role-selector'
import { MobileNav } from '@/components/mobile-nav'
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import { cn } from '@/lib/utils'

const STEP_VIEWS: Record<number, React.ComponentType> = {
  0: StepCommandCenter,
  1: StepUpload,
  2: StepSummary,
  3: StepAnalysis,
  4: StepIntelligence,
  5: StepCaseClosure,
  6: StepExecutiveDemo,
}

const CHAT_WIDTH_STORAGE_KEY = 'rastroseguro-chat-width'
const CHAT_WIDTH_MIN = 320
const CHAT_WIDTH_MAX = 720
const CHAT_WIDTH_DEFAULT = 380
// Left rail (lg:ml-64 = 16rem) plus the breathing room the main column must keep
// so the chat can never crush the workflow view on narrow desktops.
const DESKTOP_RAIL = 256
const MAIN_MIN_WIDTH = 400

// Clamp the chat width to the viewport: never below the readable minimum, never
// so wide that the main column drops under MAIN_MIN_WIDTH. Falls back to the
// fixed ceiling when the viewport is unknown (SSR / first paint).
function clampChatWidth(width: number, viewportWidth?: number): number {
  let max = CHAT_WIDTH_MAX
  if (viewportWidth && viewportWidth > 0) {
    const available = viewportWidth - DESKTOP_RAIL - MAIN_MIN_WIDTH
    max = Math.min(CHAT_WIDTH_MAX, Math.max(CHAT_WIDTH_MIN, available))
  }
  return Math.min(max, Math.max(CHAT_WIDTH_MIN, width))
}

function MainContent() {
  const {
    currentStep,
    showCommandBar,
    setShowCommandBar,
    userRole,
    setCurrentStep,
    showChat,
    setShowChat,
    isDataLoaded,
    selectedClaimId,
    setSelectedClaimId,
    setIsDataLoaded,
    claims,
  } = useAppState()

  const flowReady = isDataLoaded && selectedClaimId !== null

  useEffect(() => {
    if (userRole === 'executive' && currentStep >= 1 && currentStep <= 4) {
      setCurrentStep(0)
    }
  }, [currentStep, setCurrentStep, userRole])

  useEffect(() => {
    if (userRole !== 'executive' || currentStep !== 5 || selectedClaimId || !claims.length) return
    setSelectedClaimId(claims[0].id_siniestro)
    setIsDataLoaded(true)
  }, [claims, currentStep, selectedClaimId, setIsDataLoaded, setSelectedClaimId, userRole])

  useEffect(() => {
    if (!userRole) return

    if (userRole === 'analyst') {
      if (flowReady && currentStep >= 2) {
        setShowChat(true)
      }
      return
    }

    if (userRole === 'executive' && flowReady && (currentStep === 5 || currentStep === 6)) {
      setShowChat(true)
    }
  }, [userRole, currentStep, flowReady, setShowChat])

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        setShowCommandBar(!showCommandBar)
        return
      }
      if (event.key === 'Escape' && showCommandBar) {
        setShowCommandBar(false)
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [showCommandBar, setShowCommandBar])

  const [chatWidth, setChatWidth] = useState(CHAT_WIDTH_DEFAULT)
  const [isResizingChat, setIsResizingChat] = useState(false)

  // Restore the user's preferred chat width once on mount, clamped to the
  // current viewport so a width saved on a wide screen can't crush a laptop.
  useEffect(() => {
    try {
      const saved = window.localStorage.getItem(CHAT_WIDTH_STORAGE_KEY)
      if (saved) setChatWidth(clampChatWidth(Number(saved), window.innerWidth))
    } catch {
      // Ignore storage restrictions.
    }
  }, [])

  // Re-clamp when the viewport shrinks (resize / orientation change) so the
  // main column always keeps its minimum.
  useEffect(() => {
    const onResize = () => setChatWidth((w) => clampChatWidth(w, window.innerWidth))
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])

  // Persist width changes (covers keyboard nudges; drag also saves on release).
  useEffect(() => {
    const id = window.setTimeout(() => {
      try {
        window.localStorage.setItem(CHAT_WIDTH_STORAGE_KEY, String(chatWidth))
      } catch {
        // Ignore storage restrictions.
      }
    }, 250)
    return () => window.clearTimeout(id)
  }, [chatWidth])

  // Drag the left border of the chat panel to resize it. The panel is anchored
  // to the right edge of the viewport, so width = viewport width - pointer X.
  const startChatResize = useCallback((event: React.PointerEvent<HTMLDivElement>) => {
    event.preventDefault()
    setIsResizingChat(true)
    document.body.style.userSelect = 'none'
    document.body.style.cursor = 'col-resize'
    const onMove = (e: PointerEvent) => {
      setChatWidth(clampChatWidth(window.innerWidth - e.clientX, window.innerWidth))
    }
    const onUp = () => {
      setIsResizingChat(false)
      document.body.style.userSelect = ''
      document.body.style.cursor = ''
      window.removeEventListener('pointermove', onMove)
      window.removeEventListener('pointerup', onUp)
    }
    window.addEventListener('pointermove', onMove)
    window.addEventListener('pointerup', onUp)
  }, [])

  const reduceMotion = useReducedMotion()
  const StepView = STEP_VIEWS[currentStep] ?? StepCommandCenter

  if (!userRole) return <RoleSelector />

  return (
    <div className="flex h-svh overflow-hidden bg-background text-foreground">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col lg:ml-64">
        <Header />
        <div className="flex min-h-0 min-w-0 flex-1">
          <main className="min-w-0 flex-1 overflow-y-auto overflow-x-hidden pb-[calc(6rem+env(safe-area-inset-bottom,0px))] lg:pb-0">
            <AnimatePresence mode="wait" initial={false}>
              <motion.div
                key={currentStep}
                className="min-h-full"
                initial={reduceMotion ? { opacity: 0 } : { opacity: 0, transform: 'translateY(8px)' }}
                animate={{ opacity: 1, transform: 'translateY(0px)' }}
                exit={reduceMotion ? { opacity: 0 } : { opacity: 0, transform: 'translateY(-6px)' }}
                transition={{ duration: 0.26, ease: [0.23, 1, 0.32, 1] }}
              >
                <StepView />
              </motion.div>
            </AnimatePresence>
          </main>
          {showChat && (
            <aside
              className="relative hidden min-h-0 shrink-0 flex-col border-l border-border lg:flex"
              style={{ width: chatWidth }}
            >
              <div
                role="separator"
                aria-orientation="vertical"
                aria-label="Redimensionar asistente"
                aria-valuenow={Math.round(chatWidth)}
                aria-valuemin={CHAT_WIDTH_MIN}
                aria-valuemax={CHAT_WIDTH_MAX}
                tabIndex={0}
                onPointerDown={startChatResize}
                onKeyDown={(e) => {
                  // Arrow keys nudge; wider chat = smaller X, so Left grows it.
                  if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
                    e.preventDefault()
                    const delta = e.key === 'ArrowLeft' ? 24 : -24
                    setChatWidth((w) => clampChatWidth(w + delta, window.innerWidth))
                  }
                }}
                className={cn(
                  'focus-ring group absolute left-0 top-0 z-20 flex h-full w-2 -translate-x-1/2 cursor-col-resize items-center justify-center',
                )}
              >
                <span
                  className={cn(
                    'h-12 w-1 rounded-full bg-border transition-colors group-hover:bg-primary',
                    isResizingChat && 'bg-primary',
                  )}
                />
              </div>
              <AIAssistant variant="sidebar" />
            </aside>
          )}
        </div>
      </div>
      <AIAssistant variant="floating" />
      <CommandBar />
      <MobileNav />
    </div>
  )
}

export default function PlatformPage() {
  return (
    <AppProvider>
      <MainContent />
    </AppProvider>
  )
}
