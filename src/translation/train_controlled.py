"""Entrenamiento controlado de MarianMT (es -> en) sobre un subconjunto de OPUS-100.

Reproduce el experimento descrito en el capítulo V del informe: 10 000 pares de
entrenamiento, 1 000 de validación y una época, con los mismos hiperparámetros
del smoke test (AdamW, lr 5e-5, weight decay 0,01, label smoothing 0,1, FP16,
max_length 128, beam search 4, semilla 42). Después evalúa el modelo base y el
checkpoint generado sobre los mismos pares de prueba, que no intervienen en el
ajuste.

No es el entrenamiento completo de 100 000 pares: el límite está forzado en
``MAX_CONTROLLED_TRAIN_SAMPLES``.

Uso desde línea de comandos (requiere data/processed/translation/*.csv):

    python -m src.translation.train_controlled
"""

from __future__ import annotations

import argparse
import inspect
import json
import math
import time
from pathlib import Path
from typing import Any

import torch
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    set_seed,
)

from src.paths import project_path
from src.translation.data import (
    DEFAULT_DATA_DIR,
    DEFAULT_MAX_LENGTH,
    DEFAULT_MODEL_NAME,
    get_data_collator,
    load_raw_dataset,
    prepare_tokenized_datasets,
)
from src.translation.train import build_compute_metrics_fn

SEED = 42
MAX_CONTROLLED_TRAIN_SAMPLES = 10_000
DEFAULT_TRAIN_SAMPLES = 10_000
DEFAULT_VAL_SAMPLES = 1_000
DEFAULT_EPOCHS = 1.0
DEFAULT_BATCH_SIZE = 8
DEFAULT_LEARNING_RATE = 5e-5
DEFAULT_WEIGHT_DECAY = 0.01
DEFAULT_LABEL_SMOOTHING = 0.1
DEFAULT_NUM_BEAMS = 4

METRICS_DIR = project_path("outputs", "metrics", "nmt_controlled_10k")
CHECKPOINT_DIR = project_path("models", "checkpoints", "controlled_10k")
TRAINER_WORK_DIR = project_path("models", "checkpoints", "_trainer_work")


def _build_trainer(
    model,
    tokenizer,
    *,
    args: Seq2SeqTrainingArguments,
    train_dataset=None,
    eval_dataset=None,
    collator=None,
    max_length: int = DEFAULT_MAX_LENGTH,
) -> Seq2SeqTrainer:
    """Crea un Seq2SeqTrainer compatible con transformers 4.x y 5.x."""
    kwargs: dict[str, Any] = {
        "model": model,
        "args": args,
        "train_dataset": train_dataset,
        "eval_dataset": eval_dataset,
        "data_collator": collator,
        "compute_metrics": build_compute_metrics_fn(tokenizer, max_length=max_length),
    }
    params = inspect.signature(Seq2SeqTrainer.__init__).parameters
    if "processing_class" in params:
        kwargs["processing_class"] = tokenizer
    elif "tokenizer" in params:
        kwargs["tokenizer"] = tokenizer
    return Seq2SeqTrainer(**kwargs)


def _eval_args(
    batch_size: int, max_length: int, num_beams: int, label_smoothing: float
) -> Seq2SeqTrainingArguments:
    return Seq2SeqTrainingArguments(
        output_dir=str(TRAINER_WORK_DIR / "eval"),
        per_device_eval_batch_size=batch_size,
        predict_with_generate=True,
        generation_max_length=max_length,
        generation_num_beams=num_beams,
        label_smoothing_factor=label_smoothing,
        fp16=torch.cuda.is_available(),
        seed=SEED,
        report_to="none",
    )


