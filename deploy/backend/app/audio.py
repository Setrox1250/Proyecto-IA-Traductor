"""Validación y normalización de audio antes de invocar el pipeline."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from app.config import Settings
from app.errors import APIError, AudioTooLongError, InvalidAudioError
from src.voice_cloning.audio import DEFAULT_MIN_RMS, validate_audio


def _run(command: list[str], timeout: int) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as error:
        raise APIError(
            503,
            "media_tool_unavailable",
            "El servidor no tiene las herramientas de audio necesarias.",
        ) from error
    except subprocess.TimeoutExpired as error:
        raise InvalidAudioError(
            "El audio tardó demasiado en analizarse y fue rechazado."
        ) from error


def probe_duration(path: Path, settings: Settings) -> float:
    """Obtiene la duración del primer stream de audio sin decodificar completo."""
    command = [
        settings.ffprobe_bin,
        "-v",
        "error",
        "-select_streams",
        "a:0",
        "-show_entries",
        "format=duration:stream=duration",
        "-of",
        "json",
        str(path),
    ]
    completed = _run(command, settings.ffmpeg_timeout_seconds)
    if completed.returncode != 0:
        raise InvalidAudioError("El archivo no contiene un audio legible.")
    try:
        payload = json.loads(completed.stdout or "{}")
    except json.JSONDecodeError as error:
        raise InvalidAudioError("No se pudo interpretar la información del audio.") from error

    candidates: list[float] = []
    format_duration = payload.get("format", {}).get("duration")
    if format_duration not in (None, "N/A"):
        try:
            candidates.append(float(format_duration))
        except (TypeError, ValueError):
            pass
    for stream in payload.get("streams", []):
        stream_duration = stream.get("duration")
        if stream_duration in (None, "N/A"):
            continue
        try:
            candidates.append(float(stream_duration))
        except (TypeError, ValueError):
            continue

    durations = [value for value in candidates if value > 0]
    if not durations:
        raise InvalidAudioError("No se pudo determinar la duración del audio.")
    return max(durations)


def normalize_audio(
    input_path: Path,
    output_path: Path,
    settings: Settings,
) -> dict:
    """Convierte cualquier formato permitido a WAV mono PCM y valida su calidad."""
    duration = probe_duration(input_path, settings)
    if duration > settings.max_audio_seconds:
        raise AudioTooLongError(settings.max_audio_seconds)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        settings.ffmpeg_bin,
        "-nostdin",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(input_path),
        "-map_metadata",
        "-1",
        "-vn",
        "-ac",
        "1",
        "-ar",
        "44100",
        "-c:a",
        "pcm_s16le",
        str(output_path),
    ]
    completed = _run(command, settings.ffmpeg_timeout_seconds)
    if completed.returncode != 0 or not output_path.exists():
        raise InvalidAudioError("El archivo de audio está corrupto o no es compatible.")

    try:
        info = validate_audio(
            output_path,
            min_duration_sec=settings.min_audio_seconds,
            min_rms=DEFAULT_MIN_RMS,
        )
    except (ValueError, OSError) as error:
        raise InvalidAudioError(
            "El audio no contiene voz suficiente o su formato es inválido."
        ) from error

    if info["duration_sec"] > settings.max_audio_seconds:
        raise AudioTooLongError(settings.max_audio_seconds)

    return info
