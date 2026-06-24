export interface StepContext {
  step: number
  title: string
  subtitle: string
  /** Qué muestra esta pantalla (1–2 frases). */
  overview: string
  /** Puntos clave que el usuario debe revisar. */
  focusPoints: string[]
  hints: string[]
}

export const STEP_CONTEXT: Record<number, StepContext> = {
  0: {
    step: 0,
    title: 'Centro de control',
    subtitle: 'Indicadores de la cartera y selección de casos.',
    overview: 'Vista general de la cartera: distribución de riesgo, proveedores, ciudades y casos prioritarios. Desde aquí eliges qué siniestro revisar en detalle.',
    focusPoints: [
      'Totales de casos verdes, amarillos y rojos',
      'Principales proveedores y ciudades con alertas',
      'Selección del caso foco para el flujo analista',
    ],
    hints: [
      '¿Cuáles son los casos con mayor prioridad?',
      '¿Qué proveedores concentran más alertas?',
      'Genera un resumen general de la cartera.',
    ],
  },
  1: {
    step: 1,
    title: 'Carga de datos',
    subtitle: 'Recepción y validación de la cartera de siniestros.',
    overview: 'Subes o sincronizas el archivo de datos de siniestros. El sistema valida columnas, normaliza identificadores y prepara la evaluación de riesgo para toda la cartera.',
    focusPoints: [
      'Archivo cargado y filas reconocidas',
      'Campos obligatorios para reglas y patrones históricos',
      'Confirmación de que la cartera quedó activa',
    ],
    hints: [
      '¿Qué valida el sistema al subir el archivo?',
      '¿Cuántos siniestros hay en la cartera activa?',
      '¿Qué campos son obligatorios para la evaluación?',
    ],
  },
  2: {
    step: 2,
    title: 'Resumen del caso',
    subtitle: 'Ficha del caso: documentos, narrativa y contexto.',
    overview: 'Revisión de la ficha del caso antes del puntaje: narrativa, estado documental, ubicación, montos y cobertura. Aquí validas que la información base sea coherente.',
    focusPoints: [
      'Narrativa y descripción del evento',
      'Documentos completos, pendientes o inconsistentes',
      'Ramo, cobertura, monto y contexto geográfico',
    ],
    hints: [
      '¿Qué documentos faltan en este caso?',
      'Resume la narrativa del siniestro seleccionado.',
      '¿Qué datos geográficos tiene este caso?',
    ],
  },
  3: {
    step: 3,
    title: 'Resultado y motivos',
    subtitle: 'Puntaje, reglas activadas y recomendación.',
    overview: 'El puntaje final (0–100) combina reglas, patrones históricos, comportamiento inusual, narrativa, relaciones y contexto del caso. Ves el desglose, las alertas activadas y la acción sugerida — sin decisión automática.',
    focusPoints: [
      'Puntaje final y semáforo de riesgo',
      'Desglose del puntaje por señales',
      'Principales alertas y detalle verificable de reglas',
    ],
    hints: [
      '¿Por qué este caso tiene este puntaje?',
      '¿Qué reglas activó el sistema?',
      '¿Qué recomienda el sistema para este caso?',
    ],
  },
  4: {
    step: 4,
    title: 'Conexiones del caso',
    subtitle: 'Red de relaciones, recurrencias y comparación con la cartera.',
    overview: 'Exploración de la red del caso: conexiones con proveedores, beneficiarios, ciudades y otros siniestros. Los gráficos muestran elementos repetidos y grupos relacionados que pueden elevar el riesgo.',
    focusPoints: [
      'Red del caso y elementos compartidos',
      'Principales recurrencias en la cartera',
      'Comparación del caso respecto al promedio de la cartera',
    ],
    hints: [
      '¿Qué elementos se repiten en este caso?',
      '¿Hay relatos parecidos o conexiones con otros casos?',
      '¿Qué proveedores aparecen más en la red?',
    ],
  },
  5: {
    step: 5,
    title: 'Reporte y cierre',
    subtitle: 'Síntesis del caso y exportación ejecutiva.',
    overview: 'Cierre del recorrido: puntaje del caso desglosado, síntesis de etapas 1–4, gráficos explicados y contexto de la cartera. Puedes exportar un reporte .md para pitch o auditoría.',
    focusPoints: [
      'Puntaje del caso con aporte de cada señal',
      'Recorrido por etapas y gráficos explicados',
      'Expediente completo y exportación del reporte',
    ],
    hints: [
      'Resume este caso para un ejecutivo.',
      'Genera un resumen ejecutivo de la cartera.',
      '¿Cuál es el impacto de negocio de los casos más prioritarios?',
    ],
  },
  6: {
    step: 6,
    title: 'Impacto ejecutivo',
    subtitle: 'Casos estrella y exposición priorizada.',
    overview: 'Vista para decisión: casos estrella de la muestra, exposición de los más prioritarios y mensaje de impacto de negocio. Enlaza el caso individual con el valor del sistema para la organización.',
    focusPoints: [
      'Casos prioritarios para revisión (estrella)',
      'Monto priorizado de los casos más urgentes',
      'Guardrail ético: priorización, no acusación',
    ],
    hints: [
      '¿Cuáles son los casos estrella para la muestra?',
      '¿Cuál es la exposición de los casos más prioritarios?',
      'Muéstrame un caso rojo evidente.',
    ],
  },
}

