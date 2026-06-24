const STORAGE_KEY = 'rastroseguro:lastSinNumber'

function splitCsvLine(line: string): string[] {
  const out: string[] = []
  let cur = ''
  let inQuotes = false
  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i]
    if (ch === '"') {
      const next = line[i + 1]
      if (inQuotes && next === '"') {
        cur += '"'
        i += 1
      } else {
        inQuotes = !inQuotes
      }
      continue
    }
    if (ch === ',' && !inQuotes) {
      out.push(cur)
      cur = ''
      continue
    }
    cur += ch
  }
  out.push(cur)
  return out
}

function joinCsvLine(values: string[]): string {
  return values
    .map((value) => {
      const needsQuotes = /[",\n]/.test(value)
      if (!needsQuotes) return value
      return `"${value.replace(/"/g, '""')}"`
    })
    .join(',')
}

function readLastCounter(): number {
  if (typeof window === 'undefined') return 0
  const raw = window.localStorage.getItem(STORAGE_KEY)
  const parsed = Number(raw)
  return Number.isFinite(parsed) && parsed > 0 ? Math.floor(parsed) : 0
}

function writeLastCounter(value: number) {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(STORAGE_KEY, String(Math.max(0, Math.floor(value))))
}

function nextSin(counter: number) {
  return `SIN-${String(counter).padStart(6, '0')}`
}

export async function extractCsvClaimIds(file: File): Promise<string[]> {
  const raw = await file.text()
  const lines = raw.replace(/\r\n/g, '\n').split('\n').filter((line) => line.trim())
  if (lines.length <= 1) return []

  const header = splitCsvLine(lines[0]).map((col) => col.trim().toLowerCase())
  const idIndex = header.findIndex((col) => col === 'id_siniestro')
  if (idIndex === -1) return []

  const ids: string[] = []
  const seen = new Set<string>()
  for (const line of lines.slice(1)) {
    const cols = splitCsvLine(line)
    const id = String(cols[idIndex] || '').trim()
    if (!id || seen.has(id)) continue
    seen.add(id)
    ids.push(id)
  }
  return ids
}

export async function assignIncrementalSinIds(file: File): Promise<File> {
  const raw = await file.text()
  const lines = raw.replace(/\r\n/g, '\n').split('\n')
  if (!lines.length || !lines[0].trim()) return file

  const header = splitCsvLine(lines[0])
  const idIndex = header.findIndex((col) => col.trim().toLowerCase() === 'id_siniestro')
  if (idIndex === -1) {
    header.unshift('id_siniestro')
  }

  let counter = readLastCounter()
  const rebuilt = [joinCsvLine(idIndex === -1 ? header : splitCsvLine(lines[0]))]

  for (let i = 1; i < lines.length; i += 1) {
    const line = lines[i]
    if (!line.trim()) continue
    const cols = splitCsvLine(line)
    counter += 1
    const id = nextSin(counter)
    if (idIndex === -1) {
      cols.unshift(id)
    } else {
      while (cols.length <= idIndex) cols.push('')
      cols[idIndex] = id
    }
    rebuilt.push(joinCsvLine(cols))
  }

  if (rebuilt.length <= 1) return file

  writeLastCounter(counter)
  const normalizedCsv = `${rebuilt.join('\n')}\n`
  return new File([normalizedCsv], file.name, { type: 'text/csv' })
}
