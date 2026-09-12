"""Acceso a FLEURS (google/fleurs) por streaming y guardado de muestras de audio.

FLEURS es un corpus multilingüe de reconocimiento de voz; la configuración
`es_419` (español latinoamericano) contiene audio, transcripción y metadatos
básicos, pero NO proporciona un `speaker_id` (identificador de hablante). Por
eso dicha columna se deja siempre a None, sin inventar valores.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

import numpy as np
import pandas as pd

FLEURS_DATASET_NAME = "google/fleurs"
FLEURS_CONFIG_ES = "es_419"
DEFAULT_SAMPLE_SIZE = 20
SEED = 42
SAMPLE_RATE_HZ = 16_000

MANIFEST_COLUMNS = [
    "sample_id",
    "speaker_id",
    "audio_path",
    "transcription_es",
    "duration_sec",
    "source",
]


def stream_fleurs(config: str = FLEURS_CONFIG_ES):
    """Devuelve FLEURS en modo streaming (IterableDataset).

    Con streaming no se descarga el corpus completo: las muestras se van
    descargando bajo demanda mientras se itera.
    """
    from datasets import load_dataset

    dataset = load_dataset(FLEURS_DATASET_NAME, config, streaming=True)
    return dataset["train"]


def take_samples(stream: Any, n: int = DEFAULT_SAMPLE_SIZE, seed: int = SEED) -> list[dict]:
    """Toma `n` muestras del stream con un barajado 'safe' reproducible.

    El barajado con buffer no mezcla todo el dataset, pero garantiza variación
    y, con la misma semilla y versión de la librería, los mismos ejemplos.
    """
    dataset = stream.shuffle(seed=seed, buffer_size=1_000)
    return list(dataset.take(n))


def save_audio_sample(audio: dict[str, Any], output_dir: str | Path, sample_id: str) -> Path:
    """Guarda un audio de FLEURS en WAV (16 kHz, float 32). Devuelve la ruta."""
    import soundfile as sf

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{sample_id}.wav"
    if not out_path.exists():
        sf.write(out_path, audio["array"], audio["sampling_rate"])
    return out_path


def audio_duration_sec(audio: dict[str, Any]) -> float:
    """Duración en segundos a partir del array de audio ya decodificado."""
    return float(len(audio["array"])) / float(audio["sampling_rate"])


def get_transcription(sample: dict[str, Any]) -> str:
    """Transcripción preferida: la original (sin normalizar) si existe."""
    transcription = sample.get("raw_transcription") or sample.get("transcription") or ""
    return str(transcription)


def build_fleurs_manifest(
    samples: Iterator[dict[str, Any]] | list[dict[str, Any]],
    audio_dir: str | Path = "data/raw/audio",
    source: str = f"fleurs:{FLEURS_CONFIG_ES}",
) -> pd.DataFrame:
    """Guarda cada audio en WAV y construye el manifest `fleurs_sample.csv`.

    Nota: FLEURS no expone `speaker_id`; la columna queda vacía (None) y esto
    queda documentado en el notebook 01.
    """
    rows: list[dict[str, Any]] = []
    audio_dir = Path(audio_dir)
    for i, sample in enumerate(samples):
        sample_id = f"fleurs_{FLEURS_CONFIG_ES}_{i:04d}"
        audio_path = save_audio_sample(sample["audio"], audio_dir, sample_id)
        rows.append(
            {
                "sample_id": sample_id,
                "speaker_id": None,
                "audio_path": audio_path.as_posix(),
                "transcription_es": get_transcription(sample),
                "duration_sec": round(audio_duration_sec(sample["audio"]), 3),
                "source": source,
            }
        )
    return pd.DataFrame(rows, columns=MANIFEST_COLUMNS)