export function getStepContext(step: number): StepContext {
  return STEP_CONTEXT[step] ?? STEP_CONTEXT[0]
}

export function getExecutiveStepTitle(step: number): string {
  if (step === 5) return 'Reporte ejecutivo del caso'
  if (step === 6) return 'Impacto ejecutivo'
  if (step === 0) return 'Centro de control ejecutivo'
  return getStepContext(step).title
}

function stepLabel(step: number): string {
  return step > 0 ? `Paso ${step}` : 'Inicio'
}

/** Guía explicativa uniforme para cada etapa (demo / chat lateral). */
export function getStepGuideMessage(step: number, claimId: string | null, userRole: 'analyst' | 'executive' = 'analyst'): string {
  const ctx = getStepContext(step)
  const isExecutive = userRole === 'executive'
  const title = isExecutive ? getExecutiveStepTitle(step) : ctx.title
  const overview = isExecutive && step === 5
    ? 'Resumen ejecutivo del caso seleccionado: puntaje, señales principales, relaciones relevantes, contexto de la cartera y expediente de respaldo para decisión.'
    : ctx.overview
  const focusPoints = isExecutive && step === 5
    ? ['Puntaje y nivel de riesgo del caso', 'Señales principales y recomendación', 'Contexto de la cartera y expediente de respaldo']
    : ctx.focusPoints
  const lines = [
    isExecutive ? title : `${stepLabel(step)}: ${title}`,
    '',
    overview,
    '',
    'Qué conviene revisar:',
    ...focusPoints.map((point) => `• ${point}`),
  ]

  if (claimId) {
    lines.push('', isExecutive ? `Caso seleccionado: ${claimId}. Pregúntame sobre este resumen o sobre la decisión ejecutiva.` : `Caso activo: ${claimId}. Pregúntame sobre esta etapa o sobre el caso.`)
  } else {
    lines.push('', isExecutive ? 'Selecciona un caso del panel ejecutivo para profundizar.' : 'Selecciona un caso en el panel o carga datos para profundizar.')
  }

  return lines.join('\n')
}

/** @deprecated Usar getStepGuideMessage */
export function getStepWelcomeMessage(step: number, claimId: string | null): string {
  return getStepGuideMessage(step, claimId)
}

export function getStepQuickQuestions(step: number, claimId: string | null): string[] {
  const ctx = getStepContext(step)
  const hints = [...ctx.hints]

  if (claimId) {
    if (step === 2) {
      hints.unshift(`Resume el caso ${claimId} en esta etapa.`)
    } else if (step === 3) {
      hints.unshift(`¿Por qué el caso ${claimId} tiene este puntaje?`)
    } else if (step === 4) {
      hints.unshift(`¿Qué relaciones tiene el caso ${claimId}?`)
    } else if (step === 5) {
      hints.unshift(`Genera el reporte del caso ${claimId}.`)
    } else if (step >= 1) {
      hints.unshift(`¿Qué debo revisar del caso ${claimId} aquí?`)
    }
  }

  return hints.slice(0, 5)
}
