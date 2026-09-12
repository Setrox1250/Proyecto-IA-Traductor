"""Construcción del dataset de evaluación Speech-to-Speech a partir de un manifest.

Convierte la muestra de audio (FLEURS) en el "golden dataset" del proyecto:
audio + transcripción en español + traducción de referencia al inglés + split.
La traducción de referencia se introduce de forma manual (nunca generada por el
propio modelo que luego será evaluado).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
DEV_RATIO = 0.7

EVALUATION_COLUMNS = [
    "sample_id",
    "speaker_id",
    "audio_path",
    "transcription_es",
    "translation_en",
    "duration_sec",
    "source",
    "split",
]

MANUAL_TRANSLATIONS_PATH = Path("data/processed/manifests/manual_translations.csv")
FLEURS_MANIFEST_PATH = Path("data/processed/manifests/fleurs_sample.csv")
EVALUATION_CSV = Path("data/processed/manifests/evaluation_v1.csv")


def load_manifest(path: str | Path) -> pd.DataFrame:
    """Carga un manifest (CSV) de muestras de audio."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"No existe el manifest: {path}")
    df = pd.read_csv(path, encoding="utf-8")
    if "sample_id" not in df.columns:
        raise ValueError(f"El manifest {path} no tiene la columna 'sample_id'.")
    return df


def save_manifest(df: pd.DataFrame, path: str | Path) -> Path:
    """Guarda un DataFrame como CSV (UTF-8) creando el directorio si falta."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")
    print(f"Guardado en {path}")
    return path


def load_translations_dict(path: str | Path | None = None) -> dict[str, str]:
    """Carga las traducciones manuales (CSV: sample_id, translation_en).

    Las filas con traducción vacía se ignoran, de modo que una re-ejecución del
    notebook solo aplica las traducciones ya cumplimentadas.
    """
    if path is None:
        path = MANUAL_TRANSLATIONS_PATH
    path = Path(path)
    if not path.exists():
        return {}
    df = pd.read_csv(path, encoding="utf-8")
    required = {"sample_id", "translation_en"}
    if not required.issubset(df.columns):
        raise ValueError(f"El CSV {path} debe tener las columnas {sorted(required)}.")
    df = df.rename(columns={"translation_en": "_t"})
    out = {}
    for _, row in df.iterrows():
        value = str(row["_t"]).strip() if pd.notna(row["_t"]) else ""
        if value:
            out[str(row["sample_id"]).strip()] = value
    return out


def ensure_manual_translations_file(
    manifest: pd.DataFrame, path: str | Path | None = None
) -> Path:
    """Crea el CSV de traducciones manuales si no existe (pre-rellenado vacío)."""
    if path is None:
        path = MANUAL_TRANSLATIONS_PATH
    path = Path(path)
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    df = manifest[["sample_id"]].copy()
    df["translation_en"] = ""
    df.to_csv(path, index=False, encoding="utf-8")
    print(f"Archivo de traducciones creado (vacío): {path}")
    return path


def apply_translations(manifest: pd.DataFrame, translations: dict[str, str]) -> pd.DataFrame:
    """Rellena `translation_en` desde un dict {sample_id: traducción}."""
    df = manifest.copy()
    df["translation_en"] = df["sample_id"].map(translations).fillna("")
    return df


def assign_splits(
    df: pd.DataFrame, dev_ratio: float = DEV_RATIO, seed: int = SEED
) -> pd.DataFrame:
    """Asigna split dev/test (dev_ratio ~70%).

    Si existe `speaker_id` (no es el caso en FLEURS) se dividen grupos completos
    de hablantes para evitar *leakage* entre splits. Si no existe, se barajan las
    filas con la misma semilla.
    """
    df = df.copy()
    rng = np.random.default_rng(seed)
    df["split"] = ""

    has_speaker = df["speaker_id"].notna() & (df["speaker_id"].astype(str) != "nan")

    if has_speaker.any():
        speakers = np.array(sorted(df.loc[has_speaker, "speaker_id"].unique()))
        rng.shuffle(speakers)
        n_dev_speakers = max(1, int(round(len(speakers) * dev_ratio)))
        dev_speakers = set(speakers[:n_dev_speakers].tolist())
        df.loc[has_speaker, "split"] = np.where(
            df.loc[has_speaker, "speaker_id"].isin(dev_speakers), "dev", "test"
        )

    without_speaker = df["split"] == ""
    if without_speaker.any():
        indices = np.array(df.index[without_speaker], copy=True)
        rng.shuffle(indices)
        n_dev = max(1, int(round(len(indices) * dev_ratio)))
        df.loc[indices[:n_dev], "split"] = "dev"
        df.loc[indices[n_dev:], "split"] = "test"

    return df


def assert_complete_evaluation(df: pd.DataFrame, audio_root: str | Path) -> None:
    """Valida que toda fila tenga audio existente, texto y duración válida.

    Lanza ValueError con un mensaje claro si algo falta; es la puerta de entrada
    antes de guardar el dataset dorado.
    """
    audio_root = Path(audio_root)
    problems: list[str] = []

    def _audio_exists(audio_path: str) -> bool:
        path = Path(str(audio_path))
        resolved = path if path.is_absolute() else audio_root / path
        return resolved.exists()

    missing_audio = [not _audio_exists(p) for p in df["audio_path"]]
    if any(missing_audio):
        problems.append("algún audio_path no existe (relativo a audio_root)")

    if df["transcription_es"].isna().any() or (df["transcription_es"].astype(str).str.strip() == "").any():
        problems.append("hay transcripciones en español vacías")

    if df["translation_en"].isna().any() or (df["translation_en"].astype(str).str.strip() == "").any():
        problems.append("hay traducciones de referencia vacías")

    invalid_duration = (df["duration_sec"].isna()) | (df["duration_sec"] <= 0)
    if invalid_duration.any():
        problems.append("hay duraciones inválidas (nulas o <= 0)")

    if problems:
        raise ValueError("El dataset de evaluación está incompleto:\n - " + "\n - ".join(problems))


def evaluate_manifest_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Estadísticas básicas del dataset en forma de DataFrame legible."""
    num_speakers = None
    if "speaker_id" in df.columns and df["speaker_id"].notna().any():
        num_speakers = int(df["speaker_id"].nunique())

    stats = pd.DataFrame(
        {
            "metric": [
                "num_samples",
                "total_duration_sec",
                "mean_duration_sec",
                "num_speakers",
            ],
            "value": [
                len(df),
                round(float(df["duration_sec"].sum()), 2),
                round(float(df["duration_sec"].mean()), 3),
                num_speakers,
            ],
        }
    )
    return stats


def split_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Distribución de muestras por split (dev/test)."""
    return df["split"].value_counts().rename("count").to_frame()


def save_evaluation_manifest(df: pd.DataFrame, path: str | Path) -> Path:
    """Guarda el dataset de evaluación ordenando las columnas canónicas."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    missing = [col for col in EVALUATION_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas requeridas: {missing}")
    df[EVALUATION_COLUMNS].to_csv(path, index=False, encoding="utf-8")
    print(f"Dataset de evaluación guardado en {path}")
    return path