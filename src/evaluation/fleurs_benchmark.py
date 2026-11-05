"""Evaluación Speech-to-Speech sobre el split oficial de test de FLEURS es_419.

Este módulo sustituye la reserva histórica construida sobre ``train``. La
reserva nueva se genera desde ``test``, exige referencias inglesas oficiales y
descarta audios vacíos, demasiado cortos o silenciosos antes de ejecutar el
pipeline.
"""

from __future__ import annotations

import json
import platform
import string
import subprocess
import time
from pathlib import Path
from typing import Any

import jiwer
import numpy as np
import pandas as pd
import sacrebleu
import soundfile as sf

from src.dataset.fleurs import (
    FLEURS_CONFIG_ES,
    decode_audio,
    stream_fleurs,
)
from src.dataset.manifest import load_fleurs_english_references
from src.paths import PROJECT_ROOT
from src.pipeline import runner as pipeline_runner
from src.voice_cloning.audio import validate_audio

OFFICIAL_SPLIT = "test"
DEFAULT_N_SAMPLES = 20
DEFAULT_SAMPLE_PREFIX = "fleurs_es_419_test"
MIN_DURATION_SEC = 1.0
MIN_RMS = 1e-4

RESERVATION_COLUMNS = [
    "sample_id",
    "sentence_id",
    "split",
    "source_split",
    "reference_es",
    "reference_en",
    "duration_sec",
    "sample_rate",
    "peak",
    "rms",
]


def _relative_path(path: Path) -> str:
    """Ruta relativa al repositorio cuando sea posible; nunca absoluta en JSON."""
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.name


def normalize_orthographic(text: str) -> str:
    """Normaliza puntuación y espacios para WER normalizado."""
    punctuation = string.punctuation + "¡¿"
    return " ".join(
        str(text).lower().translate(str.maketrans("", "", punctuation)).split()
    )


def _quality(array: np.ndarray, sample_rate: int) -> dict[str, float]:
    signal = np.asarray(array, dtype=np.float32)
    if signal.ndim == 2:
        signal = signal.mean(axis=1, dtype=np.float32)
    if signal.ndim != 1 or signal.size == 0 or sample_rate <= 0:
        raise ValueError("Audio vacío o con forma inválida.")
    duration = float(signal.size) / float(sample_rate)
    peak = float(np.max(np.abs(signal)))
    rms = float(np.sqrt(np.mean(np.square(signal, dtype=np.float64))))
    return {
        "duration_sec": round(duration, 3),
        "peak": peak,
        "rms": rms,
    }


def _quality_problem(quality: dict[str, float]) -> str | None:
    if quality["duration_sec"] < MIN_DURATION_SEC:
        return f"duración {quality['duration_sec']:.3f}s < {MIN_DURATION_SEC}s"
    if quality["rms"] < MIN_RMS:
        return f"RMS {quality['rms']:.8f} < {MIN_RMS}"
    if quality["peak"] > 1.0001:
        return f"peak {quality['peak']:.4f} fuera de rango"
    return None


def build_official_reservation(
    output_path: str | Path,
    n_samples: int = DEFAULT_N_SAMPLES,
    split: str = OFFICIAL_SPLIT,
    config: str = FLEURS_CONFIG_ES,
    sample_prefix: str = DEFAULT_SAMPLE_PREFIX,
) -> pd.DataFrame:
    """Construye una reserva determinista desde el split oficial indicado.

    Toma las primeras ``n_samples`` muestras válidas, no las primeras muestras
    sin comprobar. Las muestras descartadas se devuelven en la columna de
    auditoría del propio proceso y se informan por consola.
    """
    if split != "test":
        raise ValueError(
            "La evaluación final debe usar el split oficial `test`; "
            f"se recibió {split!r}."
        )

    references_en = load_fleurs_english_references()
    stream = stream_fleurs(config=config, split=split)
    rows: list[dict[str, Any]] = []
    skipped: list[str] = []

    for sample in stream:
        sentence_id = str(sample["id"])
        reference_en = references_en.get(sentence_id, "").strip()
        if not reference_en:
            skipped.append(f"{sentence_id}: sin referencia inglesa")
            continue
        try:
            audio, sample_rate = decode_audio(sample["audio"])
            quality = _quality(audio, sample_rate)
        except (ValueError, OSError) as error:
            skipped.append(f"{sentence_id}: audio ilegible ({error})")
            continue
        problem = _quality_problem(quality)
        if problem:
            skipped.append(f"{sentence_id}: {problem}")
            continue
        reference_es = str(
            sample.get("raw_transcription") or sample.get("transcription") or ""
        ).strip()
        if not reference_es:
            skipped.append(f"{sentence_id}: sin transcripción española")
            continue
        rows.append(
            {
                "sample_id": f"{sample_prefix}_{len(rows):04d}",
                "sentence_id": sentence_id,
                "split": "test",
                "source_split": split,
                "reference_es": reference_es,
                "reference_en": reference_en,
                "sample_rate": int(sample_rate),
                **quality,
            }
        )
        if len(rows) == n_samples:
            break

    if len(rows) != n_samples:
        raise RuntimeError(
            f"Solo se encontraron {len(rows)} muestras válidas de {n_samples}. "
            f"Descartadas: {skipped}"
        )

    frame = pd.DataFrame(rows, columns=RESERVATION_COLUMNS)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        raise FileExistsError(
            f"La reserva ya existe y no se sobrescribe: {output_path}"
        )
    frame.to_csv(output_path, index=False, encoding="utf-8")
    print(f"Reserva oficial FLEURS {split}: {len(frame)} muestras -> {output_path}")
    if skipped:
        print("Muestras descartadas durante la reserva:")
        for item in skipped:
            print(" -", item)
    return frame


