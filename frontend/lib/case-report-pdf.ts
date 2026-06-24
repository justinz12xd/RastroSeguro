import type { jsPDF } from 'jspdf'
import { formatCurrency } from '@/lib/claims-data'
import { UI_COPY } from '@/lib/human-labels'
import type { CaseReportData } from '@/lib/case-report-export'

const MARGIN = 16
const FOOTER_H = 14
const PAGE_W = 210
const CONTENT_W = PAGE_W - MARGIN * 2
const LINE = 5.2

type RGB = [number, number, number]

const BRAND: RGB = [30, 64, 175]
const SLATE_900: RGB = [15, 23, 42]
const SLATE_700: RGB = [51, 65, 85]
const SLATE_500: RGB = [100, 116, 139]
const SLATE_100: RGB = [241, 245, 249]
const SLATE_50: RGB = [248, 250, 252]
const WHITE: RGB = [255, 255, 255]

function asRgb(rgb: RGB): RGB {
  return [rgb[0], rgb[1], rgb[2]]
}

function pageHeight(doc: jsPDF) {
  return doc.internal.pageSize.getHeight()
}

function setColor(doc: jsPDF, rgb: RGB) {
  doc.setTextColor(rgb[0], rgb[1], rgb[2])
}

function setFill(doc: jsPDF, rgb: RGB) {
  doc.setFillColor(rgb[0], rgb[1], rgb[2])
}

function riskAccent(label: string): RGB {
  const v = label.toLowerCase()
  if (v.includes('crít') || v.includes('crit') || v.includes('rojo') || v.includes('alto')) return [220, 38, 38]
  if (v.includes('med') || v.includes('amar')) return [217, 119, 6]
  if (v.includes('baj') || v.includes('verde')) return [22, 163, 74]
  return BRAND
}

function wrapText(doc: jsPDF, text: string, x: number, y: number, maxW: number, lineH = LINE): number {
  const lines = doc.splitTextToSize(text, maxW) as string[]
  doc.text(lines, x, y)
  return y + lines.length * lineH
}

function ensureSpace(doc: jsPDF, y: number, needed: number): number {
  const limit = pageHeight(doc) - FOOTER_H - 4
  if (y + needed > limit) {
    doc.addPage()
    return MARGIN + 10
  }
  return y
}

function drawFooters(doc: jsPDF, claimId: string) {
  const total = doc.getNumberOfPages()
  for (let i = 1; i <= total; i++) {
    doc.setPage(i)
    const h = pageHeight(doc)
    setFill(doc, SLATE_100)
    doc.rect(0, h - FOOTER_H, PAGE_W, FOOTER_H, 'F')
    doc.setDrawColor(SLATE_100[0], SLATE_100[1], SLATE_100[2])
    doc.setLineWidth(0.3)
    doc.line(MARGIN, h - FOOTER_H, PAGE_W - MARGIN, h - FOOTER_H)
    doc.setFontSize(7.5)
    doc.setFont('helvetica', 'normal')
    setColor(doc, SLATE_500)
    doc.text('RastroSeguro · Reporte de caso · Solo apoyo a revisión humana', MARGIN, h - 5.5)
    doc.text(`${claimId} · Pág. ${i} de ${total}`, PAGE_W - MARGIN, h - 5.5, { align: 'right' })
  }
}

function drawRunningHeader(doc: jsPDF, claimId: string) {
  setFill(doc, BRAND)
  doc.rect(0, 0, PAGE_W, 10, 'F')
  doc.setFontSize(8)
  doc.setFont('helvetica', 'bold')
  setColor(doc, WHITE)
  doc.text('RastroSeguro', MARGIN, 6.5)
  doc.setFont('helvetica', 'normal')
  doc.text(`Caso ${claimId}`, PAGE_W - MARGIN, 6.5, { align: 'right' })
}

