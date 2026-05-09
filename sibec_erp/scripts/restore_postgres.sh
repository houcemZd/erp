#!/usr/bin/env bash
set -euo pipefail

if [ -z "${DATABASE_URL:-}" ]; then
  echo "DATABASE_URL is required"
  exit 1
fi

if [ $# -ne 1 ]; then
  echo "Usage: $0 <backup.sql>"
  exit 1
fi

psql "$DATABASE_URL" < "$1"
echo "Restore completed from: $1"
