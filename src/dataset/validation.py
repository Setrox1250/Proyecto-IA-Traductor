"""Validación automática del dataset de evaluación Speech-to-Speech.

Comprueba que cada fila del manifest `evaluation_v1.csv` pueda usarse después
por ASR, traducción (NMT) y voice cloning: audio existente y abrible, sin vacíos,
sin duplicados y sin filtración (leakage) de hablantes entre dev/test.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

SEED = 42


def resolve_audio_path(audio_path: str, audio_root: str | Path) -> Path:
    """Resuelve la ruta del audio: si es relativa, la ancla en audio_root."""
    path = Path(str(audio_path))
    if path.is_absolute():
        return path
    return Path(audio_root) / path


def check_audio_file(audio_path: str, audio_root: str | Path) -> dict:
    """Inspecciona un archivo de audio con soundfile (sin cargarlo en memoria)."""
    import soundfile as sf

    path = resolve_audio_path(audio_path, audio_root)
    result = {
        "audio_exists": path.exists(),
        "audio_openable": False,
        "sample_rate": None,
        "duration_sec": None,
        "is_empty_audio": None,
    }
    if not result["audio_exists"]:
        return result
    try:
        info = sf.info(path)
        result["audio_openable"] = True
        result["sample_rate"] = int(info.samplerate)
        result["duration_sec"] = round(float(info.frames) / float(info.samplerate), 3)
        result["is_empty_audio"] = bool(info.frames == 0)
    except Exception:
        result["audio_openable"] = False
    return result


def validate_manifest(df: pd.DataFrame, audio_root: str | Path) -> pd.DataFrame:
    """Devuelve un DataFrame con un chequeo por fila.

    Columnas por fila: audio_exists, audio_openable, sample_rate, duration_sec,
    is_empty_audio, has_transcription, has_translation, duplicate_transcription.
    """
    df = df.reset_index(drop=True)
    duplicated_id = df["sample_id"].duplicated(keep=False)
    duplicated_text = df["transcription_es"].duplicated(keep=False)

    rows = []
    for i, row in df.iterrows():
        audio = check_audio_file(str(row["audio_path"]), audio_root)
        transcription = str(row["transcription_es"]).strip() if pd.notna(row["transcription_es"]) else ""
        translation = str(row["translation_en"]).strip() if pd.notna(row["translation_en"]) else ""
        rows.append(
            {
                "sample_id": row["sample_id"],
                "split": row.get("split", ""),
                "speaker_id": row["speaker_id"] if "speaker_id" in df.columns else None,
                **audio,
                "duplicate_id": bool(duplicated_id.iloc[i]),
                "has_transcription": bool(transcription != ""),
                "has_translation": bool(translation != ""),
                "duplicate_transcription": bool(duplicated_text.iloc[i]),
            }
        )
    return pd.DataFrame(rows)


def check_speaker_leakage(df: pd.DataFrame) -> list[str]:
    """Hablantes que aparecen en dev AND test (leakage de hablante).

    Si no existe `speaker_id` vuelve lista vacía (no se puede evaluar leakage).
    """
    if "speaker_id" not in df.columns or "split" not in df.columns:
        return []
    if df["speaker_id"].isna().all():
        return []
    by_split = {}
    for split in df["split"].dropna().unique():
        by_split[split] = set(
            df.loc[df["split"] == split, "speaker_id"].dropna().astype(str).unique()
        )
    if "dev" in by_split and "test" in by_split:
        return sorted(by_split["dev"] & by_split["test"])
    return []


def build_summary(df: pd.DataFrame, check: pd.DataFrame, leakage: list[str]) -> pd.DataFrame:
    """Resumen agregado de la validación en forma de DataFrame."""
    durations = check["duration_sec"].dropna()

    def _count(column: str, value: bool = True) -> int:
        return int((check[column] == value).sum())

    rows = [
        ("num_samples", len(df)),
        ("num_audio_missing", _count("audio_exists", False)),
        ("num_audio_unopenable", _count("audio_openable", False)),
        ("num_empty_audio", _count("is_empty_audio", True)),
        ("num_duplicate_ids", _count("duplicate_id", True)),
        ("num_missing_transcription", _count("has_transcription", False)),
        ("num_missing_translation", _count("has_translation", False)),
        ("num_duplicate_transcriptions", _count("duplicate_transcription", True)),
        ("splits_dev", int((check["split"] == "dev").sum())),
        ("splits_test", int((check["split"] == "test").sum())),
        ("num_speakers", int(df["speaker_id"].nunique()) if "speaker_id" in df.columns and df["speaker_id"].notna().any() else "No disponible (FLEURS no expone speaker_id)"),
        ("leakage_speakers_count", len(leakage)),
        ("leakage_speakers_list", "; ".join(leakage) if leakage else ""),
        ("duration_min_sec", round(float(durations.min()), 3) if len(durations) else None),
        ("duration_max_sec", round(float(durations.max()), 3) if len(durations) else None),
        ("duration_mean_sec", round(float(durations.mean()), 3) if len(durations) else None),
        ("sample_rates", "; ".join(sorted({str(sr) for sr in check["sample_rate"].dropna().unique()}))),
    ]
    return pd.DataFrame(rows, columns=["metric", "value"])


def save_validation_files(
    check: pd.DataFrame,
    summary: pd.DataFrame,
    csv_out: str | Path = "outputs/dataset/dataset_validation.csv",
    txt_out: str | Path = "outputs/dataset/dataset_validation_summary.txt",
) -> tuple[Path, Path]:
    """Guarda el reporte de validación por fila (CSV) y el resumen (TXT)."""
    csv_out = Path(csv_out)
    txt_out = Path(txt_out)
    csv_out.parent.mkdir(parents=True, exist_ok=True)
    txt_out.parent.mkdir(parents=True, exist_ok=True)

    check.to_csv(csv_out, index=False, encoding="utf-8")

    lines = ["DATASET EVALUATION - REPORTE DE VALIDACIÓN", "=" * 42, ""]
    for _, row in summary.iterrows():
        lines.append(f"{str(row['metric'])}: {row['value']}")
    lines.append("")
    lines.append("Chequeo por fila: dataset_validation.csv (mismo directorio)")
    txt_out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Reporte por fila guardado en {csv_out}")
    print(f"Resumen guardado en {txt_out}")
    return csv_out, txt_out