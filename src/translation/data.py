"""Preparación de datos y tokenización para fine-tuning del modelo NMT.

Carga las particiones train/validation/test de OPUS-100, aplica tokenización
con max_length determinado empíricamente y configura el DataCollatorForSeq2Seq.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from datasets import Dataset, DatasetDict, load_dataset
from transformers import AutoTokenizer, DataCollatorForSeq2Seq, PreTrainedTokenizerBase


DEFAULT_MODEL_NAME = "Helsinki-NLP/opus-mt-es-en"
DEFAULT_DATA_DIR = Path("data/processed/translation")
DEFAULT_MAX_LENGTH = 128


def load_raw_dataset(
    data_dir: Path | str = DEFAULT_DATA_DIR,
    train_limit: int | None = None,
    eval_limit: int | None = None,
    test_limit: int | None = None,
    require_local_files: bool = False,
) -> DatasetDict:
    """Carga los pares de datos desde archivos locales CSV o streaming de Hugging Face.
    
    Si require_local_files=True, exige que existan los archivos locales preparados del
    proyecto y no realiza fallback silencioso a Hugging Face.
    """
    data_dir = Path(data_dir)
    train_csv = data_dir / "train.csv"
    val_csv = data_dir / "validation.csv"
    test_csv = data_dir / "test.csv"

    if train_csv.exists() and val_csv.exists() and test_csv.exists():
        print(f"Cargando datasets desde archivos locales en {data_dir}...")
        train_df = pd.read_csv(train_csv, nrows=train_limit)
        val_df = pd.read_csv(val_csv, nrows=eval_limit)
        test_df = pd.read_csv(test_csv, nrows=test_limit)

        return DatasetDict(
            {
                "train": Dataset.from_pandas(train_df[["text_es", "text_en"]]),
                "validation": Dataset.from_pandas(val_df[["text_es", "text_en"]]),
                "test": Dataset.from_pandas(test_df[["text_es", "text_en"]]),
            }
        )

    if require_local_files:
        raise FileNotFoundError(
            f"Archivos locales requeridos no encontrados en {data_dir}. "
            "Para el entrenamiento completo se exige la presencia de train.csv, "
            "validation.csv y test.csv preparados por el pipeline del proyecto sin "
            "fallback a fuentes externas."
        )

    print("Archivos locales de traducción no encontrados. Cargando desde Hugging Face (streaming)...")
    from src.dataset.parallel import normalize_text

    raw_opus = load_dataset("Helsinki-NLP/opus-100", "en-es", streaming=True)

    def _extract_pairs(split_stream, limit: int | None) -> list[dict[str, str]]:
        rows = []
        for item in split_stream:
            trans = item.get("translation") or {}
            es = normalize_text(trans.get("es"))
            en = normalize_text(trans.get("en"))
            if es and en:
                rows.append({"text_es": es, "text_en": en})
                if limit is not None and len(rows) >= limit:
                    break
        return rows

    # Para debug y streaming eficiente
    train_rows = _extract_pairs(raw_opus["train"], train_limit or 1000)
    val_rows = _extract_pairs(raw_opus["validation"], eval_limit or 200)
    test_rows = _extract_pairs(raw_opus["test"], test_limit or 200)

    return DatasetDict(
        {
            "train": Dataset.from_list(train_rows),
            "validation": Dataset.from_list(val_rows),
            "test": Dataset.from_list(test_rows),
        }
    )


def preprocess_function_factory(
    tokenizer: PreTrainedTokenizerBase,
    max_length: int = DEFAULT_MAX_LENGTH,
):
    """Crea la función de preprocesamiento y tokenización para Seq2SeqTrainer."""

    def preprocess_function(examples: dict[str, list[str]]) -> dict[str, Any]:
        inputs = examples["text_es"]
        targets = examples["text_en"]

        model_inputs = tokenizer(
            inputs,
            max_length=max_length,
            truncation=True,
            padding=False,  # El collator se encarga del padding dinámico
        )

        labels = tokenizer(
            text_target=targets,
            max_length=max_length,
            truncation=True,
            padding=False,
        )

        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    return preprocess_function


def prepare_tokenized_datasets(
    raw_datasets: DatasetDict,
    tokenizer: PreTrainedTokenizerBase,
    max_length: int = DEFAULT_MAX_LENGTH,
) -> DatasetDict:
    """Aplica la tokenización y remueve las columnas de texto crudo."""
    preprocess_fn = preprocess_function_factory(tokenizer, max_length=max_length)

    tokenized_datasets = raw_datasets.map(
        preprocess_fn,
        batched=True,
        remove_columns=raw_datasets["train"].column_names,
        desc="Tokenizando particiones para NMT",
    )
    return tokenized_datasets


def get_data_collator(
    tokenizer: PreTrainedTokenizerBase,
    model: Any | None = None,
    pad_to_multiple_of: int | None = 8,
) -> DataCollatorForSeq2Seq:
    """Instancia el DataCollatorForSeq2Seq con padding dinámico eficiente."""
    return DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        model=model,
        padding=True,
        pad_to_multiple_of=pad_to_multiple_of,
        label_pad_token_id=-100,
    )
