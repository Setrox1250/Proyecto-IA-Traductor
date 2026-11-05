#!/usr/bin/env bash
# Inicia la API desde deploy/backend con el entorno del proyecto.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$SCRIPT_DIR"

PYTHON_BIN="${PYTHON_BIN:-$PROJECT_ROOT/.venv-xtts/bin/python}"
if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "No se encontró el intérprete: $PYTHON_BIN" >&2
  echo "Crea el entorno o exporta PYTHON_BIN con la ruta correcta." >&2
  exit 1
fi

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
ENV_FILE="${ENV_FILE:-$SCRIPT_DIR/.env}"

ARGS=(-m uvicorn app.main:app --host "$HOST" --port "$PORT" --workers 1)
if [[ -f "$ENV_FILE" ]]; then
  ARGS+=(--env-file "$ENV_FILE")
fi

exec "$PYTHON_BIN" "${ARGS[@]}"
