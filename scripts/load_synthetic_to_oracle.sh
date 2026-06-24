#!/usr/bin/env bash
# Optional demo loader — requires Oracle XE running via docker/oracle-xe
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCHEMA="$ROOT/db/oracle/schema.sql"

echo "Applying schema to Oracle XE..."
docker exec -i rastoseguro-oracle-xe sqlplus -s rastro/rastro@XEPDB1 @"$SCHEMA" || {
  echo "Ensure Oracle XE is running: cd docker/oracle-xe && docker compose up -d"
  exit 1
}
echo "Schema applied. Use SQL*Loader templates in db/oracle/load_csv.sql for CSV import."
