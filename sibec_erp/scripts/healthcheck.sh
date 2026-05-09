#!/usr/bin/env bash
set -euo pipefail

URL="${1:-http://127.0.0.1:5000/healthz}"

curl -fsS "$URL" && echo
