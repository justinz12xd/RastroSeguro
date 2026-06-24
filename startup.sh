#!/bin/bash
set -euo pipefail

# Azure App Service sets PORT; default to 8000 for local parity.
PORT="${PORT:-8000}"

# Use a single worker on small App Service plans to avoid OOM restarts.
# sklearn/pandas + 4 gunicorn workers often exceed B1/B2 memory limits.
exec gunicorn api.main:app \
  --bind "0.0.0.0:${PORT}" \
  --timeout 600 \
  --workers "${WEB_CONCURRENCY:-1}" \
  --threads "${GUNICORN_THREADS:-4}" \
  --worker-tmp-dir /dev/shm \
  -k uvicorn.workers.UvicornWorker
