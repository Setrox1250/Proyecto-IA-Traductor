"""Configuración centralizada del backend, basada en variables de entorno."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RESULT_DIR = PROJECT_ROOT / "deploy" / "backend" / ".data" / "results"

SERVICE_NAME = "hilo-translation-api"
SERVICE_VERSION = "1.0.0"

ALLOWED_EXTENSIONS = (".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm")
ALLOWED_MIME_TYPES = (
    "audio/wav",
    "audio/x-wav",
    "audio/wave",
    "audio/mpeg",
    "audio/mp3",
    "audio/mp4",
    "audio/x-m4a",
    "audio/ogg",
    "audio/flac",
    "audio/x-flac",
    "audio/webm",
    "video/webm",
    "application/ogg",
)
GENERIC_MIME_TYPES = ("", "application/octet-stream")

DEFAULT_CORS_ORIGINS = (
    "http://localhost:8081",
    "http://127.0.0.1:8081",
    "http://localhost:19006",
    "http://127.0.0.1:19006",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)


def _env_int(name: str, default: int, minimum: int = 1) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError as error:
        raise ValueError(f"{name} debe ser un entero.") from error
    if value < minimum:
        raise ValueError(f"{name} debe ser >= {minimum}.")
    return value


def _env_float(name: str, default: float, minimum: float = 0.1) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError as error:
        raise ValueError(f"{name} debe ser numérico.") from error
    if value < minimum:
        raise ValueError(f"{name} debe ser >= {minimum}.")
    return value


def _env_list(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return tuple(item.strip() for item in raw.split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    service_name: str = SERVICE_NAME
    version: str = SERVICE_VERSION
    max_upload_mb: int = 20
    max_audio_seconds: float = 120.0
    min_audio_seconds: float = 0.5
    result_ttl_seconds: int = 3600
    result_dir: Path = DEFAULT_RESULT_DIR
    cors_origins: tuple[str, ...] = DEFAULT_CORS_ORIGINS
    ffmpeg_bin: str = "ffmpeg"
    ffprobe_bin: str = "ffprobe"
    ffmpeg_timeout_seconds: int = 60
    cleanup_interval_seconds: int = 300
    log_level: str = "INFO"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def xtts_license_accepted(self) -> bool:
        return os.getenv("COQUI_TOS_AGREED") == "1"

    @classmethod
    def from_env(cls) -> Settings:
        result_dir = Path(
            os.getenv("RESULT_DIR", str(DEFAULT_RESULT_DIR))
        ).expanduser()
        if not result_dir.is_absolute():
            result_dir = (PROJECT_ROOT / result_dir).resolve()

        return cls(
            max_upload_mb=_env_int("MAX_UPLOAD_MB", 20),
            max_audio_seconds=_env_float("MAX_AUDIO_SECONDS", 120.0),
            min_audio_seconds=_env_float("MIN_AUDIO_SECONDS", 0.5),
            result_ttl_seconds=_env_int("RESULT_TTL_SECONDS", 3600, minimum=60),
            result_dir=result_dir,
            cors_origins=_env_list("CORS_ORIGINS", DEFAULT_CORS_ORIGINS),
            ffmpeg_bin=os.getenv("FFMPEG_BIN", "ffmpeg"),
            ffprobe_bin=os.getenv("FFPROBE_BIN", "ffprobe"),
            ffmpeg_timeout_seconds=_env_int("FFMPEG_TIMEOUT_SECONDS", 60),
            cleanup_interval_seconds=_env_int(
                "CLEANUP_INTERVAL_SECONDS", 300, minimum=30
            ),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        )