function drawCover(doc: jsPDF, data: CaseReportData): number {
  setFill(doc, BRAND)
  doc.rect(0, 0, PAGE_W, 42, 'F')

  doc.setFont('helvetica', 'bold')
  doc.setFontSize(22)
  setColor(doc, WHITE)
  doc.text('Reporte de caso', MARGIN, 18)

  doc.setFontSize(11)
  doc.setFont('helvetica', 'normal')
  doc.text('RastroSeguro · Unidad de inteligencia de riesgo', MARGIN, 26)

  doc.setFontSize(9)
  doc.text(`Generado: ${data.generatedAt}`, MARGIN, 34)

  let y = 52

  setFill(doc, SLATE_50)
  doc.setDrawColor(BRAND[0], BRAND[1], BRAND[2])
  doc.setLineWidth(0.4)
  doc.roundedRect(MARGIN, y, CONTENT_W, 22, 2, 2, 'FD')

  doc.setFont('helvetica', 'bold')
  doc.setFontSize(9)
  setColor(doc, SLATE_500)
  doc.text('IDENTIFICADOR', MARGIN + 5, y + 7)
  doc.text('RAMO / COBERTURA', MARGIN + 55, y + 7)
  doc.text('MONTO RECLAMADO', MARGIN + 120, y + 7)

  doc.setFontSize(11)
  setColor(doc, SLATE_900)
  doc.text(data.claimId, MARGIN + 5, y + 14)
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(9)
  setColor(doc, SLATE_700)
  doc.text(`${data.ramo} · ${data.cobertura}`, MARGIN + 55, y + 14)
  doc.setFont('helvetica', 'bold')
  setColor(doc, SLATE_900)
  doc.text(data.montoReclamado, MARGIN + 120, y + 14)

  return y + 30
}

function drawScoreHero(doc: jsPDF, data: CaseReportData, y: number): number {
  y = ensureSpace(doc, y, 38)
  const accent = riskAccent(data.nivelRiesgo)
  const boxH = 34

  setFill(doc, SLATE_50)
  doc.setDrawColor(accent[0], accent[1], accent[2])
  doc.setLineWidth(0.6)
  doc.roundedRect(MARGIN, y, CONTENT_W, boxH, 2, 2, 'FD')
  setFill(doc, accent)
  doc.rect(MARGIN, y, 3, boxH, 'F')

  doc.setFont('helvetica', 'bold')
  doc.setFontSize(28)
  setColor(doc, SLATE_900)
  doc.text(String(Math.round(data.scoreFinal)), MARGIN + 10, y + 18)

  doc.setFontSize(9)
  setColor(doc, SLATE_500)
  doc.text('/ 100', MARGIN + 10 + doc.getTextWidth(String(Math.round(data.scoreFinal))) + 1, y + 18)

  doc.setFontSize(8)
  doc.text('PUNTAJE DEL CASO', MARGIN + 10, y + 8)

  const badgeX = MARGIN + 48
  setFill(doc, accent)
  doc.roundedRect(badgeX, y + 8, 36, 8, 1.5, 1.5, 'F')
  doc.setFontSize(8)
  doc.setFont('helvetica', 'bold')
  setColor(doc, WHITE)
  doc.text(data.nivelRiesgo.toUpperCase(), badgeX + 18, y + 13.5, { align: 'center' })

  doc.setFont('helvetica', 'bold')
  doc.setFontSize(9)
  setColor(doc, SLATE_700)
  doc.text('Recomendación', badgeX, y + 22)
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(8.5)
  setColor(doc, SLATE_700)
  wrapText(doc, data.accion, badgeX, y + 27, CONTENT_W - (badgeX - MARGIN) - 4, 4)

  return y + boxH + 8
}

function drawSectionHeader(doc: jsPDF, number: number, title: string, y: number): number {
  y = ensureSpace(doc, y, 16)
  setFill(doc, BRAND)
  doc.circle(MARGIN + 4, y - 1.5, 4, 'F')
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(9)
  setColor(doc, WHITE)
  doc.text(String(number), MARGIN + 4, y + 0.5, { align: 'center' })

  doc.setFontSize(12)
  setColor(doc, SLATE_900)
  doc.text(title, MARGIN + 12, y)

  doc.setDrawColor(SLATE_100[0], SLATE_100[1], SLATE_100[2])
  doc.setLineWidth(0.5)
  doc.line(MARGIN, y + 3, PAGE_W - MARGIN, y + 3)

  return y + 10
}

