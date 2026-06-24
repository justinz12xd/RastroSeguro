# Backend `src/` + `api/` — Análisis de Arquitectura Limpia

> Estado: **REFACTOR COMPLETO** — Fases 0–4 aplicadas. Quedan solo recomendaciones §5 (DI con `Depends`, DB real, CI).
> Baseline verificado tras cambios: `import api.main` OK · **120 tests pasan** · contratos import-linter **KEPT**.
> Regla rectora: **no cambiar comportamiento del producto**. Solo estructura, modularidad, dead code.

### Progreso aplicado (verificado, 120 tests verdes)

- **Fase 0 — Dead code:** eliminado lo de §3.1 (`generate_executive_report_markdown`,
  `compare_branches`, import `simulate_new_claim`, `ApiEnvelope`, `SimulatorClaimRequest`,
  `ReportResponseFormat`, var `min_len`, import `np`).
- **Fase 1 — Config/persistencia:**
  - `src/infrastructure/config/paths.py` posee las rutas canónicas; `scoring/final_score.py`
    re-exporta `INPUT_PATH`/`OUTPUT_PATH` (back-compat, callers intactos).
  - `src/infrastructure/repositories/scored_claims_repository.py` (`ScoredClaimsRepository`)
    encapsula `read/read_or_empty/save/exists`. Adoptado por rutas y por `tools._load_scored`
    (único punto de lectura del CSV; se conserva el cache por mtime y la patchabilidad de tests).
- **Fase 2 — Capa de aplicación (COMPLETA):**
  - `_rescore_with_population` → `src/application/claims/rescore_portfolio.py`. La ruta queda
    como adaptador fino (se conserva el nombre `_rescore_with_population` para el patch de tests).
  - Orquestación de `chat_agent` → `src/application/agent/chat_service.py::run_chat`, con
    **inyección de dependencias** (`store`, `answer_fn`, `extract_claim_id`) → resuelve parte de
    S8 y mantiene los patch points (`api.routes.agent.answer_question`) de los tests.
  - **Split de `tools.py` (S2):** el god-facade se movió a `src/application/risk_queries.py`
    (hogar canónico de las read-queries sobre el portafolio). `src/agent/tools.py` queda como
    **shim** que re-exporta. Los callers de primera mano (`antifraud_agent`, `quick_questions`,
    `explain_claim`, rutas `claims`/`reports`, `build_pdf_benchmark`) ahora importan
    `from src.application import risk_queries as tools`, de modo que los parches internos
    (`_load_scored`) resuelven correctamente. Se actualizaron 9 patch targets en
    `tests/test_agent.py` a `src.application.risk_queries.*` (los de `test_api_bridge.py`
    siguen vía el alias de módulo `tools` en las rutas, sin cambios).
- **Fase 3 — Packaging (S7):**
  - Tooling offline movido a `pipelines/`: `pipelines/ingestion/`, `pipelines/models/` (todo
    `src/ingestion` y `src/models`) y `pipelines/data/` (los 7 módulos offline de `src/data`:
    `claim_signals`, `demo_scenarios`, `ecuador_context`, `export_complementary_tables`,
    `export_features`, `generate_synthetic_data`, `qa_metrics`). `src/data` conserva solo el
    hot-path (`feature_engineering`, `portfolio_stats`). Imports reescritos (código, 3 tests y
    el string de error de `final_score`); docs actualizadas a `python -m pipelines.*`.
  - `pyproject.toml` añadido (aditivo, `requirements.txt` intacto para deploy): deps runtime vs
    `optional-dependencies` `pipelines` (`beautifulsoup4`, `openpyxl`) y `dev`
    (`pytest`, `httpx`, `ruff`, `vulture`, `import-linter`). Config de `ruff`, `vulture` e
    `import-linter`.
  - **Contratos import-linter (§5.3) verdes:** "deployed code (api/src) no importa `pipelines`"
    y "`src.infrastructure` no importa `api`" → ambos **KEPT** (131 archivos analizados).
- **Fase 4 — Cohesión de `agent/` (S6):**
  - `src/agent/llm/*` → `src/infrastructure/llm/*` (provider Strategy: `base`, `openai_provider`,
    `disabled_provider`, `settings`, `prompts`, `build_llm_provider`).
  - `ChatHistoryStore` (SQLite) → `src/infrastructure/chat/chat_history.py` (con `__init__`
    que re-exporta `ChatHistoryStore`).
  - Consumidores actualizados: `antifraud_agent` (`from src.infrastructure.llm import …`),
    `api/routes/agent.py` (`from src.infrastructure.chat.chat_history import ChatHistoryStore`),
    tests `test_agent_llm.py` y `test_agent.py` (incl. patch `src.infrastructure.llm.openai_provider._post_json`).
  - `src/agent/` queda cohesivo con el **dominio del agente** (router, intents, entities,
    responses, rag, langgraph_runtime, quick_questions, antifraud_agent) + el shim `tools.py`.
    El orquestador de chat ya vive en `application/agent/chat_service.py` (Fase 2).

