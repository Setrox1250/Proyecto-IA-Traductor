"""Evaluación objetiva continua de similitud vocal con ECAPA-TDNN."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import torch
import torch.nn.functional as functional
import torchaudio


MODEL_ID = "speechbrain/spkrec-ecapa-voxceleb"
TARGET_SAMPLE_RATE = 16_000
_ENCODER_CACHE: dict[str, Any] = {}


def load_speaker_encoder(device: str | None = None):
    """Carga los pesos preentrenados ECAPA una sola vez por dispositivo."""
    selected_device = device or ("cuda:0" if torch.cuda.is_available() else "cpu")
    if selected_device not in _ENCODER_CACHE:
        from speechbrain.inference.speaker import EncoderClassifier

        encoder = EncoderClassifier.from_hparams(
            source=MODEL_ID,
            run_opts={"device": selected_device},
        )
        _ENCODER_CACHE[selected_device] = encoder
    return _ENCODER_CACHE[selected_device]


def load_audio_for_ecapa(audio_path: str | Path) -> torch.Tensor:
    """Entrega audio mono 16 kHz, finito y en el rango esperado por ECAPA."""
    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(f"Archivo de audio no encontrado: {path}")
    waveform, sample_rate = torchaudio.load(str(path))
    if waveform.numel() == 0:
        raise ValueError("El audio está vacío.")
    waveform = waveform.mean(dim=0, keepdim=True).to(torch.float32)
    if sample_rate != TARGET_SAMPLE_RATE:
        waveform = torchaudio.functional.resample(waveform, sample_rate, TARGET_SAMPLE_RATE)
    if not torch.isfinite(waveform).all():
        raise ValueError("El audio contiene NaN o infinito.")
    return waveform.clamp(-1.0, 1.0)


def extract_embedding(audio_path: str | Path) -> torch.Tensor:
    """Extrae un embedding L2-normalizado de un WAV con ECAPA-TDNN."""
    encoder = load_speaker_encoder()
    waveform = load_audio_for_ecapa(audio_path)
    device = next(encoder.parameters()).device
    waveform = waveform.to(device)
    with torch.inference_mode():
        embedding = encoder.encode_batch(waveform).squeeze()
    return functional.normalize(embedding.flatten(), p=2, dim=0).cpu()


def speaker_similarity(reference_audio: str | Path, generated_audio: str | Path) -> float:
    """Devuelve coseno ECAPA continuo, sin convertirlo en umbral de identidad."""
    reference = extract_embedding(reference_audio)
    generated = extract_embedding(generated_audio)
    if reference.shape != generated.shape:
        raise ValueError("Los embeddings ECAPA tienen dimensiones incompatibles.")
    return float(functional.cosine_similarity(reference, generated, dim=0).item())
