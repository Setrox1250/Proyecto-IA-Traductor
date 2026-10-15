"""Orquestación reproducible del pipeline Speech-to-Speech base."""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Any, Callable

import soundfile as sf

from src.asr.transcribe import WhisperTranscriber
from src.evaluation.speaker_similarity import MODEL_ID as ECAPA_MODEL_ID
from src.evaluation.speaker_similarity import speaker_similarity
from src.translation.model import DEFAULT_MODEL_NAME, MarianTranslator
from src.voice_cloning.audio import prepare_audio_copy, prepare_reference_audio, validate_audio
from src.voice_cloning.synthesize import DEFAULT_MODEL_ID, synthesize


_COMPONENTS: dict[str, Any] | None = None


def _get_pipeline_components() -> dict[str, Any]:
    """Inicializa una vez los modelos pesados para ejecuciones consecutivas."""
    global _COMPONENTS
    if _COMPONENTS is None:
        _COMPONENTS = {
            "asr": WhisperTranscriber(),
            "translator": MarianTranslator(model_name_or_path=DEFAULT_MODEL_NAME),
            "synthesize": synthesize,
            "speaker_similarity": speaker_similarity,
        }
    return _COMPONENTS


def _copy_master_audio(input_audio: Path, output_path: Path) -> None:
    """Conserva una copia auditable del input, sin tocar el archivo original."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if input_audio.suffix.lower() == ".wav":
        shutil.copy2(input_audio, output_path)
        return
    # La demo admite MP3 si libsndfile puede decodificarlo; se materializa WAV.
    audio, sample_rate = sf.read(input_audio, dtype="float32", always_2d=False)
    sf.write(output_path, audio, sample_rate, format="WAV", subtype="FLOAT")


def _find_reference_transcription(input_audio: Path, output_dir: Path) -> str | None:
    """Busca una referencia opcional sin exigirla al contrato público."""
    candidates = (
        input_audio.with_suffix(input_audio.suffix + ".txt"),
        input_audio.with_suffix(".txt"),
        output_dir / "reference_transcription.txt",
    )
    for candidate in candidates:
        if candidate.exists():
            text = candidate.read_text(encoding="utf-8").strip()
            if text:
                return text
    return None


def process_audio(input_audio: str, output_dir: str) -> dict:
    """Procesa un audio español con Whisper → Marian base → XTTS → ECAPA.

    El modelo de traducción es deliberadamente el checkpoint base; el
    fine-tuning debug no es un checkpoint productivo para esta iteración.
    """
    started_at = time.perf_counter()
    source = Path(input_audio)
    destination = Path(output_dir)
    if not source.exists():
        raise FileNotFoundError(f"Archivo de entrada no encontrado: {source}")
    destination.mkdir(parents=True, exist_ok=True)

    preprocessing_start = time.perf_counter()
    master_path = destination / "input.wav"
    _copy_master_audio(source, master_path)
    master_info = validate_audio(master_path)
    asr_path = destination / "asr_input.wav"
    prepare_audio_copy(master_path, asr_path, target_sample_rate=16_000)
    reference_path = destination / "xtts_reference.wav"
    prepare_reference_audio(master_path, reference_path)
    preprocessing_sec = time.perf_counter() - preprocessing_start

    components = _get_pipeline_components()
    asr_start = time.perf_counter()
    transcription_es = components["asr"].transcribe(str(asr_path))
    asr_sec = time.perf_counter() - asr_start
    if not isinstance(transcription_es, str):
        raise TypeError("El contrato ASR debe devolver una cadena de texto.")

    translation_start = time.perf_counter()
    translation_en = components["translator"].translate(transcription_es)
    translation_sec = time.perf_counter() - translation_start
    if not isinstance(translation_en, str):
        raise TypeError("El contrato NMT debe devolver una cadena de texto.")

    output_audio = destination / "output.wav"
    xtts_start = time.perf_counter()
    output_value = components["synthesize"](
        translation_en, str(reference_path), str(output_audio), language="en"
    )
    xtts_sec = time.perf_counter() - xtts_start
    output_path = Path(output_value)
    output_info = validate_audio(output_path)

    evaluation_start = time.perf_counter()
    similarity = components["speaker_similarity"](str(master_path), str(output_path))
    speaker_evaluation_sec = time.perf_counter() - evaluation_start
    if not isinstance(similarity, (float, int)):
        raise TypeError("El contrato ECAPA debe devolver un float.")

    transcription_file = destination / "transcription.txt"
    translation_file = destination / "translation.txt"
    transcription_file.write_text(transcription_es + "\n", encoding="utf-8")
    translation_file.write_text(translation_en + "\n", encoding="utf-8")

    reference_transcription = _find_reference_transcription(source, destination)
    wer: float | None = None
    if reference_transcription:
        import jiwer

        wer = float(jiwer.wer(reference_transcription, transcription_es))

    total_sec = time.perf_counter() - started_at
    metadata = {
        # El directorio de ejecución identifica la muestra incluso si el audio
        # maestro conserva un sufijo descriptivo como ``_original``.
        "sample_id": destination.name,
        "input_audio": str(source),
        "models": {
            "asr": "openai/whisper-small",
            "translation": DEFAULT_MODEL_NAME,
            "translation_checkpoint": "base",
            "tts": DEFAULT_MODEL_ID,
            "speaker_encoder": ECAPA_MODEL_ID,
        },
        "transcription_es": transcription_es,
        "translation_en": translation_en,
        "wer": wer,
        "speaker_similarity": float(similarity),
        "audio": {
            "input_duration_sec": master_info["duration_sec"],
            "output_path": str(output_path),
            "output_sample_rate": output_info["sample_rate"],
            "output_duration_sec": output_info["duration_sec"],
        },
        "timings": {
            "preprocessing_sec": round(preprocessing_sec, 4),
            "asr_sec": round(asr_sec, 4),
            "translation_sec": round(translation_sec, 4),
            "xtts_sec": round(xtts_sec, 4),
            "speaker_evaluation_sec": round(speaker_evaluation_sec, 4),
            "total_sec": round(total_sec, 4),
        },
        "rtf_total": round(total_sec / float(master_info["duration_sec"]), 4),
    }
    (destination / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return metadata