El producto en runtime es `api.main:app` (gunicorn/uvicorn, ver `startup.sh`). Todo lo
alcanzable desde ahí es **hot path** e intocable en comportamiento. El resto (scrapers,
entrenamiento, generadores de datos) es **tooling offline**.

---

## 1. Diagnóstico de la arquitectura actual

### 1.1 Mapa de capas real (medido, no asumido)

Reachability desde `api.main` (AST import graph):

- **Hot path producto (~69 módulos):** `agent/*`, `rules/*`, `scoring/*`, `nlp/*`,
  `graph/*`, `categorical/*`, `model_integration/*`, `explainability/explain_claim`,
  `documents/claim_extraction`, `simulator/*`, `reports/*` (subset), `data/feature_engineering`,
  `data/portfolio_stats`, `utils/*`.
- **Solo usado por tests:** `data/{claim_signals,demo_scenarios,ecuador_context,export_*,generate_synthetic_data,qa_metrics}`,
  `ingestion/{build_agent_ready_dataset,model_curated_dataset}`, `models/*` (training).
- **Offline / no en producto ni tests:** `ingestion/{scrape_ecuador,boost_ocds_sercop,package_ecuador_datasets,sources}`,
  `models/{run_carlos_pipeline,validate_deliverables}`.

### 1.2 Smells de acoplamiento (verificados)

| # | Problema | Evidencia | Impacto |
|---|----------|-----------|---------|
| S1 | **Fat controllers**: lógica de negocio dentro de la capa de transporte | `api/routes/claims.py::_rescore_with_population` (pandas read/concat/dedup/score/write); `api/routes/agent.py::chat_agent` ~100 líneas orquestando store+agente+secciones | Rutas no testeables sin HTTP; lógica duplicable; difícil de reusar |
| S2 | **God-facade `src/agent/tools.py`** (278 LOC, 21 funciones) | Expone claims, ranking proveedores, riesgo por ciudad/ramo, dossier, star cases, business impact, savings, fraud rings. Lo consumen `claims.py` **y** `reports.py`, no solo el agente | Alto fan-in; mezcla data-access + agregación + presentación; nombre engañoso ("tools" del agente) |
| S3 | **Sin abstracción de persistencia**: el "DB" es un CSV global | `OUTPUT_PATH` (de `src/scoring/final_score.py`) importado en rutas/tools; `pd.read_csv/to_csv` directo en handlers | Dominio e interfaz acoplados a formato+ruta de archivo |
| S4 | **Constante de infra vive en módulo de dominio** | `OUTPUT_PATH` definido en `scoring/final_score.py` y reimportado por todos | Inversión de dependencias rota: dominio "posee" detalle de infra |
| S5 | **Escritura de CSV en request bajo threads** | `startup.sh` corre `--threads 4`; `_rescore_with_population` y upload escriben el CSV | Riesgo latente de corrupción/carrera (se documenta; **no** se cambia ahora) |
| S6 | **Paquete `agent/` mezcla 4 responsabilidades** | LLM provider, persistencia SQLite (`ChatHistoryStore`), routing/intents, data-access (`tools`) en un solo paquete | Baja cohesión; cambios en LLM tocan el mismo paquete que el data-access |
| S7 | **Scripts offline mezclados con la librería runtime** | `ingestion/`, `models/`, `data/generate_*` bajo `src/` junto al dominio importable | Infla superficie de import y la imagen de deploy; no distingue "desplegado" de "dev-only" |
| S8 | **Sin DI**: dependencias instanciadas dentro del handler | `_chat_store()` crea `ChatHistoryStore()` por request | No inyectable/mockeable; imposible cambiar backend sin tocar la ruta |

### 1.3 Lo que YA está bien (preservar)

- `rules/` está bien modularizado: `rule_registry` + reglas por ramo + `common/`.
- `agent/llm/` con `base.py` (interfaz) + providers (`openai`, `disabled`) → patrón Strategy correcto.
- `api/routes/_errors.py::run_endpoint` centraliza traducción de errores → buen seam.
- `api/schemas.py::json_safe` resuelve NaN→null en un solo punto.

---

## 2. Estructura de carpetas propuesta (objetivo)

Migración **gradual**, no big-bang. Cada caja existe ya como código disperso; se reubica.

```
src/
  domain/                  # lógica pura de negocio, SIN IO ni framework
    rules/                 # ← src/rules/*           (ya cohesivo)
    scoring/               # ← algoritmos de score (final_score sin IO)
    graph/  nlp/  categorical/  explainability/
    valueobjects.py        # ← rules/models.py
  application/             # casos de uso: orquestan dominio, sin framework
    claims/                # rescore_portfolio, ingest_csv, confirm_document
    risk_queries/          # ← lo "read" de tools.py (top risky, rankings, dossier…)
    reports/               # executive, audit, savings
    agent/                 # chat_service (extraído de la ruta)
  infrastructure/          # IO, persistencia, servicios externos
    config/paths.py        # ← OUTPUT_PATH y rutas de datos viven AQUÍ
    repositories/          # ScoredClaimsRepository (CSV hoy, swappable)
    chat/                  # ← ChatHistoryStore (SQLite)
    llm/                   # ← agent/llm/*
api/                       # interfaces: controladores FINOS (FastAPI)
pipelines/                 # offline: ← ingestion/, models/(training), data/generate_*
```

