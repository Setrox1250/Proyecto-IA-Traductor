"""Preprocesamiento no destructivo de audio de referencia para XTTS-v2."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly


XTTS_REFERENCE_SAMPLE_RATE = 22_050


def _to_mono_float32(audio: np.ndarray) -> np.ndarray:
    """Convierte una señal válida a mono ``float32`` sin normalizar su timbre."""
    array = np.asarray(audio, dtype=np.float32)
    if array.ndim == 2:
        array = array.mean(axis=1, dtype=np.float32)
    if array.ndim != 1 or array.size == 0:
        raise ValueError("El audio debe contener al menos una muestra mono o multicanal.")
    if not np.isfinite(array).all():
        raise ValueError("El audio de referencia contiene NaN o infinito.")
    return array


def _resample(audio: np.ndarray, source_rate: int, target_rate: int) -> np.ndarray:
    if source_rate <= 0 or target_rate <= 0:
        raise ValueError("Las frecuencias de muestreo deben ser positivas.")
    if source_rate == target_rate:
        return audio.astype(np.float32, copy=True)
    divisor = int(np.gcd(source_rate, target_rate))
    return resample_poly(audio, target_rate // divisor, source_rate // divisor).astype(np.float32)


def validate_audio(path: str | Path, expected_sample_rate: int | None = None) -> dict[str, float | int | str]:
    """Valida existencia, duración, frecuencia, finitud y amplitud de un WAV."""
    audio_path = Path(path)
    if not audio_path.exists() or not audio_path.is_file():
        raise FileNotFoundError(f"Archivo de audio no encontrado: {audio_path}")

    audio, sample_rate = sf.read(audio_path, dtype="float32", always_2d=False)
    mono = _to_mono_float32(audio)
    duration_sec = len(mono) / float(sample_rate)
    peak = float(np.max(np.abs(mono)))
    if duration_sec <= 0:
        raise ValueError(f"El audio no tiene duración positiva: {audio_path}")
    if peak > 1.0001:
        raise ValueError(f"La amplitud del audio no es válida (peak={peak}): {audio_path}")
    if expected_sample_rate is not None and sample_rate != expected_sample_rate:
        raise ValueError(
            f"Frecuencia de muestreo inesperada: {sample_rate} Hz; "
            f"se esperaban {expected_sample_rate} Hz."
        )
    return {
        "path": str(audio_path),
        "sample_rate": int(sample_rate),
        "duration_sec": float(duration_sec),
        "peak": peak,
    }


def prepare_audio_copy(
    input_path: str | Path,
    output_path: str | Path,
    target_sample_rate: int,
) -> str:
    """Crea una copia WAV mono remuestreada, sin modificar el audio maestro."""
    source = Path(input_path)
    destination = Path(output_path)
    if source.resolve() == destination.resolve():
        raise ValueError("La salida debe ser distinta del audio maestro de entrada.")
    if not source.exists():
        raise FileNotFoundError(f"Archivo de audio no encontrado: {source}")

    audio, sample_rate = sf.read(source, dtype="float32", always_2d=False)
    mono = _to_mono_float32(audio)
    converted = _resample(mono, int(sample_rate), target_sample_rate)
    if converted.size == 0 or not np.isfinite(converted).all():
        raise ValueError("El remuestreo produjo un audio vacío o no finito.")

    # El remuestreo puede sobrepasar el rango por unos pocos decimales. Se limita
    # únicamente la copia de trabajo, sin alterar el audio maestro ni normalizarlo.
    converted = np.clip(converted, -1.0, 1.0)
    destination.parent.mkdir(parents=True, exist_ok=True)
    sf.write(destination, converted, target_sample_rate, format="WAV", subtype="FLOAT")
    validate_audio(destination, expected_sample_rate=target_sample_rate)
    return str(destination)


def prepare_reference_audio(input_path: str | Path, output_path: str | Path) -> str:
    """Prepara una copia WAV mono de 22.05 kHz para XTTS-v2.

    No aplica reducción de ruido ni normalización de volumen para conservar el
    timbre de la referencia. El archivo de entrada nunca se sobrescribe.
    """
    return prepare_audio_copy(input_path, output_path, XTTS_REFERENCE_SAMPLE_RATE)
