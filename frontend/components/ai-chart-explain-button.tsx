'use client'

import { MouseEvent } from 'react'
import { Sparkles } from 'lucide-react'
import { useAppState } from '@/lib/app-context'
import { cn } from '@/lib/utils'

export function AIChartExplainButton({
  prompt,
  className,
  title = 'Explicar gráfico con IA',
}: {
  prompt: string
  className?: string
  title?: string
}) {
  const { requestChatPrompt } = useAppState()

  const handleClick = (event: MouseEvent<HTMLButtonElement>) => {
    event.preventDefault()
    event.stopPropagation()
    requestChatPrompt(prompt)
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      className={cn(
        'focus-ring absolute right-2 top-2 z-20 inline-flex h-7 w-7 items-center justify-center rounded-md border border-primary/30 bg-card/90 text-primary shadow-sm backdrop-blur transition hover:border-primary hover:bg-primary hover:text-primary-foreground',
        className,
      )}
      aria-label={title}
      title={title}
    >
      <Sparkles className="h-3.5 w-3.5" />
    </button>
  )
}
