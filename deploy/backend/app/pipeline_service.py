"""Servicio de integración entre FastAPI y el pipeline de IA existente."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from starlette.concurrency import run_in_threadpool

from app.audio import normalize_audio
from app.config import Settings
from app.errors import (
    APIError,
    InvalidAudioError,
    ModelUnavailableError,
    PipelineFailureError,
)
from app.result_store import ResultStore

logger = logging.getLogger(__name__)

RESULT_URL_PREFIX = "/api/v1/results"


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


class PipelineService:
    """Ejecuta el pipeline real de forma secuencial y mantiene su caché de modelos.

    ``process_audio`` ya conserva Whisper, MarianMT y XTTS cargados en memoria.
    El lock evita dos inferencias simultáneas sobre la misma GPU.
    """

    def __init__(
        self,
        settings: Settings,
        store: ResultStore,
        processor: Callable[[str, str], dict[str, Any]] | None = None,
    ) -> None:
        self.settings = settings
        self.store = store
        self._processor = processor
        self._lock = asyncio.Lock()
        self._busy = False
        self._warm = False
        self._requests_total = 0
        self._completed_total = 0
        self._last_error: str | None = None
        self._last_completed_at: str | None = None

    def _get_processor(self) -> Callable[[str, str], dict[str, Any]]:
        if self._processor is None:
            # Importación diferida: /status no carga modelos ni inicializa CUDA.
            from src.pipeline.runner import process_audio

            self._processor = process_audio
        return self._processor

    def _run_pipeline(self, source: Path, output_dir: Path) -> dict[str, Any]:
        processor = self._get_processor()
        return processor(str(source), str(output_dir))

    async def translate(self, job_id: str, upload_path: Path) -> dict[str, Any]:
        directory = self.store.job_dir(job_id)
        if not directory.is_dir():
            raise FileNotFoundError("El directorio del trabajo no existe.")
        self._requests_total += 1
        self._last_error = None
        async with self._lock:
            self._busy = True
            started = time.perf_counter()
            try:
                upload_path = Path(upload_path)
                normalized_path = directory / "normalized.wav"
                await run_in_threadpool(
                    normalize_audio, upload_path, normalized_path, self.settings
                )
                upload_path.unlink(missing_ok=True)

                metadata = await run_in_threadpool(
                    self._run_pipeline, normalized_path, directory
                )
                output_path = directory / "output.wav"
                if not output_path.is_file():
                    raise RuntimeError("El pipeline no generó el audio traducido.")

                payload = self._build_payload(job_id, metadata, started)
                for intermediate in (
                    normalized_path,
                    directory / "input.wav",
                    directory / "asr_input.wav",
                    directory / "xtts_reference.wav",
                    directory / "transcription.txt",
                    directory / "translation.txt",
                    directory / "metadata.json",
                    directory / "error.json",
                ):
                    intermediate.unlink(missing_ok=True)
                stored = self.store.save(job_id, payload)
                self._warm = True
                self._completed_total += 1
                self._last_completed_at = _utc_now()
                return stored
            except APIError as error:
                self._last_error = error.code
                self.store.delete(job_id)
                raise
            except RuntimeError as error:
                message = str(error)
                self._last_error = "model_unavailable"
                self.store.delete(job_id)
                if "licencia" in message.lower() or "cpml" in message.lower():
                    raise ModelUnavailableError(
                        "XTTS-v2 no está habilitado. El operador debe aceptar la "
                        "licencia CPML configurando COQUI_TOS_AGREED=1."
                    ) from error
                if "out of memory" in message.lower() or "cuda" in message.lower():
                    raise ModelUnavailableError(
                        "La GPU no tiene memoria suficiente para procesar este audio."
                    ) from error
                logger.exception("Fallo del pipeline para el trabajo %s", job_id)
                raise PipelineFailureError() from error
            except MemoryError as error:
                self._last_error = "gpu_out_of_memory"
                self.store.delete(job_id)
                raise ModelUnavailableError(
                    "No hay memoria suficiente para procesar este audio."
                ) from error
            except ValueError as error:
                self._last_error = "invalid_audio"
                self.store.delete(job_id)
                message = str(error).lower()
                if "silencio" in message:
                    detail = "El audio parece silencioso. Prueba con una grabación con voz."
                elif "corto" in message:
                    detail = "El audio es demasiado corto para procesarlo."
                elif "duración" in message or "duracion" in message:
                    detail = "La duración del audio no es válida."
                else:
                    detail = "El audio no es válido o no contiene voz suficiente."
                raise InvalidAudioError(detail) from error
            except Exception as error:
                self._last_error = "pipeline_error"
                self.store.delete(job_id)
                logger.exception(
                    "Error inesperado del pipeline para el trabajo %s", job_id
                )
                raise PipelineFailureError() from error
            finally:
                self._busy = False
                elapsed = time.perf_counter() - started
                logger.info(
                    "Trabajo %s finalizado en %.2f s (estado=%s)",
                    job_id,
                    elapsed,
                    "ok" if self._last_error is None else self._last_error,
                )

    def _build_payload(
        self,
        job_id: str,
        metadata: dict[str, Any],
        started: float,
    ) -> dict[str, Any]:
        for key in ("transcription_es", "translation_en", "speaker_similarity", "timings"):
            if key not in metadata:
                raise PipelineFailureError()
        audio = metadata.get("audio") or {}
        models = metadata.get("models") or {}
        filename = f"hilo_{job_id[:8]}_en.wav"
        return {
            "id": job_id,
            "status": "completed",
            "transcription_es": str(metadata["transcription_es"]),
            "translation_en": str(metadata["translation_en"]),
            "speaker_similarity": float(metadata["speaker_similarity"]),
            "audio": {
                "url": f"{RESULT_URL_PREFIX}/{job_id}/audio",
                "download_url": f"{RESULT_URL_PREFIX}/{job_id}/audio?download=1",
                "mime_type": "audio/wav",
                "sample_rate": int(audio.get("output_sample_rate", 24000)),
                "duration_sec": float(audio.get("output_duration_sec", 0.0)),
                "filename": filename,
            },
            "input": {
                "duration_sec": float(audio.get("input_duration_sec", 0.0)),
            },
            "timings": {
                "preprocessing_sec": float(metadata["timings"].get("preprocessing_sec", 0)),
                "asr_sec": float(metadata["timings"].get("asr_sec", 0)),
                "translation_sec": float(metadata["timings"].get("translation_sec", 0)),
                "xtts_sec": float(metadata["timings"].get("xtts_sec", 0)),
                "speaker_evaluation_sec": float(
                    metadata["timings"].get("speaker_evaluation_sec", 0)
                ),
                "total_sec": float(metadata["timings"].get("total_sec", 0)),
                "api_sec": round(time.perf_counter() - started, 4),
            },
            "models": {
                "asr": str(models.get("asr", "openai/whisper-small")),
                "translation": str(
                    models.get("translation", "Helsinki-NLP/opus-mt-es-en")
                ),
                "translation_checkpoint": str(
                    models.get("translation_checkpoint", "base")
                ),
                "tts": str(models.get("tts", "coqui/XTTS-v2")),
                "speaker_encoder": str(
                    models.get("speaker_encoder", "speechbrain/spkrec-ecapa-voxceleb")
                ),
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "busy": self._busy,
            "warm": self._warm,
            "mode": "sequential",
            "requests_total": self._requests_total,
            "completed_total": self._completed_total,
            "last_error_code": self._last_error,
            "last_completed_at": self._last_completed_at,
        }
