"""API REST FastAPI para el pipeline de traducción de voz ES→EN."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import time
import uuid
from collections.abc import Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app.config import (
    ALLOWED_EXTENSIONS,
    ALLOWED_MIME_TYPES,
    GENERIC_MIME_TYPES,
    Settings,
)
from app.errors import (
    APIError,
    AudioTooLargeError,
    InvalidAudioError,
    ModelUnavailableError,
    ResultNotFoundError,
    UnsupportedMediaError,
)
from app.pipeline_service import RESULT_URL_PREFIX, PipelineService
from app.result_store import ResultStore
from app.schemas import (
    CapabilitiesInfo,
    ErrorResponse,
    GPUInfo,
    HealthResponse,
    LimitsInfo,
    ModelSummary,
    PipelineStatus,
    StatusResponse,
    TranslateResponse,
)

logger = logging.getLogger(__name__)

API_PREFIX = "/api/v1"
MAX_UPLOAD_CHUNK = 1024 * 1024

MODEL_SUMMARY = ModelSummary(
    asr="openai/whisper-small",
    translation="Helsinki-NLP/opus-mt-es-en",
    translation_checkpoint="base",
    tts="coqui/XTTS-v2",
    speaker_encoder="speechbrain/spkrec-ecapa-voxceleb",
)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _gpu_info() -> tuple[GPUInfo, str]:
    try:
        import torch

        if torch.cuda.is_available():
            properties = torch.cuda.get_device_properties(0)
            return (
                GPUInfo(
                    available=True,
                    name=torch.cuda.get_device_name(0),
                    total_memory_gb=round(properties.total_memory / (1024**3), 1),
                ),
                "cuda",
            )
    except Exception:  # noqa: BLE001 - el estado nunca debe romper la API
        logger.warning("No se pudo consultar el estado de CUDA.")
    return GPUInfo(available=False), "cpu"


def _error_response(request: Request, error: APIError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=error.status_code,
        content={
            "error": {
                "code": error.code,
                "message": error.message,
                "request_id": request_id,
            }
        },
        headers=error.headers,
    )


def _validate_upload_metadata(filename: str | None, content_type: str | None) -> str:
    suffix = Path(filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(item.lstrip(".").upper() for item in ALLOWED_EXTENSIONS)
        raise UnsupportedMediaError(
            f"Formato no permitido. Usa uno de: {allowed}."
        )
    mime = (content_type or "").split(";")[0].strip().lower()
    if mime not in ALLOWED_MIME_TYPES and mime not in GENERIC_MIME_TYPES:
        raise UnsupportedMediaError(
            "El tipo MIME del archivo no corresponde a un audio permitido."
        )
    return suffix


async def _save_upload(file: UploadFile, destination: Path, settings: Settings) -> int:
    total = 0
    with destination.open("wb") as output:
        while True:
            chunk = await file.read(MAX_UPLOAD_CHUNK)
            if not chunk:
                break
            total += len(chunk)
            if total > settings.max_upload_bytes:
                raise AudioTooLargeError(settings.max_upload_mb)
            output.write(chunk)
    if total == 0:
        raise InvalidAudioError("El archivo de audio está vacío.")
    return total


def _cleanup_loop(store: ResultStore, interval_seconds: int) -> asyncio.Task:
    async def loop() -> None:
        while True:
            try:
                removed = await asyncio.to_thread(store.cleanup)
                if removed:
                    logger.info("Resultados temporales eliminados: %s", removed)
            except Exception:
                logger.exception("Fallo al limpiar resultados temporales.")
            await asyncio.sleep(interval_seconds)

    return asyncio.create_task(loop(), name="result-cleanup")


def create_app(
    settings: Settings | None = None,
    processor: Callable[[str, str], dict[str, Any]] | None = None,
) -> FastAPI:
    settings = settings or Settings.from_env()
    store = ResultStore(settings.result_dir, settings.result_ttl_seconds)
    pipeline = PipelineService(settings, store, processor=processor)
    cleanup_task: asyncio.Task | None = None

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        nonlocal cleanup_task
        settings.result_dir.mkdir(parents=True, exist_ok=True)
        removed = await asyncio.to_thread(store.cleanup)
        if removed:
            logger.info("Resultados vencidos al iniciar: %s", removed)
        if not settings.xtts_license_accepted:
            logger.warning(
                "COQUI_TOS_AGREED != 1: /status estará degradado y XTTS fallará."
            )
        cleanup_task = _cleanup_loop(store, settings.cleanup_interval_seconds)
        logger.info("API iniciada en modo de inferencia secuencial.")
        yield
        if cleanup_task is not None:
            cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await cleanup_task

    app = FastAPI(
        title="Hilo — API de traducción de voz ES→EN",
        description=(
            "Expone el pipeline Whisper Small → MarianMT base → XTTS-v2 → ECAPA. "
            "La inferencia es secuencial y los resultados expiran automáticamente. "
            "No se almacenan audios de forma permanente."
        ),
        version=settings.version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.store = store
    app.state.pipeline = pipeline

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID", "Content-Disposition"],
        max_age=600,
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", "")
        if not request_id or len(request_id) > 64 or not request_id.isalnum():
            request_id = uuid.uuid4().hex
        request.state.request_id = request_id
        started = time.perf_counter()

        if request.url.path == f"{API_PREFIX}/translate":
            raw_length = request.headers.get("content-length")
            if raw_length:
                try:
                    declared_length = int(raw_length)
                except ValueError:
                    declared_length = 0
                if declared_length > settings.max_upload_bytes + 2 * 1024 * 1024:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": {
                                "code": "file_too_large",
                                "message": f"El archivo supera el límite de {settings.max_upload_mb} MB.",
                                "request_id": request_id,
                            }
                        },
                        headers={
                            "X-Request-ID": request_id,
                            "X-Content-Type-Options": "nosniff",
                        },
                    )

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        logger.info(
            "%s %s -> %s (%.0f ms) request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            (time.perf_counter() - started) * 1000,
            request_id,
        )
        return response

    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, error: APIError):
        return _error_response(request, error)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, error: RequestValidationError):
        is_file_error = any("file" in [str(part) for part in item.get("loc", [])] for item in error.errors())
        message = (
            "Debes adjuntar un archivo de audio en el campo 'file'."
            if is_file_error
            else "La solicitud no es válida."
        )
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_error",
                    "message": message,
                    "request_id": getattr(request.state, "request_id", None),
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, error: Exception):
        request_id = getattr(request.state, "request_id", None)
        logger.exception("Error no controlado request_id=%s", request_id)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "Ocurrió un error interno. Intenta nuevamente.",
                    "request_id": request_id,
                }
            },
        )

    @app.get(
        "/health",
        response_model=HealthResponse,
        tags=["Sistema"],
        summary="Comprobación de disponibilidad",
    )
    async def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            service=settings.service_name,
            version=settings.version,
        )

    @app.get(
        f"{API_PREFIX}/status",
        response_model=StatusResponse,
        responses={503: {"model": ErrorResponse}},
        tags=["Sistema"],
        summary="Estado del pipeline sin cargar modelos",
    )
    async def status() -> StatusResponse:
        gpu, device = _gpu_info()
        state = pipeline.status()
        ready = settings.xtts_license_accepted
        return StatusResponse(
            status="ok" if ready else "degraded",
            service=settings.service_name,
            version=settings.version,
            timestamp=_utc_now(),
            pipeline=PipelineStatus(
                ready=ready,
                busy=state["busy"],
                warm=state["warm"],
                mode=state["mode"],
                device=device,
                gpu=gpu,
                xtts_license_accepted=settings.xtts_license_accepted,
                requests_total=state["requests_total"],
                completed_total=state["completed_total"],
                last_error_code=state["last_error_code"],
                last_completed_at=state["last_completed_at"],
                models=MODEL_SUMMARY,
            ),
            limits=LimitsInfo(
                max_upload_mb=settings.max_upload_mb,
                max_audio_seconds=settings.max_audio_seconds,
                result_ttl_seconds=settings.result_ttl_seconds,
            ),
            capabilities=CapabilitiesInfo(
                translation_direction="es-en",
                speaker_similarity=True,
                background_jobs=False,
            ),
        )

    @app.post(
        f"{API_PREFIX}/translate",
        response_model=TranslateResponse,
        responses={
            413: {"model": ErrorResponse},
            415: {"model": ErrorResponse},
            422: {"model": ErrorResponse},
            500: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
        tags=["Traducción"],
        summary="Sube un audio en español y ejecuta el pipeline completo",
    )
    async def translate(
        file: Annotated[UploadFile, File()],
    ) -> TranslateResponse:
        if not settings.xtts_license_accepted:
            raise ModelUnavailableError(
                "XTTS-v2 no está habilitado. El operador debe aceptar la licencia "
                "CPML configurando COQUI_TOS_AGREED=1."
            )
        suffix = _validate_upload_metadata(file.filename, file.content_type)
        job_id = uuid.uuid4().hex
        directory = store.new_job_dir(job_id)
        upload_path = directory / f"upload{suffix}"
        try:
            await _save_upload(file, upload_path, settings)
        except APIError:
            store.delete(job_id)
            raise
        except Exception as error:
            store.delete(job_id)
            logger.exception("No se pudo guardar la subida del trabajo %s", job_id)
            raise InvalidAudioError(
                "No se pudo recibir el archivo de audio completo."
            ) from error
        finally:
            await file.close()

        result = await pipeline.translate(job_id, upload_path)
        return TranslateResponse(**result)

    @app.get(
        f"{RESULT_URL_PREFIX}/{{result_id}}/audio",
        responses={
            200: {"content": {"audio/wav": {}}},
            404: {"model": ErrorResponse},
        },
        tags=["Resultados"],
        summary="Reproduce o descarga el audio traducido",
        response_class=FileResponse,
    )
    async def result_audio(result_id: str, download: bool = False):
        stored = store.audio_path(result_id)
        if stored is None:
            raise ResultNotFoundError()
        path, payload = stored
        filename = str(payload.get("audio", {}).get("filename", "hilo_en.wav"))
        return FileResponse(
            path,
            media_type="audio/wav",
            filename=filename,
            content_disposition_type="attachment" if download else "inline",
            headers={
                "Cache-Control": "private, no-store",
                "X-Content-Type-Options": "nosniff",
            },
        )

    return app


app = create_app()
