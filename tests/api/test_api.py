"""Pruebas de contrato de la API web con un pipeline ligero simulado."""

from __future__ import annotations

import io
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf
from app.config import Settings
from app.main import create_app
from app.result_store import ResultStore
from fastapi.testclient import TestClient


def _wav_bytes(duration: float = 1.0, sample_rate: int = 16000, silence: bool = False) -> bytes:
    samples = int(duration * sample_rate)
    if silence:
        audio = np.zeros(samples, dtype=np.float32)
    else:
        t = np.linspace(0, duration, samples, endpoint=False)
        audio = (0.12 * np.sin(2 * np.pi * 220 * t)).astype(np.float32)
    buffer = io.BytesIO()
    sf.write(buffer, audio, sample_rate, format="WAV", subtype="PCM_16")
    return buffer.getvalue()


def _fake_processor(source: str, output_dir: str) -> dict:
    output = Path(output_dir) / "output.wav"
    sf.write(output, np.zeros(24000, dtype=np.float32) + 0.01, 24000, subtype="FLOAT")
    return {
        "transcription_es": "Hola, esta es una prueba.",
        "translation_en": "Hello, this is a test.",
        "speaker_similarity": 0.57,
        "models": {
            "asr": "openai/whisper-small",
            "translation": "Helsinki-NLP/opus-mt-es-en",
            "translation_checkpoint": "base",
            "tts": "coqui/XTTS-v2",
            "speaker_encoder": "speechbrain/spkrec-ecapa-voxceleb",
        },
        "audio": {
            "input_duration_sec": 1.0,
            "output_sample_rate": 24000,
            "output_duration_sec": 1.0,
        },
        "timings": {
            "preprocessing_sec": 0.01,
            "asr_sec": 0.1,
            "translation_sec": 0.1,
            "xtts_sec": 0.2,
            "speaker_evaluation_sec": 0.1,
            "total_sec": 0.51,
        },
    }


@pytest.fixture()
def settings(tmp_path, monkeypatch) -> Settings:
    monkeypatch.setenv("COQUI_TOS_AGREED", "1")
    return Settings(
        max_upload_mb=1,
        max_audio_seconds=2.0,
        min_audio_seconds=0.5,
        result_ttl_seconds=3600,
        result_dir=tmp_path / "results",
        cleanup_interval_seconds=9999,
    )


@pytest.fixture()
def client(settings):
    app = create_app(settings=settings, processor=_fake_processor)
    with TestClient(app) as test_client:
        yield test_client


def _post_wav(client: TestClient, data: bytes, filename="sample.wav", content_type="audio/wav"):
    return client.post(
        "/api/v1/translate",
        files={"file": (filename, data, content_type)},
    )


def test_health_and_status_do_not_load_pipeline(client):
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    status = client.get("/api/v1/status")
    assert status.status_code == 200
    payload = status.json()
    assert payload["pipeline"]["ready"] is True
    assert payload["pipeline"]["busy"] is False
    assert payload["pipeline"]["models"]["translation_checkpoint"] == "base"
    assert payload["limits"]["max_upload_mb"] == 1


def test_status_degraded_without_xtts_license(settings, monkeypatch):
    monkeypatch.delenv("COQUI_TOS_AGREED", raising=False)
    app = create_app(settings=settings, processor=_fake_processor)
    with TestClient(app) as client:
        payload = client.get("/api/v1/status").json()
        assert payload["status"] == "degraded"
        assert payload["pipeline"]["ready"] is False
        assert payload["pipeline"]["xtts_license_accepted"] is False


def test_successful_translation_and_audio_download(client):
    response = _post_wav(client, _wav_bytes())
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["transcription_es"] == "Hola, esta es una prueba."
    assert payload["translation_en"] == "Hello, this is a test."
    assert payload["speaker_similarity"] == pytest.approx(0.57)
    assert payload["audio"]["url"].startswith("/api/v1/results/")
    assert payload["audio"]["filename"].endswith("_en.wav")

    audio = client.get(payload["audio"]["url"])
    assert audio.status_code == 200
    assert audio.headers["content-type"] == "audio/wav"
    assert len(audio.content) > 1000

    download = client.get(payload["audio"]["download_url"])
    assert download.status_code == 200
    assert "attachment" in download.headers["content-disposition"]