def train_controlled(
    train_samples: int = DEFAULT_TRAIN_SAMPLES,
    val_samples: int = DEFAULT_VAL_SAMPLES,
    epochs: float = DEFAULT_EPOCHS,
    batch_size: int = DEFAULT_BATCH_SIZE,
    learning_rate: float = DEFAULT_LEARNING_RATE,
    weight_decay: float = DEFAULT_WEIGHT_DECAY,
    label_smoothing: float = DEFAULT_LABEL_SMOOTHING,
    num_beams: int = DEFAULT_NUM_BEAMS,
    max_length: int = DEFAULT_MAX_LENGTH,
    model_name: str = DEFAULT_MODEL_NAME,
    data_dir: Path | str = DEFAULT_DATA_DIR,
    checkpoint_dir: Path = CHECKPOINT_DIR,
    metrics_dir: Path = METRICS_DIR,
) -> dict[str, Any]:
    """Ajusta MarianMT con los primeros ``train_samples`` pares de ``train.csv``."""
    if train_samples > MAX_CONTROLLED_TRAIN_SAMPLES:
        raise ValueError(
            f"Este módulo solo ejecuta el experimento controlado "
            f"(<= {MAX_CONTROLLED_TRAIN_SAMPLES} pares). "
            "El entrenamiento de 100 000 pares no se ha realizado."
        )

    set_seed(SEED)
    is_cuda = torch.cuda.is_available()
    device_name = torch.cuda.get_device_name(0) if is_cuda else "CPU"
    print(f"Dispositivo: {device_name} (CUDA={is_cuda})")

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    # require_local_files=True evita un fallback silencioso a streaming:
    # el entrenamiento debe usar los CSV preparados con semilla 42.
    raw = load_raw_dataset(
        data_dir=data_dir,
        train_limit=train_samples,
        eval_limit=val_samples,
        test_limit=1,  # el test completo se evalúa aparte, en evaluate_on_test
        require_local_files=True,
    )
    if len(raw["train"]) != train_samples:
        raise RuntimeError(
            f"train.csv aportó {len(raw['train'])} pares; se esperaban {train_samples}."
        )
    tokenized = prepare_tokenized_datasets(raw, tokenizer, max_length=max_length)
    collator = get_data_collator(tokenizer, model=model)

    steps_per_epoch = math.ceil(train_samples / batch_size)
    total_steps = int(steps_per_epoch * epochs)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)

    args = Seq2SeqTrainingArguments(
        output_dir=str(TRAINER_WORK_DIR / "train"),
        eval_strategy="epoch",
        save_strategy="no",
        learning_rate=learning_rate,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        weight_decay=weight_decay,
        num_train_epochs=epochs,
        predict_with_generate=True,
        generation_max_length=max_length,
        generation_num_beams=num_beams,
        label_smoothing_factor=label_smoothing,
        fp16=is_cuda,
        warmup_steps=max(1, int(0.1 * total_steps)),
        logging_steps=max(1, total_steps // 25),
        seed=SEED,
        report_to="none",
    )
    trainer = _build_trainer(
        model,
        tokenizer,
        args=args,
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["validation"],
        collator=collator,
        max_length=max_length,
    )

    if is_cuda:
        torch.cuda.reset_peak_memory_stats(0)
    start = time.perf_counter()
    result = trainer.train()
    train_seconds = time.perf_counter() - start
    peak_gib = (
        round(torch.cuda.max_memory_allocated(0) / 1024**3, 3) if is_cuda else 0.0
    )

    val_metrics = trainer.evaluate(metric_key_prefix="val")

    trainer.save_model(str(checkpoint_dir))
    tokenizer.save_pretrained(str(checkpoint_dir))

    summary = {
        "mode": "controlled_experiment",
        "disclaimer": (
            "Experimento controlado de 10 000 pares y una época; no es el "
            "entrenamiento completo de 100 000 pares ni el modelo final."
        ),
        "device": device_name,
        "base_model": model_name,
        "train_pairs_available": 100_000,
        "train_pairs_used": train_samples,
        "validation_pairs_used": len(raw["validation"]),
        "epochs": epochs,
        "batch_size": batch_size,
        "global_steps": int(result.global_step),
        "learning_rate": learning_rate,
        "weight_decay": weight_decay,
        "label_smoothing": label_smoothing,
        "max_length": max_length,
        "num_beams": num_beams,
        "seed": SEED,
        "fp16": is_cuda,
        "training_seconds": round(train_seconds, 3),
        "training_loss": round(float(result.training_loss), 6),
        "peak_vram_gib": peak_gib,
        "validation": {
            k: (round(float(v), 4) if isinstance(v, (int, float)) else v)
            for k, v in val_metrics.items()
        },
        "log_history": trainer.state.log_history,
        "checkpoint_dir": str(checkpoint_dir),
    }
    (metrics_dir / "train_metrics.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Checkpoint guardado en {checkpoint_dir}")
    print(f"Métricas guardadas en {metrics_dir / 'train_metrics.json'}")
    return summary


def evaluate_on_test(
    model_name_or_path: str,
    batch_size: int = DEFAULT_BATCH_SIZE,
    max_length: int = DEFAULT_MAX_LENGTH,
    num_beams: int = DEFAULT_NUM_BEAMS,
    label_smoothing: float = DEFAULT_LABEL_SMOOTHING,
    data_dir: Path | str = DEFAULT_DATA_DIR,
) -> dict[str, Any]:
    """Evalúa un modelo (base o checkpoint) sobre TODO el ``test.csv``."""
    tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name_or_path)
    raw = load_raw_dataset(
        data_dir=data_dir,
        train_limit=1,
        eval_limit=1,
        test_limit=None,
        require_local_files=True,
    )
    tokenized = prepare_tokenized_datasets(raw, tokenizer, max_length=max_length)
    collator = get_data_collator(tokenizer, model=model)
    trainer = _build_trainer(
        model,
        tokenizer,
        args=_eval_args(batch_size, max_length, num_beams, label_smoothing),
        eval_dataset=tokenized["test"],
        collator=collator,
        max_length=max_length,
    )
    metrics = trainer.evaluate(metric_key_prefix="test")
    n = len(tokenized["test"])
    runtime = float(metrics["test_runtime"])
    result = {
        "model": str(model_name_or_path),
        "test_pairs": n,
        "eval_loss": round(float(metrics["test_loss"]), 4),
        "sacrebleu": round(float(metrics["test_bleu"]), 4),
        "chrf": round(float(metrics["test_chrf"]), 4),
        "inference_seconds_total": round(runtime, 3),
        "inference_seconds_per_sentence": round(runtime / n, 4),
    }
    del trainer, model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return result


