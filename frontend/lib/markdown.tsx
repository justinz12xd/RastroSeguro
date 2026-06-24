import { Fragment, type ReactNode } from 'react'

function formatInline(text: string) {
  const parts: ReactNode[] = []
  let cursor = 0
  const pattern = /(\*\*([^*]+)\*\*|__([^_]+)__|`([^`]+)`)/g
  let match: RegExpExecArray | null

  while ((match = pattern.exec(text))) {
    if (match.index > cursor) parts.push(text.slice(cursor, match.index))
    if (match[2]) parts.push(<strong key={`${match.index}-b`}>{match[2]}</strong>)
    else if (match[3]) parts.push(<em key={`${match.index}-i`}>{match[3]}</em>)
    else if (match[4]) parts.push(<code key={`${match.index}-c`} className="rounded bg-[var(--surface-container)] px-1 py-0.5 font-mono text-[0.92em]">{match[4]}</code>)
    cursor = match.index + match[0].length
  }

  if (cursor < text.length) parts.push(text.slice(cursor))
  return parts
}

function renderParagraph(text: string, key: string) {
  return <p key={key} className="whitespace-pre-wrap leading-relaxed">{formatInline(text)}</p>
}

export function renderMarkdownBlocks(text: string) {
  const cleaned = String(text || '').replace(/\r\n/g, '\n').trim()
  if (!cleaned) return null

  const lines = cleaned.split('\n')
  const blocks: ReactNode[] = []
  let i = 0

  while (i < lines.length) {
    const line = lines[i].trimEnd()
    if (!line.trim()) {
      i += 1
      continue
    }

    const heading = line.match(/^(#{1,3})\s+(.*)$/)
    if (heading) {
      const level = heading[1].length
      const Tag = level === 1 ? 'h1' : level === 2 ? 'h2' : 'h3'
      blocks.push(<Tag key={`h-${i}`} className={level === 1 ? 'text-2xl font-bold' : level === 2 ? 'text-xl font-semibold' : 'text-lg font-semibold'}>{formatInline(heading[2])}</Tag>)
      i += 1
      continue
    }

    const bulletMatch = line.match(/^\s*[-*]\s+(.*)$/)
    if (bulletMatch) {
      const items: string[] = []
      while (i < lines.length) {
        const bullet = lines[i].trimEnd().match(/^\s*[-*]\s+(.*)$/)
        if (!bullet) break
        items.push(bullet[1])
        i += 1
      }
      blocks.push(
        <ul key={`ul-${i}`} className="space-y-1.5 pl-5">
          {items.map((item, idx) => (
            <li key={idx} className="list-disc">{formatInline(item)}</li>
          ))}
        </ul>,
      )
      continue
    }

    const paragraphLines = [line]
    i += 1
    while (i < lines.length && lines[i].trim() && !lines[i].trim().match(/^(#{1,3})\s+/) && !lines[i].trim().match(/^\s*[-*]\s+/)) {
      paragraphLines.push(lines[i].trimEnd())
      i += 1
    }
    blocks.push(renderParagraph(paragraphLines.join(' '), `p-${i}`))
  }

  return <div className="space-y-3">{blocks.map((node, index) => <Fragment key={index}>{node}</Fragment>)}</div>
}