def load_reservation(path: str | Path) -> pd.DataFrame:
    """Carga y valida la reserva oficial sin aceptar splits mezclados."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"No existe la reserva FLEURS: {path}")
    frame = pd.read_csv(path, dtype={"sentence_id": str})
    required = set(RESERVATION_COLUMNS)
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"La reserva no tiene las columnas requeridas: {sorted(missing)}")
    if frame["sample_id"].duplicated().any():
        raise ValueError("La reserva contiene sample_id duplicados.")
    if frame["sentence_id"].duplicated().any():
        raise ValueError("La reserva contiene sentence_id duplicados.")
    if frame["source_split"].nunique() != 1:
        raise ValueError("La reserva mezcla particiones oficiales.")
    if frame["source_split"].iat[0] != OFFICIAL_SPLIT:
        raise ValueError(
            "La reserva debe provenir del split oficial `test`; "
            f"se encontró {frame['source_split'].iat[0]!r}."
        )
    return frame


def _fetch_audio_samples(sentence_ids: set[str], split: str) -> dict[str, Any]:
    from datasets import Audio, load_dataset

    dataset = load_dataset(
        "google/fleurs",
        FLEURS_CONFIG_ES,
        split=split,
        streaming=True,
    ).cast_column("audio", Audio(decode=False))
    found: dict[str, Any] = {}
    for sample in dataset:
        sentence_id = str(sample["id"])
        if sentence_id in sentence_ids:
            found[sentence_id] = sample
            if len(found) == len(sentence_ids):
                break
    missing = sorted(sentence_ids.difference(found))
    if missing:
        raise RuntimeError("No se reconstruyeron los IDs reservados: " + ", ".join(missing))
    return found


def _git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _environment(run_dir: Path, reservation_path: Path) -> dict[str, Any]:
    from importlib import metadata

    import torch

    def version(name: str) -> str | None:
        try:
            return metadata.version(name)
        except metadata.PackageNotFoundError:
            return None

    environment = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python": platform.python_version(),
        "operating_system": platform.platform(),
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "torch": torch.__version__,
        "cuda": torch.version.cuda,
        "torch_cuda_available": torch.cuda.is_available(),
        "transformers": version("transformers"),
        "datasets": version("datasets"),
        "sacrebleu": version("sacrebleu"),
        "jiwer": version("jiwer"),
        "coqui_tts": version("coqui-tts"),
        "speechbrain": version("speechbrain"),
        "numpy": version("numpy"),
        "git_commit": _git_commit(),
        "reservation": _relative_path(reservation_path),
    }
    (run_dir / "environment.json").write_text(
        json.dumps(environment, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return environment


def run_benchmark(
    reservation_path: str | Path,
    output_dir: str | Path,
    limit: int | None = None,
    translation_model_name_or_path: str | None = None,
) -> dict[str, Any]:
    """Ejecuta el pipeline real y calcula las métricas de Dataset B.

    El directorio de salida debe ser nuevo para no sobrescribir evidencias
    anteriores. Cada muestra se valida antes de entrar al pipeline. Las muestras
    inválidas se registran en ``exclusions.csv`` y no se incluyen en las medias.
    """
    reservation_path = Path(reservation_path)
    run_dir = Path(output_dir)
    if run_dir.exists():
        raise FileExistsError(
            f"El directorio de resultados ya existe; no se sobrescribe: {run_dir}"
        )
    run_dir.mkdir(parents=True)
    audio_dir = run_dir / "audio_original"
    pipeline_dir = run_dir / "pipeline"
    audio_dir.mkdir()
    pipeline_dir.mkdir()

    reservation = load_reservation(reservation_path)
    if limit is not None:
        reservation = reservation.head(limit).copy()
    environment = _environment(run_dir, reservation_path)

    found = _fetch_audio_samples(
        set(reservation["sentence_id"]), reservation["source_split"].iat[0]
    )

    results: list[dict[str, Any]] = []
    exclusions: list[dict[str, str]] = []
    processed_rows: list[pd.Series] = []

    for row in reservation.itertuples(index=False):
        sample = found[row.sentence_id]
        try:
            audio, sample_rate = decode_audio(sample["audio"])
            quality = _quality(audio, sample_rate)
            problem = _quality_problem(quality)
            if problem:
                exclusions.append(
                    {
                        "sample_id": row.sample_id,
                        "sentence_id": row.sentence_id,
                        "reason": problem,
                    }
                )
                continue
            input_wav = audio_dir / f"{row.sample_id}.wav"
            sf.write(input_wav, audio, sample_rate, subtype="FLOAT")
            validate_audio(
                input_wav,
                min_duration_sec=MIN_DURATION_SEC,
                min_rms=MIN_RMS,
            )
        except (ValueError, OSError) as error:
            exclusions.append(
                {
                    "sample_id": row.sample_id,
                    "sentence_id": row.sentence_id,
                    "reason": str(error),
                }
            )
            continue

        sample_output = pipeline_dir / row.sample_id
        try:
            result = pipeline_runner.process_audio(
                str(input_wav),
                str(sample_output),
                translation_model_name_or_path=translation_model_name_or_path,
            )
        except Exception as error:  # noqa: BLE001 - se documenta y se continúa
            exclusions.append(
                {
                    "sample_id": row.sample_id,
                    "sentence_id": row.sentence_id,
                    "reason": f"{type(error).__name__}: {error}",
                }
            )
            continue

        processed_rows.append(row)
        results.append(
            {
                "sample_id": row.sample_id,
                "sentence_id": row.sentence_id,
                "run_regime": "cold" if not results else "hot",
                "duration_sec": quality["duration_sec"],
                "reference_es": row.reference_es,
                "reference_en": row.reference_en,
                "transcription_es": result["transcription_es"],
                "translation_en": result["translation_en"],
                "wer_raw": float(jiwer.wer(row.reference_es, result["transcription_es"])),
                "wer_normalized": float(
                    jiwer.wer(
                        normalize_orthographic(row.reference_es),
                        normalize_orthographic(result["transcription_es"]),
                    )
                ),
                "cer": float(jiwer.cer(row.reference_es, result["transcription_es"])),
                "speaker_similarity": float(result["speaker_similarity"]),
                "asr_sec": float(result["timings"]["asr_sec"]),
                "nmt_sec": float(result["timings"]["translation_sec"]),
                "xtts_sec": float(result["timings"]["xtts_sec"]),
                "ecapa_sec": float(result["timings"]["speaker_evaluation_sec"]),
                "total_sec": float(result["timings"]["total_sec"]),
                "rtf": float(result["rtf_total"]),
                "translation_model": result["models"]["translation"],
                "translation_checkpoint": result["models"]["translation_checkpoint"],
            }
        )
        print(
            f"{row.sample_id}: WER={results[-1]['wer_raw']:.4f} "
            f"ECAPA={results[-1]['speaker_similarity']:.4f} "
            f"RTF={results[-1]['rtf']:.4f}"
        )

    if not results:
        raise RuntimeError("No se procesó ninguna muestra válida de la reserva.")

    results_frame = pd.DataFrame(results)
    pd.DataFrame(
        exclusions,
        columns=["sample_id", "sentence_id", "reason"],
    ).to_csv(run_dir / "exclusions.csv", index=False, encoding="utf-8")

    # NMT aislada: traduce las referencias españolas, sin errores de ASR.
    translator = pipeline_runner._COMPONENTS["translator"]
    isolated_predictions = translator.translate_batch(
        [row.reference_es for row in processed_rows],
        batch_size=16,
        max_length=128,
        num_beams=4,
    )
    results_frame["translation_isolated_en"] = isolated_predictions
    references_en = [row.reference_en for row in processed_rows]
    references_es = [row.reference_es for row in processed_rows]

    hot = results_frame[results_frame["run_regime"] == "hot"]
    aggregate = {
        "dataset": "google/fleurs",
        "config": FLEURS_CONFIG_ES,
        "official_split": OFFICIAL_SPLIT,
        "reservation": _relative_path(reservation_path),
        "num_reserved": len(reservation),
        "num_evaluated": len(results_frame),
        "num_excluded": len(exclusions),
        "wer_raw_mean": float(results_frame["wer_raw"].mean()),
        "wer_normalized_mean": float(results_frame["wer_normalized"].mean()),
        "cer_mean": float(results_frame["cer"].mean()),
        "sacrebleu_isolated": float(
            sacrebleu.corpus_bleu(isolated_predictions, [references_en]).score
        ),
        "chrf_isolated": float(
            sacrebleu.corpus_chrf(isolated_predictions, [references_en]).score
        ),
        "sacrebleu_pipeline": float(
            sacrebleu.corpus_bleu(
                results_frame["translation_en"].tolist(), [references_en]
            ).score
        ),
        "chrf_pipeline": float(
            sacrebleu.corpus_chrf(
                results_frame["translation_en"].tolist(), [references_en]
            ).score
        ),
        "speaker_similarity_mean": float(results_frame["speaker_similarity"].mean()),
        "speaker_similarity_median": float(
            results_frame["speaker_similarity"].median()
        ),
        "speaker_similarity_min": float(results_frame["speaker_similarity"].min()),
        "speaker_similarity_max": float(results_frame["speaker_similarity"].max()),
        "speaker_similarity_std": float(
            results_frame["speaker_similarity"].std(ddof=0)
        ),
        "total_time_mean": float(results_frame["total_sec"].mean()),
        "rtf_hot_mean": float(hot["rtf"].mean()) if not hot.empty else None,
        "translation_model": str(results_frame["translation_model"].iat[0]),
        "translation_checkpoint": str(
            results_frame["translation_checkpoint"].iat[0]
        ),
        "git_commit": environment.get("git_commit"),
    }

    results_frame.to_csv(run_dir / "results_per_sample.csv", index=False, encoding="utf-8")
    (run_dir / "aggregate_metrics.json").write_text(
        json.dumps(aggregate, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    summary = {
        "reservation_file": _relative_path(reservation_path),
        "official_split": OFFICIAL_SPLIT,
        "num_samples": len(reservation),
        "num_evaluated": len(results_frame),
        "num_excluded": len(exclusions),
        "excluded": exclusions,
        "reference_es_available": len(references_es),
        "git_commit": environment.get("git_commit"),
    }
    (run_dir / "dataset_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return aggregate


def write_report(run_dir: str | Path) -> Path:
    """Genera un reporte Markdown autocontenido a partir de los JSON del run."""
    run_dir = Path(run_dir)
    aggregate = json.loads((run_dir / "aggregate_metrics.json").read_text(encoding="utf-8"))
    exclusions_path = run_dir / "exclusions.csv"
    exclusions = (
        pd.read_csv(exclusions_path)
        if exclusions_path.exists() and exclusions_path.stat().st_size > 0
        else pd.DataFrame()
    )
    report = f"""# Evaluación Dataset B — FLEURS es_419

