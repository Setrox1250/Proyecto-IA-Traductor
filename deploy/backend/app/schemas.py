"""Modelos Pydantic de la API, usados también por OpenAPI."""

from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(examples=["ok"])
    service: str = Field(examples=["hilo-translation-api"])
    version: str = Field(examples=["1.0.0"])


class ModelSummary(BaseModel):
    asr: str
    translation: str
    translation_checkpoint: str
    tts: str
    speaker_encoder: str


class GPUInfo(BaseModel):
    available: bool
    name: str | None = None
    total_memory_gb: float | None = None


class PipelineStatus(BaseModel):
    ready: bool
    busy: bool
    warm: bool
    mode: str
    device: str
    gpu: GPUInfo
    xtts_license_accepted: bool
    requests_total: int
    completed_total: int
    last_error_code: str | None = None
    last_completed_at: str | None = None
    models: ModelSummary


class LimitsInfo(BaseModel):
    max_upload_mb: int
    max_audio_seconds: float
    result_ttl_seconds: int


class CapabilitiesInfo(BaseModel):
    translation_direction: str
    speaker_similarity: bool
    background_jobs: bool = False


class StatusResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str
    pipeline: PipelineStatus
    limits: LimitsInfo
    capabilities: CapabilitiesInfo


class AudioOutput(BaseModel):
    url: str
    download_url: str
    mime_type: str
    sample_rate: int
    duration_sec: float
    filename: str


class InputAudioInfo(BaseModel):
    duration_sec: float


class Timings(BaseModel):
    preprocessing_sec: float
    asr_sec: float
    translation_sec: float
    xtts_sec: float
    speaker_evaluation_sec: float
    total_sec: float
    api_sec: float


class TranslateResponse(BaseModel):
    id: str
    status: str
    transcription_es: str
    translation_en: str
    speaker_similarity: float = Field(
        description="Similitud coseno ECAPA; no es un porcentaje de identidad."
    )
    audio: AudioOutput
    input: InputAudioInfo
    timings: Timings
    models: ModelSummary
    created_at: str
    expires_at: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
