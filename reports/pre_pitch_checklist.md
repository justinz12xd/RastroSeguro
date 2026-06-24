# Checklist pre-pitch (PDF completo)

## Dataset PDF §6.1
- [x] `data/synthetic/siniestros.csv` con `monto_pagado`, `estado`, `sucursal`
- [x] Vehículo: `placa_hash`, `chasis_hash`, `motor_hash`, marca, modelo, año
- [x] QA: `data/synthetic/siniestros_qa.json` con `ok=true`

## Tablas complementarias §6.2
- [x] `data/synthetic/polizas.csv`
- [x] `data/synthetic/asegurados.csv`
- [x] `data/synthetic/proveedores.csv`
- [x] `data/synthetic/documentos.csv`
- [x] `data/synthetic/dataset_manifest.json`

## Motor antifraude
- [x] Reglas RF-01…RF-07 documentadas en `docs/reglas_negocio.md`
- [x] RF-02 explícito en trazas críticas
- [x] NLP alineado PDF: ≥85% → 8 pts, 70–84% → 4 pts
- [x] Score híbrido + semáforo Verde/Amarillo/Rojo
- [x] Agente responde 12 preguntas del PDF
- [x] Consulta jurado: 80% alertas rojas en proveedores

## Funcionalidades deseables §10.2
- [x] Simulación de ahorro potencial
- [x] Exportación reporte auditoría (`GET /api/report/audit`)
- [x] API FastAPI funcional

## Artefactos
- [x] Features, modelos `.joblib`, métricas, casos estrella
- [x] Benchmark 12 preguntas: `reports/benchmark_preguntas_pdf.json`
- [x] Scoring: `data/processed/siniestros_scored.csv`

## Documentación PDF §14–§15
- [x] README actualizado
- [x] `docs/arquitectura.md`, `docs/uso_ia.md`
- [x] `docs/reglas_negocio.md`, `docs/modelo_datos.md`, `docs/limitaciones.md`
- [x] Notebooks `01`, `02`, `03`
- [x] `presentation/pitch.md`

## R y Oracle §16
- [x] `r/01_validacion_metricas.R`, `r/02_exploracion_siniestros.Rmd`
- [x] `db/oracle/schema.sql`, `docker/oracle-xe/`

## Guardrails éticos
- Alertas de revisión, no acusaciones automáticas
- Datos sintéticos sin PII real
- Revisión humana obligatoria antes de decisiones

## Demo jurado §23.2
1. Pregunta agente: proveedores con 80% alertas rojas
2. Simulador: siniestro 24h después de póliza → RF-05
3. Mostrar `rule_trace` + semáforo en UI