## Configuración

- Split oficial: `{aggregate['official_split']}`
- Reserva: `{aggregate['reservation']}`
- Muestras reservadas: {aggregate['num_reserved']}
- Muestras evaluadas: {aggregate['num_evaluated']}
- Muestras excluidas: {aggregate['num_excluded']}
- Modelo NMT: `{aggregate['translation_model']}` ({aggregate['translation_checkpoint']})
- Commit: `{aggregate['git_commit']}`

## Métricas

| Métrica | Valor |
|---|---:|
| WER raw | {aggregate['wer_raw_mean']:.6f} |
| WER normalizado | {aggregate['wer_normalized_mean']:.6f} |
| CER | {aggregate['cer_mean']:.6f} |
| BLEU aislado | {aggregate['sacrebleu_isolated']:.4f} |
| chrF aislado | {aggregate['chrf_isolated']:.4f} |
| BLEU pipeline | {aggregate['sacrebleu_pipeline']:.4f} |
| chrF pipeline | {aggregate['chrf_pipeline']:.4f} |
| ECAPA media | {aggregate['speaker_similarity_mean']:.4f} |
| ECAPA mediana | {aggregate['speaker_similarity_median']:.4f} |
| RTF hot medio | {aggregate['rtf_hot_mean']} |

## Exclusiones

{exclusions.to_string(index=False) if not exclusions.empty else 'Ninguna.'}

## Limitaciones

- FLEURS no expone `speaker_id`; no se puede medir leakage de hablante.
- La similitud ECAPA es coseno continuo, no un porcentaje de voz conservada.
- No se realizó evaluación MOS.
- El pipeline no es de transmisión en tiempo real.
"""
    path = run_dir / "REPORTE_DATASET_B.md"
    path.write_text(report, encoding="utf-8")
    return path
