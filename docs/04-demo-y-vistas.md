# Demo y vistas de la aplicación

Este documento reduce el alcance visual sin eliminar funcionalidades avanzadas.

## Decisión

```txt
Menos páginas independientes.
Más tabs internas por página.
```

Así Justin puede construir una app clara sin duplicar pantallas.

## Vista 1 — Dashboard

Objetivo: mostrar valor ejecutivo rápido.

Tabs sugeridas:

- Resumen general.
- Riesgo por ramo.
- Ciudades y proveedores.
- Métricas del modelo.

Debe mostrar:

- Total de siniestros.
- Casos verdes, amarillos y rojos.
- Monto total reclamado.
- Monto en casos rojos.
- Distribución de riesgo.
- Top proveedores y ciudades.

## Vista 2 — Revisión de siniestros

Objetivo: priorizar y explicar casos.

Tabs sugeridas:

- Bandeja priorizada.
- Detalle del siniestro.
- Explicación del score.
- Documentos y alertas.

Debe consumir:

- `data/processed/siniestros_scored.csv`.
- `explain_claim(id_siniestro)`.

## Vista 3 — Inteligencia antifraude

Objetivo: mostrar diferenciadores técnicos.

Tabs sugeridas:

- Narrativas similares.
- Grafo de relaciones.
- Ranking de proveedores.
- Comparación multi-ramo.

Nota: el grafo no tiene que ser complejo al inicio. Puede empezar como red del caso seleccionado y rankings de concentración.

## Vista 4 — Agente y simulador

Objetivo: demostrar interacción inteligente y evaluación en vivo.

Tabs sugeridas:

- Chat antifraude.
- Preguntas rápidas.
- Simulador de nuevo siniestro.
- RAG documental.

El agente debe usar herramientas reales. El simulador debe calcular score y explicación con los mismos módulos de Jeremy.

## Vista 5 — Reporte / demo

Objetivo: facilitar pitch y cierre ejecutivo.

**Paso 5 en la app (analista y ejecutivo):** pantalla `step-case-closure` con pestañas **Reporte** y **Expediente**.

- **Reporte:** score objetivo desglosado (pesos 30/25/15/15/10/5), recorrido por etapas 1–4, gráficos explicados, contexto portafolio, guion demo y exportación `.md`.
- **Expediente:** ficha antifraude completa (`step-dossier` embebido).

El chat lateral (desktop) usa preguntas rápidas contextualizadas por paso (`demo-step-context.ts`).

Tabs sugeridas (vista conceptual):

- Resumen ejecutivo.
- Casos estrella.
- Exportar reporte.
- Guion de demo.

No usar “modo jurado” como concepto formal de producto. Si se necesitan accesos rápidos para la presentación, llamarlos “casos estrella” o “demo ejecutiva”.

## Casos estrella

- Rojo evidente: muchas reglas críticas activadas.
- Rojo no evidente: anomalía, grafo o narrativa lo elevan.
- Amarillo ético: señales moderadas, revisión documental.
- Proveedor recurrente: concentración de alertas.
- Narrativa similar: reclamos con textos parecidos.
- Simulación en vivo: nuevo caso evaluado durante la demo.

## Implementación de diferenciadores para destacar

Se agregaron dos secciones explícitas al frontend Next.js (`frontend/`):

### Expediente antifraude

Convierte un siniestro seleccionado en una ficha investigativa con:

- Score, nivel de riesgo y decisión automática = No.
- Evidencias trazables ordenadas por puntaje.
- Principal componente que explica el riesgo.
- Señales de NLP y grafo cuando existen.
- Próximos pasos de revisión humana.
- Guardrail ético visible: alerta de priorización, no acusación.

### Demo ejecutiva

Vista preparada para el pitch y preguntas del jurado con:

- Casos estrella: rojo evidente, rojo no evidente, amarillo ético, proveedor recurrente y narrativa similar.
- Impacto de negocio como exposición priorizada del top 10%, sin presentarlo como ahorro automático.
- Guion sugerido de demo en vivo.

El agente también reconoce consultas sobre expediente antifraude, casos estrella e impacto de negocio usando herramientas determinísticas sobre `data/processed/siniestros_scored.csv`. Estas capacidades se exponen al frontend mediante FastAPI: `/api/claims/{id_siniestro}/dossier`, `/api/reports/star-cases` y `/api/reports/business-impact`.

## Guion demo jurado (PDF §23.2)

1. **Consulta agéntica:** *"¿Qué proveedores concentran el 80% de las alertas rojas?"*
2. **Prueba de score:** simular siniestro 24 h después de la póliza → explicar RF-05 y semáforo.
3. **Verificación repositorio:** mostrar `src/rules/`, `docs/arquitectura.md`, `docs/uso_ia.md`, `validate_deliverables`.
4. **Ahorro potencial:** Command Center → KPI ahorro estimado + reporte ejecutivo.
5. **Auditoría:** `GET /api/report/audit?format=markdown`
6. **Expediente y casos estrella:** vistas `step-dossier` y `step-executive-demo`.
