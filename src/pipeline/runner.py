"""Orquestación reproducible del pipeline Speech-to-Speech base."""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Any

import soundfile as sf

from src.asr.transcribe import WhisperTranscriber
from src.evaluation.speaker_similarity import MODEL_ID as ECAPA_MODEL_ID
from src.evaluation.speaker_similarity import speaker_similarity
from src.paths import PROJECT_ROOT
from src.translation.model import MarianTranslator, resolve_translation_model
from src.voice_cloning.audio import (
    DEFAULT_MIN_RMS,
    prepare_audio_copy,
    prepare_reference_audio,
    validate_audio,
)
from src.voice_cloning.synthesize import DEFAULT_MODEL_ID, synthesize

MIN_INPUT_DURATION_SEC = 0.5
MIN_OUTPUT_DURATION_SEC = 0.1
MIN_OUTPUT_RMS = 1e-5

_COMPONENTS: dict[str, Any] | None = None
_COMPONENTS_KEY: tuple[str, str] | None = None


def _get_pipeline_components(
    translation_model_name_or_path: str | None = None,
) -> dict[str, Any]:
    """Inicializa una vez los modelos pesados para ejecuciones consecutivas.

    La caché se invalida si cambia el modelo/checkpoint de traducción, para que
    una ejecución con checkpoint controlado no reutilice silenciosamente el base.
    """
    global _COMPONENTS, _COMPONENTS_KEY
    model_name, checkpoint_kind = resolve_translation_model(
        translation_model_name_or_path
    )
    key = (model_name, checkpoint_kind)
    if _COMPONENTS is None or _COMPONENTS_KEY != key:
        _COMPONENTS = {
            "asr": WhisperTranscriber(),
            "translator": MarianTranslator(model_name_or_path=model_name),
            "synthesize": synthesize,
            "speaker_similarity": speaker_similarity,
            "translation_model": model_name,
            "translation_checkpoint": checkpoint_kind,
        }
        _COMPONENTS_KEY = key
    return _COMPONENTS


def _display_path(path: Path) -> str:
    """Ruta relativa al repositorio cuando sea posible; nunca abs. en metadata."""
    resolved = path.resolve()
    try:
        return resolved.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.name


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


def process_audio(
    input_audio: str,
    output_dir: str,
    translation_model_name_or_path: str | None = None,
) -> dict:
    """Procesa un audio español con Whisper → Marian → XTTS → ECAPA.

    El modelo de traducción por defecto es el checkpoint base. El checkpoint
    controlado de 10 000 pares solo se usa si se pasa explícitamente o si
    ``configs/translation.yaml`` activa ``use_controlled_checkpoint``.

    La entrada se valida antes de cargar modelos: archivos vacíos, demasiado
    cortos o silenciosos se rechazan con un error claro.
    """
    started_at = time.perf_counter()
    source = Path(input_audio)
    destination = Path(output_dir)
    if not source.exists():
        raise FileNotFoundError(f"Archivo de entrada no encontrado: {source.name}")
    destination.mkdir(parents=True, exist_ok=True)

    try:
        preprocessing_start = time.perf_counter()
        master_path = destination / "input.wav"
        _copy_master_audio(source, master_path)
        master_info = validate_audio(
            master_path,
            min_duration_sec=MIN_INPUT_DURATION_SEC,
            min_rms=DEFAULT_MIN_RMS,
        )
        asr_path = destination / "asr_input.wav"
        prepare_audio_copy(
            master_path,
            asr_path,
            target_sample_rate=16_000,
            min_duration_sec=MIN_INPUT_DURATION_SEC,
            min_rms=DEFAULT_MIN_RMS,
        )
        reference_path = destination / "xtts_reference.wav"
        prepare_reference_audio(
            master_path,
            reference_path,
            min_duration_sec=MIN_INPUT_DURATION_SEC,
            min_rms=DEFAULT_MIN_RMS,
        )
        preprocessing_sec = time.perf_counter() - preprocessing_start

        components = _get_pipeline_components(translation_model_name_or_path)
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
        output_info = validate_audio(
            output_path,
            min_duration_sec=MIN_OUTPUT_DURATION_SEC,
            min_rms=MIN_OUTPUT_RMS,
        )

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
            "input_audio": _display_path(source),
            "models": {
                "asr": "openai/whisper-small",
                "translation": components.get("translation_model"),
                "translation_checkpoint": components.get(
                    "translation_checkpoint", "base"
                ),
                "tts": DEFAULT_MODEL_ID,
                "speaker_encoder": ECAPA_MODEL_ID,
            },
            "transcription_es": transcription_es,
            "translation_en": translation_en,
            "wer": wer,
            "speaker_similarity": float(similarity),
            "audio": {
                "input_duration_sec": master_info["duration_sec"],
                "input_peak": master_info["peak"],
                "input_rms": master_info["rms"],
                "output_path": _display_path(output_path),
                "output_sample_rate": output_info["sample_rate"],
                "output_duration_sec": output_info["duration_sec"],
                "output_rms": output_info["rms"],
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
    except Exception as error:
        # Se conserva el error junto a los artefactos parciales para depuración.
        (destination / "error.json").write_text(
            json.dumps(
                {
                    "error_type": type(error).__name__,
                    "message": str(error),
                    "input_audio": _display_path(source),
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        raise
