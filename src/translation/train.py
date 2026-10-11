"""Script de fine-tuning para el modelo NMT MarianMT (Helsinki-NLP/opus-mt-es-en).

Implementa Seq2SeqTrainer con soporte explícito para modo --debug (smoke test)
y modo --full (entrenamiento completo futuro). Registra pérdidas, duración,
consumo de memoria VRAM y métricas de traducción (SacreBLEU y chrF).
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import evaluate
import numpy as np
import torch
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
)

from src.translation.data import (
    DEFAULT_MAX_LENGTH,
    DEFAULT_MODEL_NAME,
    get_data_collator,
    load_raw_dataset,
    prepare_tokenized_datasets,
)


OUTPUT_DEBUG_DIR = Path("outputs/smoke_tests/nmt_training")
CHECKPOINT_DEBUG_DIR = Path("models/checkpoints/debug")


def build_compute_metrics_fn(tokenizer, max_length: int = DEFAULT_MAX_LENGTH):
    """Genera la función compute_metrics usando sacrebleu y chrf."""
    bleu_metric = evaluate.load("sacrebleu")
    chrf_metric = evaluate.load("chrf")

    def compute_metrics(eval_preds):
        preds, labels = eval_preds
        if isinstance(preds, tuple):
            preds = preds[0]

        # Reemplazar -100 por pad_token_id para poder decodificar
        preds = np.where(preds != -100, preds, tokenizer.pad_token_id)
        decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)

        labels = np.where(labels != -100, labels, tokenizer.pad_token_id)
        decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)

        decoded_preds = [pred.strip() for pred in decoded_preds]
        decoded_labels = [[label.strip()] for label in decoded_labels]

        bleu_result = bleu_metric.compute(predictions=decoded_preds, references=decoded_labels)
        chrf_result = chrf_metric.compute(predictions=decoded_preds, references=decoded_labels)

        return {
            "bleu": round(float(bleu_result["score"]), 2),
            "chrf": round(float(chrf_result["score"]), 2),
        }

    return compute_metrics


def run_training(
    debug_mode: bool = True,
    model_name_or_path: str = DEFAULT_MODEL_NAME,
    max_length: int = DEFAULT_MAX_LENGTH,
    output_dir: Path = OUTPUT_DEBUG_DIR,
    checkpoint_dir: Path = CHECKPOINT_DEBUG_DIR,
) -> dict[str, Any]:
    """Ejecuta el ciclo de entrenamiento Seq2Seq en modo debug o full."""
    is_cuda = torch.cuda.is_available()
    device_name = torch.cuda.get_device_name(0) if is_cuda else "CPU"
    print(f"Dispositivo detectado: {device_name} (CUDA={is_cuda})")

    if debug_mode:
        print("\n" + "=" * 60)
        print("INICIANDO SMOKE TEST DE FINE-TUNING (--debug)")
        print("Configuración reducida: 256 train, 64 eval, 1 epoch")
        print("=" * 60)
        train_samples = 256
        eval_samples = 64
        epochs = 1.0
        batch_size = 8
        learning_rate = 5e-5
        weight_decay = 0.01
        warmup_ratio = 0.1
        label_smoothing_factor = 0.1
        num_beams = 4
        save_strategy = "no"
        eval_strategy = "steps"
        eval_steps = 16
    else:
        raise NotImplementedError(
            "El entrenamiento completo (--full) sobre 100 000 pares no debe ejecutarse "
            "sin la confirmación explícita del usuario y la validación previa del smoke test."
        )

    # 1. Cargar Tokenizer y Modelo
    print(f"Cargando modelo y tokenizador: {model_name_or_path}")
    tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name_or_path)

    # 2. Cargar y preparar datos
    raw_datasets = load_raw_dataset(
        train_limit=train_samples,
        eval_limit=eval_samples,
        test_limit=eval_samples,
        require_local_files=not debug_mode,
    )
    tokenized_datasets = prepare_tokenized_datasets(raw_datasets, tokenizer, max_length=max_length)
    collator = get_data_collator(tokenizer, model=model)

    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 3. Configurar argumentos de entrenamiento
    training_args = Seq2SeqTrainingArguments(
        output_dir=str(checkpoint_dir),
        eval_strategy=eval_strategy,
        eval_steps=eval_steps,
        learning_rate=learning_rate,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        weight_decay=weight_decay,
        save_strategy=save_strategy,
        num_train_epochs=epochs,
        predict_with_generate=True,
        generation_max_length=max_length,
        generation_num_beams=num_beams,
        fp16=is_cuda,
        warmup_steps=max(1, int(32 * warmup_ratio)),
        label_smoothing_factor=label_smoothing_factor,
        logging_steps=8,
        seed=42,
        report_to="none",
    )

    compute_metrics_fn = build_compute_metrics_fn(tokenizer, max_length=max_length)

    trainer_kwargs = {
        "model": model,
        "args": training_args,
        "train_dataset": tokenized_datasets["train"],
        "eval_dataset": tokenized_datasets["validation"],
        "data_collator": collator,
        "compute_metrics": compute_metrics_fn,
    }
    import inspect
    sig = inspect.signature(Seq2SeqTrainer.__init__)
    if "processing_class" in sig.parameters:
        trainer_kwargs["processing_class"] = tokenizer
    elif "tokenizer" in sig.parameters:
        trainer_kwargs["tokenizer"] = tokenizer

    trainer = Seq2SeqTrainer(**trainer_kwargs)

    # Reset stats de VRAM si CUDA
    if is_cuda:
        torch.cuda.reset_peak_memory_stats(0)

    print("Evaluando modelo BASE antes del fine-tuning (smoke test baseline)...")
    base_eval_metrics = trainer.evaluate()
    base_bleu = base_eval_metrics.get("eval_bleu", 0.0)
    base_chrf = base_eval_metrics.get("eval_chrf", 0.0)
    base_loss = round(float(base_eval_metrics.get("eval_loss", 0.0)), 4)
    print(f"Base Metrics -> Loss: {base_loss} | BLEU: {base_bleu} | chrF: {base_chrf}")

    start_time = time.time()
    print("Iniciando entrenamiento...")
    train_result = trainer.train()
    training_duration = time.time() - start_time

    print(f"Entrenamiento completado en {training_duration:.2f} segundos.")

    # Evaluación final
    print("Ejecutando evaluación final del modelo FINE-TUNED (smoke test)...")
    eval_metrics = trainer.evaluate()
    debug_bleu = eval_metrics.get("eval_bleu", 0.0)
    debug_chrf = eval_metrics.get("eval_chrf", 0.0)
    debug_loss = round(float(eval_metrics.get("eval_loss", 0.0)), 4)

    peak_vram_mb = (
        round(torch.cuda.max_memory_allocated(0) / (1024 * 1024), 2) if is_cuda else 0.0
    )

    summary = {
        "mode": "debug_smoke_test" if debug_mode else "full",
        "device": device_name,
        "is_cuda": is_cuda,
        "train_samples": train_samples,
        "eval_samples": eval_samples,
        "epochs": epochs,
        "max_length": max_length,
        "num_beams": num_beams,
        "duration_seconds": round(training_duration, 2),
        "peak_vram_mb": peak_vram_mb,
        "train_loss": round(float(train_result.training_loss), 4),
        "eval_loss": debug_loss,
        "eval_bleu": debug_bleu,
        "eval_chrf": debug_chrf,
        "global_step": train_result.global_step,
    }

    metrics_file = output_dir / "train_metrics.json"
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Métricas guardadas en: {metrics_file}")

    # Guardar reporte comparativo Base vs Debug
    comparison = {
        "disclaimer": "SMOKE TEST COMPARATIVO - ESTAS MÉTRICAS DEMUESTRAN QUE EL FLUJO DE ENTRENAMIENTO Y EVALUACIÓN FUNCIONA. NO REPRESENTAN EL RESULTADO FINAL DEL PROYECTO.",
        "device": device_name,
        "eval_samples": eval_samples,
        "base_model": {
            "name": model_name_or_path,
            "eval_loss": base_loss,
            "bleu": base_bleu,
            "chrf": base_chrf,
        },
        "debug_fine_tuned_model": {
            "name": f"{model_name_or_path} (fine-tuned {train_samples} samples, 1 epoch)",
            "eval_loss": debug_loss,
            "bleu": debug_bleu,
            "chrf": debug_chrf,
        },
        "delta": {
            "delta_bleu": round(debug_bleu - base_bleu, 2),
            "delta_chrf": round(debug_chrf - base_chrf, 2),
            "delta_loss": round(debug_loss - base_loss, 4),
        }
    }

    comparison_file = Path("outputs/smoke_tests/nmt_base_vs_debug.json")
    comparison_file.parent.mkdir(parents=True, exist_ok=True)
    with open(comparison_file, "w", encoding="utf-8") as f:
        json.dump(comparison, f, indent=2, ensure_ascii=False)
    print(f"Comparación Base vs Debug guardada en: {comparison_file}")

    print("\n" + "=" * 60)
    print("RESULTADO DEL SMOKE TEST DE FINE-TUNING")
    print("=" * 60)
    print(f"Duración: {summary['duration_seconds']} s | VRAM pico: {summary['peak_vram_mb']} MB")
    print(f"Train Loss: {summary['train_loss']} | Eval Loss: {summary['eval_loss']}")
    print(f"BLEU: {summary['eval_bleu']} | chrF: {summary['eval_chrf']}")
    print("=" * 60)

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tuning MarianMT (es->en).")
    parser.add_argument("--debug", action="store_true", default=True, help="Ejecutar en modo debug smoke test.")
    parser.add_argument("--full", action="store_true", default=False, help="Ejecutar en modo full training (100k).")
    parser.add_argument("--max-length", type=int, default=DEFAULT_MAX_LENGTH, help="Longitud máxima de tokens.")
    args = parser.parse_args()

    debug = not args.full
    run_training(debug_mode=debug, max_length=args.max_length)


if __name__ == "__main__":
    main()