def compare_base_vs_checkpoint(
    checkpoint_dir: Path = CHECKPOINT_DIR,
    base_model: str = DEFAULT_MODEL_NAME,
    metrics_dir: Path = METRICS_DIR,
    **eval_kwargs: Any,
) -> dict[str, Any]:
    """Evalúa base y checkpoint sobre el mismo test y guarda la comparación."""
    base = evaluate_on_test(base_model, **eval_kwargs)
    tuned = evaluate_on_test(str(checkpoint_dir), **eval_kwargs)
    comparison = {
        "base": base,
        "controlled_checkpoint": tuned,
        "delta": {
            "eval_loss": round(tuned["eval_loss"] - base["eval_loss"], 4),
            "sacrebleu": round(tuned["sacrebleu"] - base["sacrebleu"], 4),
            "chrf": round(tuned["chrf"] - base["chrf"], 4),
            "inference_seconds_total": round(
                tuned["inference_seconds_total"] - base["inference_seconds_total"], 3
            ),
        },
    }
    metrics_dir.mkdir(parents=True, exist_ok=True)
    (metrics_dir / "test_comparison.json").write_text(
        json.dumps(comparison, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return comparison


def main() -> None:
    parser = argparse.ArgumentParser(description="Entrenamiento controlado MarianMT.")
    parser.add_argument("--train-samples", type=int, default=DEFAULT_TRAIN_SAMPLES)
    parser.add_argument("--val-samples", type=int, default=DEFAULT_VAL_SAMPLES)
    parser.add_argument("--epochs", type=float, default=DEFAULT_EPOCHS)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    args = parser.parse_args()
    train_controlled(
        train_samples=args.train_samples,
        val_samples=args.val_samples,
        epochs=args.epochs,
        batch_size=args.batch_size,
    )
    compare_base_vs_checkpoint(batch_size=args.batch_size)


if __name__ == "__main__":
    main()
