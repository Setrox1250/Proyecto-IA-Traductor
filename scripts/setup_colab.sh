#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${1:-$(pwd)}"

if [[ ! -f "$PROJECT_ROOT/requirements/dataset.txt" || ! -d "$PROJECT_ROOT/src" ]]; then
  echo "Error: '$PROJECT_ROOT' no parece ser la raíz de IA-Proyecto." >&2
  echo "Uso: bash scripts/setup_colab.sh /ruta/a/IA-Proyecto" >&2
  exit 1
fi

cd "$PROJECT_ROOT"
python -m pip install --quiet -r requirements/dataset.txt
echo "Entorno listo en: $PROJECT_ROOT"
