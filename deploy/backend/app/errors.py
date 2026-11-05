"""Errores de dominio con códigos HTTP y mensajes seguros para el cliente."""

from __future__ import annotations


class APIError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        *,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.headers = headers or {}


class UnsupportedMediaError(APIError):
    def __init__(self, message: str = "Formato de audio no permitido.") -> None:
        super().__init__(415, "unsupported_media_type", message)


class InvalidAudioError(APIError):
    def __init__(self, message: str = "No se pudo leer el archivo de audio.") -> None:
        super().__init__(422, "invalid_audio", message)


class AudioTooLargeError(APIError):
    def __init__(self, max_mb: int) -> None:
        super().__init__(
            413,
            "file_too_large",
            f"El archivo supera el límite de {max_mb} MB.",
        )


class AudioTooLongError(APIError):
    def __init__(self, max_seconds: float) -> None:
        super().__init__(
            422,
            "audio_too_long",
            f"El audio supera la duración máxima de {max_seconds:g} segundos.",
        )


class ResultNotFoundError(APIError):
    def __init__(self, message: str = "El resultado no existe o expiró.") -> None:
        super().__init__(404, "result_not_found", message)


class ModelUnavailableError(APIError):
    def __init__(self, message: str) -> None:
        super().__init__(503, "model_unavailable", message)


class PipelineFailureError(APIError):
    def __init__(self) -> None:
        super().__init__(
            500,
            "pipeline_error",
            "El procesamiento falló. Intenta con otro audio o más tarde.",
        )