Reglas de dependencia (a enforzar con import-linter):
`api → application → domain` y `application/infrastructure → domain`.
**Prohibido**: `domain → infrastructure`, `domain → api`.

---

## 3. Dead code / elementos no usados (VERIFICADO)

### 3.1 Removible — 0 referencias, behavior-safe

| Elemento | Ubicación | Verificación |
|----------|-----------|--------------|
| `generate_executive_report_markdown()` | `src/agent/tools.py:119` | 0 usos en src/api/tests |
| `compare_branches()` | `src/agent/tools.py:149` | 0 usos |
| import `simulate_new_claim` | `src/agent/tools.py:19` | importado, nunca usado |
| `ApiEnvelope` | `api/schemas.py:37` | 0 usos (las respuestas son dicts de `success()/failure()`) |
| `SimulatorClaimRequest` | `api/schemas.py:68` | 0 usos (la ruta usa `Body(dict)`) |
| `ReportResponseFormat` | `api/schemas.py:78` | 0 usos |
| var `min_len` | `src/agent/rag.py:36` | asignada, nunca leída (vulture 100%) |
| import `np` | `src/models/train_anomaly.py:9` | sin uso (script offline) |

### 3.2 NO borrar (frenos importantes)

- `src/explainability/explain_score.py` — alias de re-export, **exigido por el árbol de
  entregables del reto** (`docs/reto-aseguradora-del-sur.md:337`). Mantener.
- Métodos de `ChatHistoryStore` (`prepare_thread`, `append_message`, `choose_section`,
  `list_threads`, `update_context`, `rename_thread_from_first_message`…) — vulture los
  marca pero **sí** se usan dinámicamente desde `api/routes/agent.py`. Falsos positivos.
- Handlers de ruta y `validation_exception_handler` — registrados por decoradores. Falsos positivos.
- `route_intent` (8 usos), `enrich_claims_with_loaded_models` (2), `build_audit_report`/
  `render_audit_markdown`/`generate_report_markdown` (3 c/u) — vivos.

### 3.3 Mislocalizado (mover, NO borrar)

Tooling offline bajo `src/` → debe ir a `pipelines/`:
`ingestion/{scrape_ecuador,boost_ocds_sercop,package_ecuador_datasets,sources,build_agent_ready_dataset,model_curated_dataset}`,
`models/*` (training/validación), `data/{generate_synthetic_data,export_*,demo_scenarios,qa_metrics}`.

---

## 4. Plan de refactor por fases (cada fase verde: `pytest` + `import api.main`)

**Fase 0 — Limpieza de dead code (riesgo cero).**
Borrar lo de §3.1. Verificar 120 tests verdes + import OK.

**Fase 1 — Config/persistencia (riesgo bajo, refactor puro).**
- `src/infrastructure/config/paths.py` pasa a poseer `OUTPUT_PATH`; `scoring/final_score.py`
  lo re-exporta (back-compat, sin tocar callers).
- `ScoredClaimsRepository` envuelve `read_csv/to_csv/dedup`. Rutas y `tools` lo usan.

**Fase 2 — Capa de aplicación (riesgo medio, con shims).**
- Extraer `_rescore_with_population` → `application/claims/rescore_portfolio.py`. Ruta = fina.
- Extraer orquestación de `chat_agent` → `application/agent/chat_service.py`. Ruta = fina.
- Partir `tools.py` en `application/risk_queries.py` + servicios de reports; dejar
  `src/agent/tools.py` como **shim** que re-exporta → ningún caller se rompe de golpe.

**Fase 3 — Packaging.**
- Mover scripts offline a `pipelines/`; actualizar imports en `tests/`.
- `pyproject.toml`: separar deps runtime vs dev/pipeline → imagen de deploy más liviana.

**Fase 4 — Cohesión de `agent/`.**
- Reubicar `agent/llm/*` → `infrastructure/llm`, `ChatHistoryStore` → `infrastructure/chat`,
  `chat_service` → `application/agent`. Dominio del agente (router/intents/responses) aparte.

---

## 5. Recomendaciones de escalabilidad

1. **Reemplazar el CSV "DB"** detrás de `ScoredClaimsRepository` (SQLite/Postgres). El
   repositorio aísla el cambio; resuelve además S5 (escrituras concurrentes bajo threads).
2. **DI con `Depends`** para `ChatHistoryStore` y el LLM provider → testeable y swappable.
3. **CI de calidad**: `ruff` (lint) + `vulture` (dead code) + `import-linter` (contratos de
   capas). Evita que el acoplamiento vuelva a crecer.
4. **`pyproject.toml`** con config de paquete y split de dependencias runtime/dev.
5. **Smoke test** que importe `api.main` y golpee cada ruta con un CSV fixture mínimo.
6. **Versionar el contrato API** (`/api/v1`) antes de escalar consumidores.
