# AGENTS.md

## Cursor Cloud specific instructions

RastroSeguro is a single product with two dev services plus offline tooling. The
data/model artifacts (`data/synthetic/`, `data/processed/siniestros_scored.csv`,
`models/*.joblib`) are committed, so the API works without running any pipeline.

### Services

| Service | Dir | Dev command | Port | Notes |
|---------|-----|-------------|------|-------|
| FastAPI backend | `api/` (over `src/`) | `source .venv/bin/activate && uvicorn api.main:app --reload --port 8000` | 8000 | Health: `curl http://localhost:8000/api/health`. Standard commands in `README.md` / `docs/05-instrucciones-ejecucion.md`. |
| Next.js frontend | `frontend/` | `bun run dev` | 3000 | Reads `NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000`). Both services must run for the end-to-end UI. |

### Python
- Managed with `uv` (`uv.lock` committed); dependencies live in `pyproject.toml`
  (`.[dev]` = pytest/ruff/vulture/import-linter, `.[pipelines]` = scraping/Excel).
  The virtualenv is `.venv`.
- Test/lint (from repo root, venv active): `pytest`, `ruff check .`,
  `lint-imports`, `vulture`.
- Pre-existing (NOT environment) issues as of setup: `ruff check .` reports ~25
  style errors, and `tests/test_document_extraction.py::...joins_split_column_blocks`
  fails on a `monto_estimado` key (PDF-extraction detail). 129/130 tests pass. Do
  not "fix" these as part of environment work.

### Frontend (important gotchas)
- `frontend/.gitignore` ignores `package.json` and `next.config.mjs` (v0.dev
  export). `package.json` was reconstructed from `bun.lock` and force-committed so
  the app can install/run; if it is ever missing again, regenerate it from the
  `workspaces[""].dependencies`/`devDependencies` in `frontend/bun.lock`.
- `bun` is the package manager (matches committed `bun.lock`). `node`/`pnpm` also
  exist but the lockfile is bun's.
- `lib/case-report-pdf.ts` needs `jspdf` + `jspdf-autotable`; these were missing
  from the original lockfile and are now added. Without them the `/platform` and
  `/landing` routes 500 with a module-not-found error.
- `core-js` postinstall is blocked by bun (harmless ad script); no action needed.
- No `next.config.mjs` is required — Next 16 runs fine without it.

### LLM (optional)
- The antifraud agent works fully in deterministic mode. Set `OPENAI_API_KEY` and
  `RASTRO_LLM_ENABLED=true` (see `.env.example`) only to enable OpenAI synthesis.
