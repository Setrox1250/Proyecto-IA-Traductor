"""Preparación reproducible del corpus paralelo textual español-inglés.

El corpus de aprendizaje es OPUS-100 (configuración ``en-es``). Se conserva la
validación y la prueba oficiales; del split de entrenamiento se toma una muestra
reproducible para que el fine-tuning posterior sea viable en Google Colab.
"""

from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

DATASET_NAME = "Helsinki-NLP/opus-100"
DATASET_CONFIG = "en-es"
SEED = 42
TRAIN_SIZE = 100_000
TRAIN_SHUFFLE_BUFFER = 10_000

OUTPUT_DIR = Path("data/processed/translation")
SPLIT_FILENAMES = {
    "train": "train.csv",
    "validation": "validation.csv",
    "test": "test.csv",
}
TEXT_COLUMNS = ["text_es", "text_en"]


def load_opus100(streaming: bool = True) -> Any:
    """Carga OPUS-100 ``en-es``; por defecto usa streaming para ahorrar RAM."""
    from datasets import load_dataset

    return load_dataset(DATASET_NAME, DATASET_CONFIG, streaming=streaming)


def normalize_text(value: object) -> str:
    """Aplica NFC y normaliza únicamente espacios, sin perder signos ni tildes."""
    if value is None:
        return ""
    text = unicodedata.normalize("NFC", str(value))
    return " ".join(text.split())


def _extract_pair(row: dict[str, Any]) -> tuple[str, str]:
    translation = row.get("translation") or {}
    return normalize_text(translation.get("es")), normalize_text(translation.get("en"))


def _clean_rows(
    rows: Iterable[dict[str, Any]],
    *,
    limit: int | None = None,
    forbidden_es: set[str] | None = None,
    forbidden_en: set[str] | None = None,
) -> pd.DataFrame:
    """Limpia pares, elimina duplicados y evita solapamientos monolingües."""
    forbidden_es = forbidden_es or set()
    forbidden_en = forbidden_en or set()
    seen_pairs: set[tuple[str, str]] = set()
    output: list[dict[str, str]] = []

    for row in rows:
        text_es, text_en = _extract_pair(row)
        pair = (text_es, text_en)
        if not text_es or not text_en or pair in seen_pairs:
            continue
        if text_es in forbidden_es or text_en in forbidden_en:
            continue
        seen_pairs.add(pair)
        output.append({"text_es": text_es, "text_en": text_en})
        if limit is not None and len(output) >= limit:
            break

    if limit is not None and len(output) < limit:
        raise ValueError(
            f"Solo se obtuvieron {len(output)} pares válidos; se solicitaron {limit}."
        )
    return pd.DataFrame(output, columns=TEXT_COLUMNS)


def prepare_opus100_splits(
    dataset: Any,
    train_size: int = TRAIN_SIZE,
    seed: int = SEED,
    shuffle_buffer: int = TRAIN_SHUFFLE_BUFFER,
) -> dict[str, pd.DataFrame]:
    """Prepara train/validation/test sin contaminación entre particiones.

    Se da prioridad a test y después a validación. El entrenamiento se baraja
    con ``seed`` y se recorre hasta reunir exactamente ``train_size`` pares.
    """
    required = {"train", "validation", "test"}
    missing = required.difference(dataset.keys())
    if missing:
        raise ValueError(f"OPUS-100 no contiene los splits esperados: {sorted(missing)}")

    test = _clean_rows(dataset["test"])
    heldout_es = set(test["text_es"])
    heldout_en = set(test["text_en"])

    validation = _clean_rows(
        dataset["validation"],
        forbidden_es=heldout_es,
        forbidden_en=heldout_en,
    )
    heldout_es.update(validation["text_es"])
    heldout_en.update(validation["text_en"])

    shuffled_train = dataset["train"].shuffle(
        seed=seed, buffer_size=shuffle_buffer
    )
    train = _clean_rows(
        shuffled_train,
        limit=train_size,
        forbidden_es=heldout_es,
        forbidden_en=heldout_en,
    )
    return {"train": train, "validation": validation, "test": test}


def save_parallel_splits(
    splits: dict[str, pd.DataFrame], output_dir: str | Path = OUTPUT_DIR
) -> dict[str, Path]:
    """Guarda los tres CSV canónicos y devuelve sus rutas."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for split, filename in SPLIT_FILENAMES.items():
        if split not in splits:
            raise ValueError(f"Falta el split requerido: {split}")
        path = output_dir / filename
        splits[split][TEXT_COLUMNS].to_csv(path, index=False, encoding="utf-8")
        paths[split] = path
        print(f"{split}: {len(splits[split])} pares -> {path}")
    return paths


def parallel_stats(splits: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Resume cantidades y porcentajes de los CSV finales."""
    total = sum(len(frame) for frame in splits.values())
    rows = []
    for split in ("train", "validation", "test"):
        count = len(splits[split])
        rows.append(
            {
                "split": split,
                "num_pairs": count,
                "percentage": round(100 * count / total, 3) if total else 0,
            }
        )
    rows.append({"split": "total", "num_pairs": total, "percentage": 100.0})
    return pd.DataFrame(rows)
