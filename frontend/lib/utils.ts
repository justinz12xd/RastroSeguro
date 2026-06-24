import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Replaces technical jargon in AI-generated text with business-friendly Spanish.
 * Only modifies visible user-facing strings; does not alter code identifiers.
 */
export function sanitizeAiText(text?: string | null): string {
  if (!text) return ''
  return text
    .replace(/\bNLP\b/g, 'narrativa del relato')
    .replace(/\bML\b/g, 'patrones históricos')
    .replace(/\bIA\b/g, 'asistente')
    .replace(/\bFastAPI\b/gi, 'el sistema')
    .replace(/\bbackend\b/gi, 'el sistema')
    .replace(/\bAPI\b/g, 'el sistema')
    .replace(/\bscore\b/gi, 'puntaje')
    .replace(/\bgrafo\b/gi, 'red de relaciones')
    .replace(/\bthread\b/gi, 'conversación')
    .replace(/\bsession\b/gi, 'conversación')
    .replace(/\bsessions\b/gi, 'conversaciones')
    .replace(/\bruntime\b/gi, 'modo de respuesta')
    .replace(/\bclassic\b/gi, 'estándar')
    .replace(/\bdriver principal\b/gi, 'señal principal')
    .replace(/\bdrivers\b/gi, 'señales')
    .replace(/\bdriver\b/gi, 'señal')
    .replace(/\bpatterns\b/gi, 'patrones')
    .replace(/\bpattern\b/gi, 'patrón')
    .replace(/\bradar\b/gi, 'resumen de señales')
    .replace(/\btimeline\b/gi, 'línea de tiempo')
    .replace(/\bdemo\b/gi, 'muestra')
    .replace(/\bsimulator\b/gi, 'simulador')
    .replace(/\bdataset\b/gi, 'cartera de siniestros')
    .replace(/\bCSV\b/g, 'archivo de datos')
    .replace(/\bPDF\b/g, 'documento PDF')
    .replace(/\bTXT\b/g, 'texto')
    .replace(/\bwaterfall\b/gi, 'desglose del puntaje')
    .replace(/\branking\b/gi, 'recurrencia')
    .replace(/\bconcentraci[oó]n\b/gi, 'recurrencia')
    .replace(/\bscoring\b/gi, 'evaluación de riesgo')
    .replace(/\bzoom\b/gi, 'ampliar la vista')
    .replace(/\btop\b/gi, 'principales')
    .replace(/\bmodelo\b/gi, 'patrones históricos')
    .replace(/\banomal[ií]a(s)?\b/gi, 'comportamiento inusual')
    .replace(/\bcateg[oó]rico\b/gi, 'contexto del caso')
    .replace(/\bentidades recurrentes\b/gi, 'elementos que se repiten')
    .replace(/\bspider\b/gi, 'comparación visual')
    .replace(/\btrazabilidad\b/gi, 'detalle verificable')
    .replace(/\bingesta\b/gi, 'carga')
}
