"""Acceso a FLEURS (google/fleurs) por streaming y guardado de muestras de audio.

FLEURS es un corpus multilingüe de reconocimiento de voz; la configuración
`es_419` (español latinoamericano) contiene audio, transcripción y metadatos
básicos, pero NO proporciona un `speaker_id` (identificador de hablante). Por
eso dicha columna se deja siempre a None, sin inventar valores.
"""

from __future__ import annotations

from collections.abc import Iterator
from io import BytesIO
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

FLEURS_DATASET_NAME = "google/fleurs"
FLEURS_CONFIG_ES = "es_419"
DEFAULT_SAMPLE_SIZE = 20
SEED = 42
SAMPLE_RATE_HZ = 16_000
SHUFFLE_BUFFER_SIZE = 100

MANIFEST_COLUMNS = [
    "sample_id",
    "sentence_id",
    "speaker_id",
    "audio_path",
    "transcription_es",
    "duration_sec",
    "source",
]


def stream_fleurs(config: str = FLEURS_CONFIG_ES, split: str = "test"):
    """Devuelve un split oficial de FLEURS en modo streaming.

    El valor por defecto es ``test``: usar ``train`` para evaluación introduce
    contaminación y fue el error detectado en la reserva histórica.
    """
    from datasets import Audio, load_dataset

    if split not in {"train", "validation", "test"}:
        raise ValueError(f"Split FLEURS no válido: {split!r}")
    dataset = load_dataset(FLEURS_DATASET_NAME, config, streaming=True)
    # ``decode=False`` evita depender de torchcodec. Los bytes se decodifican
    # después con soundfile, que forma parte de requirements/dataset.txt.
    return dataset[split].cast_column("audio", Audio(decode=False))


def take_samples(
    stream: Any,
    n: int = DEFAULT_SAMPLE_SIZE,
    seed: int = SEED,
    buffer_size: int = SHUFFLE_BUFFER_SIZE,
) -> list[dict]:
    """Toma `n` muestras del stream con un barajado 'safe' reproducible.

    El barajado con buffer no mezcla todo el dataset, pero garantiza variación
    y, con la misma semilla y versión de la librería, los mismos ejemplos.
    """
    dataset = stream.shuffle(seed=seed, buffer_size=buffer_size)
    return list(dataset.take(n))


def decode_audio(audio: dict[str, Any]) -> tuple[np.ndarray, int]:
    """Decodifica un objeto Audio de datasets sin requerir torchcodec."""
    import soundfile as sf

    if audio.get("array") is not None and audio.get("sampling_rate") is not None:
        array = np.asarray(audio["array"], dtype=np.float32)
        sample_rate = int(audio["sampling_rate"])
    else:
        source: Any
        if audio.get("bytes") is not None:
            source = BytesIO(audio["bytes"])
        elif audio.get("path"):
            source = audio["path"]
        else:
            raise ValueError("El objeto de audio no contiene bytes, path ni array.")
        array, sample_rate = sf.read(source, dtype="float32", always_2d=False)
        array = np.asarray(array, dtype=np.float32)

    if array.ndim == 2:
        array = array.mean(axis=1, dtype=np.float32)
    if array.ndim != 1 or array.size == 0:
        raise ValueError("El audio decodificado está vacío o tiene una forma inválida.")
    return array, sample_rate


def save_audio_sample(audio: dict[str, Any], output_dir: str | Path, sample_id: str) -> Path:
    """Guarda un audio de FLEURS en WAV (16 kHz, float 32). Devuelve la ruta."""
    import soundfile as sf

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{sample_id}.wav"
    if not out_path.exists():
        array, sample_rate = decode_audio(audio)
        sf.write(out_path, array, sample_rate, subtype="FLOAT")
    return out_path


def audio_duration_sec(audio: dict[str, Any]) -> float:
    """Duración en segundos a partir del array de audio ya decodificado."""
    array, sample_rate = decode_audio(audio)
    return float(len(array)) / float(sample_rate)


def audio_quality(array: np.ndarray, sample_rate: int) -> dict[str, float | bool]:
    """Mide duración, peak y RMS para detectar audios vacíos o silenciosos."""
    signal = np.asarray(array, dtype=np.float32)
    if signal.ndim == 2:
        signal = signal.mean(axis=1, dtype=np.float32)
    if signal.ndim != 1 or signal.size == 0 or sample_rate <= 0:
        raise ValueError("El audio está vacío o tiene una forma inválida.")
    duration = float(signal.size) / float(sample_rate)
    peak = float(np.max(np.abs(signal)))
    rms = float(np.sqrt(np.mean(np.square(signal, dtype=np.float64))))
    return {
        "duration_sec": duration,
        "peak": peak,
        "rms": rms,
        "is_empty": False,
        "is_too_short": duration < 1.0,
        "is_silent": rms < 1e-4,
    }


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
                "sentence_id": str(sample["id"]),
                "speaker_id": None,
                "audio_path": audio_path.as_posix(),
                "transcription_es": get_transcription(sample),
                "duration_sec": round(audio_duration_sec(sample["audio"]), 3),
                "source": source,
            }
        )
    return pd.DataFrame(rows, columns=MANIFEST_COLUMNS)
