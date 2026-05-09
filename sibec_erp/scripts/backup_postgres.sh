#!/usr/bin/env bash
set -euo pipefail

if [ -z "${DATABASE_URL:-}" ]; then
  echo "DATABASE_URL is required"
  exit 1
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="backup_${TIMESTAMP}.sql"

pg_dump "$DATABASE_URL" > "$OUTPUT_FILE"
echo "Backup created: $OUTPUT_FILE"
