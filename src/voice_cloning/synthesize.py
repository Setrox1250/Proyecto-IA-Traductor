"""Síntesis zero-shot en inglés con la referencia vocal de XTTS-v2."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import soundfile as sf
import torch
import yaml

from src.voice_cloning.audio import validate_audio


DEFAULT_MODEL_ID = "coqui/XTTS-v2"
DEFAULT_TTS_API_MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"
DEFAULT_CONFIG_PATH = Path("configs/voice_cloning.yaml")
_TTS_CACHE: dict[tuple[str, str], Any] = {}


def load_voice_cloning_config(config_path: str | Path = DEFAULT_CONFIG_PATH) -> dict:
    path = Path(config_path)
    if path.exists():
        with open(path, "r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}
    return {"model_name": DEFAULT_MODEL_ID, "tts_api_model_name": DEFAULT_TTS_API_MODEL}


def _device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"


def get_xtts_model(device: str | None = None):
    """Carga y reutiliza XTTS. La importación pesada se mantiene diferida."""
    cfg = load_voice_cloning_config()
    selected_device = device or _device()
    api_model = cfg.get("tts_api_model_name", DEFAULT_TTS_API_MODEL)
    key = (api_model, selected_device)
    if key not in _TTS_CACHE:
        from TTS.api import TTS

        model = TTS(model_name=api_model, progress_bar=False)
        _TTS_CACHE[key] = model.to(selected_device)
    return _TTS_CACHE[key]


def synthesize(
    text: str,
    reference_audio: str,
    output_path: str,
    language: str = "en",
) -> str:
    """Genera un WAV zero-shot usando *reference_audio* como voz de referencia."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("El texto a sintetizar no puede estar vacío.")
    reference = Path(reference_audio)
    output = Path(output_path)
    if output.suffix.lower() != ".wav":
        raise ValueError("XTTS debe escribir un archivo WAV de salida.")
    validate_audio(reference)
    output.parent.mkdir(parents=True, exist_ok=True)

    model = get_xtts_model()
    model.tts_to_file(
        text=text.strip(),
        speaker_wav=str(reference),
        language=language,
        file_path=str(output),
    )
    # Se mide; no se asume que el WAV de XTTS sea 24 kHz.
    info = validate_audio(output)
    if sf.info(output).samplerate != info["sample_rate"]:
        raise RuntimeError("La frecuencia medida del WAV generado es inconsistente.")
    return str(output)