def test_empty_file_is_rejected(client):
    response = _post_wav(client, b"")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_audio"


def test_unsupported_extension_and_mime_are_rejected(client):
    extension = _post_wav(client, _wav_bytes(), filename="notes.txt", content_type="text/plain")
    assert extension.status_code == 415
    assert extension.json()["error"]["code"] == "unsupported_media_type"

    mime = _post_wav(client, _wav_bytes(), filename="notes.wav", content_type="text/plain")
    assert mime.status_code == 415


def test_missing_file_is_rejected(client):
    response = client.post("/api/v1/translate", files={})
    assert response.status_code == 422
    assert "file" in response.json()["error"]["message"]


def test_file_size_limit_is_enforced(client):
    payload = b"\x00" * (1024 * 1024 + 100)
    response = _post_wav(client, payload)
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "file_too_large"


def test_corrupt_audio_is_rejected(client):
    response = _post_wav(client, b"not-a-real-wave-file", filename="broken.wav")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_audio"


def test_audio_too_long_is_rejected(client):
    response = _post_wav(client, _wav_bytes(duration=3.0))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "audio_too_long"


def test_silent_audio_is_rejected(client):
    response = _post_wav(client, _wav_bytes(silence=True))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_audio"


def test_pipeline_failure_is_sanitized(settings):
    def failing_processor(source: str, output_dir: str):
        raise RuntimeError("internal path /secret/model failed")

    app = create_app(settings=settings, processor=failing_processor)
    with TestClient(app) as client:
        response = _post_wav(client, _wav_bytes())
        assert response.status_code == 500
        payload = response.json()
        assert payload["error"]["code"] == "pipeline_error"
        assert "/secret" not in json.dumps(payload)
        assert payload["error"]["request_id"]


def test_xtts_license_error_maps_to_503(settings):
    def failing_processor(source: str, output_dir: str):
        raise RuntimeError("XTTS requiere aceptar la licencia CPML")

    app = create_app(settings=settings, processor=failing_processor)
    with TestClient(app) as client:
        response = _post_wav(client, _wav_bytes())
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "model_unavailable"


def test_unknown_result_returns_404(client):
    response = client.get("/api/v1/results/" + "a" * 32 + "/audio")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "result_not_found"


def test_cors_only_allows_configured_origin(settings):
    app = create_app(settings=settings, processor=_fake_processor)
    with TestClient(app) as client:
        allowed = client.options(
            "/api/v1/translate",
            headers={
                "Origin": "http://localhost:8081",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert allowed.headers.get("access-control-allow-origin") == "http://localhost:8081"

        denied = client.options(
            "/api/v1/translate",
            headers={
                "Origin": "https://evil.example",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert denied.headers.get("access-control-allow-origin") is None


def test_openapi_documents_endpoints(client):
    schema = client.get("/openapi.json").json()
    assert "/health" in schema["paths"]
    assert "/api/v1/status" in schema["paths"]
    assert "/api/v1/translate" in schema["paths"]
    assert "/api/v1/results/{result_id}/audio" in schema["paths"]


def test_result_store_expires_and_removes_audio(tmp_path):
    store = ResultStore(tmp_path / "store", ttl_seconds=1)
    job_id = "b" * 32
    directory = store.new_job_dir(job_id)
    (directory / "output.wav").write_bytes(b"wav")
    store.save(job_id, {"status": "completed"})
    assert store.get(job_id) is not None

    result_file = directory / "result.json"
    payload = json.loads(result_file.read_text(encoding="utf-8"))
    payload["expires_at"] = (
        datetime.now(UTC) - timedelta(seconds=5)
    ).isoformat().replace("+00:00", "Z")
    result_file.write_text(json.dumps(payload), encoding="utf-8")

    assert store.get(job_id) is None
    assert not directory.exists()