function drawSubsection(doc: jsPDF, step: number, title: string, y: number): number {
  y = ensureSpace(doc, y, 12)
  setFill(doc, SLATE_100)
  doc.roundedRect(MARGIN, y - 5, CONTENT_W, 8, 1, 1, 'F')
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(9)
  setColor(doc, BRAND)
  doc.text(`Paso ${step}`, MARGIN + 3, y)
  setColor(doc, SLATE_900)
  doc.text(title, MARGIN + 22, y)
  return y + 6
}

function drawKeyValueGrid(doc: jsPDF, pairs: [string, string][], y: number): number {
  const colW = CONTENT_W / 2 - 2
  let rowY = y
  for (let i = 0; i < pairs.length; i += 2) {
    rowY = ensureSpace(doc, rowY, 14)
    for (let col = 0; col < 2 && i + col < pairs.length; col++) {
      const [label, value] = pairs[i + col]
      const x = MARGIN + col * (colW + 4)
      doc.setFont('helvetica', 'bold')
      doc.setFontSize(7.5)
      setColor(doc, SLATE_500)
      doc.text(label.toUpperCase(), x, rowY)
      doc.setFont('helvetica', 'normal')
      doc.setFontSize(9)
      setColor(doc, SLATE_700)
      wrapText(doc, value, x, rowY + 4, colW, 4)
    }
    rowY += 12
  }
  return rowY + 2
}

function drawBullets(doc: jsPDF, items: string[], y: number): number {
  for (const item of items) {
    const lines = doc.splitTextToSize(item, CONTENT_W - 8) as string[]
    y = ensureSpace(doc, y, lines.length * LINE + 2)
    setFill(doc, BRAND)
    doc.circle(MARGIN + 2, y - 1.2, 0.8, 'F')
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(9)
    setColor(doc, SLATE_700)
    doc.text(lines, MARGIN + 6, y)
    y += lines.length * LINE + 2
  }
  return y + 2
}

function drawCallout(doc: jsPDF, label: string, text: string, y: number, accent: RGB = BRAND): number {
  const lines = doc.splitTextToSize(text, CONTENT_W - 12) as string[]
  const boxH = 8 + lines.length * 4.2
  y = ensureSpace(doc, y, boxH + 4)

  setFill(doc, SLATE_50)
  doc.setDrawColor(accent[0], accent[1], accent[2])
  doc.setLineWidth(0.3)
  doc.roundedRect(MARGIN, y, CONTENT_W, boxH, 1.5, 1.5, 'FD')
  setFill(doc, accent)
  doc.rect(MARGIN, y, 2.5, boxH, 'F')

  doc.setFont('helvetica', 'bold')
  doc.setFontSize(8)
  setColor(doc, accent)
  doc.text(label.toUpperCase(), MARGIN + 6, y + 5)
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(8.5)
  setColor(doc, SLATE_700)
  doc.text(lines, MARGIN + 6, y + 10)

  return y + boxH + 5
}

function drawContributionTable(doc: jsPDF, data: CaseReportData, y: number, autoTable: typeof import('jspdf-autotable').default): number {
  y = ensureSpace(doc, y, 24)
  autoTable(doc, {
    startY: y,
    head: [[UI_COPY.whatInfluenced, 'Valor', UI_COPY.weight, UI_COPY.contribution]],
    body: data.rows.map((r) => [r.label, String(Math.round(r.value)), `${r.weightPct}%`, String(r.contribution)]),
    margin: { left: MARGIN, right: MARGIN, top: MARGIN + 10, bottom: FOOTER_H + 4 },
    styles: { fontSize: 8.5, cellPadding: 2.5, textColor: asRgb(SLATE_700), lineColor: asRgb(SLATE_100), lineWidth: 0.2 },
    headStyles: { fillColor: asRgb(BRAND), textColor: asRgb(WHITE), fontStyle: 'bold', fontSize: 8.5 },
    alternateRowStyles: { fillColor: asRgb(SLATE_50) },
    columnStyles: {
      0: { cellWidth: 62 },
      1: { halign: 'center', cellWidth: 22 },
      2: { halign: 'center', cellWidth: 22 },
      3: { halign: 'center', cellWidth: 28 },
    },
    didDrawPage: (hookData) => {
      if (hookData.pageNumber > 1) drawRunningHeader(doc, data.claimId)
    },
  })
  return (doc as jsPDF & { lastAutoTable?: { finalY: number } }).lastAutoTable?.finalY ?? y
}

