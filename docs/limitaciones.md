# Limitaciones del prototipo

## Datos

- Los siniestros son **100% sintéticos**; no representan casos reales de asegurados.
- Ecuador aporta contexto público (SERCOP, OCDS, ECU911, INEC), no microdatos de siniestros asegurados.
- No hay PII real; identificadores de vehículo usan hashes (`placa_hash`, `chasis_hash`, `motor_hash`).

## Modelo

- Métricas altas reflejan datos sintéticos con señales inyectadas; no garantizan performance en producción.
- El detector de anomalías puede marcar casos normales en portafolios reales (falsos positivos).
- NLP de similitud depende de `descripcion`; reclamos muy cortos reducen precisión.
- La simulación de ahorro potencial es una **estimación ilustrativa**, no un ahorro garantizado.

## Decisiones

- El sistema **no acusa fraude** ni rechaza pagos automáticamente.
- Toda escalación requiere **revisión humana**.
- El score es una priorización explicable, no una conclusión legal.

## Alcance técnico

- **Runtime principal**: Python + CSV (`data/synthetic/`, `data/processed/`).
- **API REST**: FastAPI en `api/main.py` — `uvicorn api.main:app --reload --port 8000`.
- **UI**: Next.js (`frontend/`) consumiendo la API FastAPI.
- **R**: scripts de validación reproducible en `r/`; no integrados en el pipeline de scoring.
- **Oracle**: esquema DDL y Docker XE de referencia en `db/oracle/`; Postgres/Supabase para analítica cloud.
- LLM opcional desactivado por defecto (`RASTRO_LLM_ENABLED=false`); el agente funciona de forma determinística sin API externa.
