"""Descarga explícita de los modelos usados por el proyecto.

No se ejecuta automáticamente. Ejemplos:
    python scripts/download_models.py --model all
    python scripts/download_models.py --model whisper marian ecapa
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


HF_MODELS = {
    "whisper": "openai/whisper-small",
    "marian": "Helsinki-NLP/opus-mt-es-en",
    "ecapa": "speechbrain/spkrec-ecapa-voxceleb",
}
XTTS_API_MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"


def download_hf(model_id: str) -> None:
    from huggingface_hub import snapshot_download

    print(f"Descargando {model_id}...")
    snapshot_download(repo_id=model_id)
    print(f"OK: {model_id}")


def download_xtts() -> None:
    if os.environ.get("COQUI_TOS_AGREED") != "1":
        raise RuntimeError(
            "XTTS-v2 requiere aceptar la licencia CPML. "
            "Ejecute `export COQUI_TOS_AGREED=1` antes de descargarlo."
        )
    from TTS.api import TTS

    print(f"Descargando {XTTS_API_MODEL}...")
    TTS(model_name=XTTS_API_MODEL, progress_bar=False)
    print("OK: XTTS-v2")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        nargs="+",
        choices=["all", "whisper", "marian", "ecapa", "xtts"],
        default=["all"],
    )
    args = parser.parse_args()
    selected = set(args.model)
    if "all" in selected:
        selected = {"whisper", "marian", "ecapa", "xtts"}
    for name in ("whisper", "marian", "ecapa"):
        if name in selected:
            download_hf(HF_MODELS[name])
    if "xtts" in selected:
        download_xtts()


if __name__ == "__main__":
    main()