function drawPortfolioKpis(doc: jsPDF, data: CaseReportData, y: number, autoTable: typeof import('jspdf-autotable').default): number {
  const s = data.portfolioReport!.summary
  y = ensureSpace(doc, y, 20)
  autoTable(doc, {
    startY: y,
    head: [['Indicador', 'Valor']],
    body: [
      ['Total siniestros en cartera', s.total_siniestros.toLocaleString('es-EC')],
      ['Casos rojos', `${s.casos_rojos.toLocaleString('es-EC')} (${s.porcentaje_rojo}%)`],
      ['Monto en casos rojos', formatCurrency(s.monto_reclamado_casos_rojos)],
    ],
    margin: { left: MARGIN, right: MARGIN, bottom: FOOTER_H + 4 },
    styles: { fontSize: 9, cellPadding: 3, textColor: asRgb(SLATE_700) },
    headStyles: { fillColor: asRgb(SLATE_700), textColor: asRgb(WHITE), fontStyle: 'bold' },
    columnStyles: { 0: { cellWidth: 80 }, 1: { halign: 'right' } },
    didDrawPage: (hookData) => {
      if (hookData.pageNumber > 1) drawRunningHeader(doc, data.claimId)
    },
  })
  return (doc as jsPDF & { lastAutoTable?: { finalY: number } }).lastAutoTable?.finalY ?? y
}


function drawChatSummary(doc: jsPDF, data: CaseReportData, y: number): number {
  if (!data.chatSummary.length) return y

  y = ensureSpace(doc, y, 14)
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(8.5)
  setColor(doc, SLATE_500)
  y = wrapText(
    doc,
    'Solo se incluyen preguntas y respuestas asociadas al siniestro de este reporte. Conversaciones de otros casos no se agregan.',
    MARGIN,
    y,
    CONTENT_W,
    4,
  ) + 2

  data.chatSummary.forEach((item, index) => {
    const question = `${index + 1}. Pregunta: ${item.question}`
    const answer = `Respuesta: ${item.answer}`
    const questionLines = doc.splitTextToSize(question, CONTENT_W - 10) as string[]
    const answerLines = doc.splitTextToSize(answer, CONTENT_W - 10) as string[]
    const boxH = 8 + (questionLines.length + answerLines.length) * 4.2
    y = ensureSpace(doc, y, boxH + 4)

    setFill(doc, SLATE_50)
    doc.setDrawColor(SLATE_100[0], SLATE_100[1], SLATE_100[2])
    doc.setLineWidth(0.3)
    doc.roundedRect(MARGIN, y, CONTENT_W, boxH, 1.5, 1.5, 'FD')

    doc.setFont('helvetica', 'bold')
    doc.setFontSize(8.5)
    setColor(doc, SLATE_900)
    doc.text(questionLines, MARGIN + 5, y + 6)

    doc.setFont('helvetica', 'normal')
    doc.setFontSize(8.2)
    setColor(doc, SLATE_700)
    doc.text(answerLines, MARGIN + 5, y + 6 + questionLines.length * 4.2 + 3)

    y += boxH + 4
  })

  return y
}

function drawDisclaimer(doc: jsPDF, y: number): number {
  y = ensureSpace(doc, y, 20)
  setFill(doc, [254, 252, 232])
  doc.setDrawColor(217, 119, 6)
  doc.setLineWidth(0.4)
  const text =
    'Documento generado por RastroSeguro. Este resultado solo apoya la revisión humana. No acusa fraude ni rechaza reclamos automáticamente.'
  const lines = doc.splitTextToSize(text, CONTENT_W - 10) as string[]
  const boxH = 10 + lines.length * 4
  doc.roundedRect(MARGIN, y, CONTENT_W, boxH, 2, 2, 'FD')
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(8)
  setColor(doc, [146, 64, 14])
  doc.text('AVISO IMPORTANTE', MARGIN + 5, y + 6)
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(8)
  setColor(doc, SLATE_700)
  doc.text(lines, MARGIN + 5, y + 11)
  return y + boxH + 4
}

export async function renderCaseReportPdf(data: CaseReportData): Promise<jsPDF> {
  const [{ jsPDF }, autoTableModule] = await Promise.all([import('jspdf'), import('jspdf-autotable')])
  const autoTable = autoTableModule.default
  const doc = new jsPDF({ unit: 'mm', format: 'a4' })

  let y = drawCover(doc, data)
  y = drawScoreHero(doc, data, y)

  if (data.explicacion) {
    y = drawCallout(doc, 'Explicación del caso', data.explicacion, y)
  }

  y = drawSectionHeader(doc, 1, UI_COPY.scoreObjective, y)
  y = drawContributionTable(doc, data, y, autoTable) + 8

  y = drawSectionHeader(doc, 2, 'Recorrido por etapas', y)

  y = drawSubsection(doc, 1, 'Carga de datos', y)
  y = drawKeyValueGrid(doc, [
    ['Archivo', data.uploadedFileName || 'Cartera activa en el sistema'],
    ['Casos en sesión', String(data.claimsCount)],
  ], y)

  y = drawSubsection(doc, 2, 'Resumen del caso', y)
  y = drawKeyValueGrid(doc, [
    ['Ramo', data.ramo],
    ['Cobertura', data.cobertura],
    ['Monto reclamado', data.montoReclamado],
    ['Documentos', data.documentosCompletos ? 'Completos' : 'Pendiente o incompleto'],
  ], y)

  y = drawSubsection(doc, 3, 'Resultado y motivos', y)
  y = drawBullets(doc, data.alertas.length ? data.alertas.slice(0, 6) : ['Sin alertas principales registradas.'], y)

  y = drawSubsection(doc, 4, 'Conexiones y gráficos', y)
  y = drawCallout(doc, 'Red del caso', data.insights.graph, y)
  y = drawCallout(doc, 'Recurrencias', data.insights.recurrence, y, [22, 163, 74])
  y = drawCallout(doc, 'Comparación con la cartera', data.insights.spider, y, [124, 58, 237])

  if (data.dossier) {
    y = drawSectionHeader(doc, 3, 'Evidencias del expediente', y)
    if (data.dossier.headline) y = drawCallout(doc, 'Resumen', data.dossier.headline, y)
    const evidence = data.dossier.evidence?.slice(0, 6) ?? []
    if (evidence.length) {
      y = ensureSpace(doc, y, 12)
      doc.setFont('helvetica', 'bold')
      doc.setFontSize(8)
      setColor(doc, SLATE_500)
      doc.text('SEÑALES DOCUMENTADAS', MARGIN, y)
      y += 5
      y = drawBullets(
        doc,
        evidence.map((e, i) => `${i + 1}. ${e.senal || e.codigo}: ${e.mensaje || ''} (+${Math.round(Number(e.puntos ?? 0))} pts)`),
        y,
      )
    }
    if (data.dossier.ethical_guardrail) y = drawCallout(doc, 'Marco ético', data.dossier.ethical_guardrail, y, SLATE_700)
  }

  if (data.chatSummary.length) {
    y = drawSectionHeader(doc, data.dossier ? 4 : 3, 'Resumen del chat sobre este siniestro', y)
    y = drawChatSummary(doc, data, y)
  }

  if (data.portfolioReport?.summary) {
    y = drawSectionHeader(doc, data.dossier ? (data.chatSummary.length ? 5 : 4) : (data.chatSummary.length ? 4 : 3), 'Contexto del portafolio', y)
    y = drawPortfolioKpis(doc, data, y, autoTable) + 6
    if (data.portfolioReport.ethics_note) y = drawCallout(doc, 'Nota de cartera', data.portfolioReport.ethics_note, y)
  }

  drawDisclaimer(doc, y)
  drawFooters(doc, data.claimId)

  return doc
}

export async function downloadCaseReportPdfFromData(data: CaseReportData): Promise<void> {
  const doc = await renderCaseReportPdf(data)
  doc.save(`reporte-demo-${data.claimId}.pdf`)
}
