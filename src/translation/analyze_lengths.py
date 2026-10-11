"""Análisis empírico de longitud de tokens para traducción NMT (es -> en).

Evalúa la distribución real de longitud de secuencias en tokens con el
tokenizador oficial de Helsinki-NLP/opus-mt-es-en para resolver de forma
empírica la discrepancia entre max_length = 128 (informe) y 512 (config).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np


MODEL_NAME = "Helsinki-NLP/opus-mt-es-en"
DEFAULT_SAMPLE_SIZE = 10_000
OUTPUT_PATH = Path("outputs/metrics/token_length_analysis.json")
LOCAL_TRAIN_CSV = Path("data/processed/translation/train.csv")


def load_pairs(sample_size: int = DEFAULT_SAMPLE_SIZE, data_path: Path | None = None) -> list[tuple[str, str]]:
    """Carga pares (text_es, text_en) desde CSV local o mediante streaming de OPUS-100."""
    path = data_path or LOCAL_TRAIN_CSV
    pairs: list[tuple[str, str]] = []

    if path.exists():
        import pandas as pd

        print(f"Leyendo dataset desde archivo local: {path}")
        df = pd.read_csv(path, nrows=sample_size if sample_size > 0 else None)
        for _, row in df.iterrows():
            es = str(row.get("text_es", "")).strip()
            en = str(row.get("text_en", "")).strip()
            if es and en:
                pairs.append((es, en))
                if sample_size > 0 and len(pairs) >= sample_size:
                    break
        return pairs

    # Fallback streaming desde Hugging Face
    from datasets import load_dataset
    from src.dataset.parallel import normalize_text

    print(f"Archivo local {path} no encontrado. Transmitiendo desde Helsinki-NLP/opus-100 (en-es)...")
    dataset = load_dataset("Helsinki-NLP/opus-100", "en-es", split="train", streaming=True)
    for item in dataset:
        trans = item.get("translation") or {}
        es = normalize_text(trans.get("es"))
        en = normalize_text(trans.get("en"))
        if es and en:
            pairs.append((es, en))
            if sample_size > 0 and len(pairs) >= sample_size:
                break
    return pairs


def compute_length_stats(lengths: list[int]) -> dict[str, float | int]:
    """Calcula estadísticas descriptivas y percentiles de longitudes de tokens."""
    arr = np.array(lengths, dtype=np.int32)
    n = len(arr)
    if n == 0:
        return {}

    return {
        "count": int(n),
        "mean": round(float(np.mean(arr)), 2),
        "std": round(float(np.std(arr)), 2),
        "median": float(np.median(arr)),
        "p90": float(np.percentile(arr, 90)),
        "p95": float(np.percentile(arr, 95)),
        "p99": float(np.percentile(arr, 99)),
        "max": int(np.max(arr)),
        "pct_gt_128": round(float(np.mean(arr > 128) * 100), 3),
        "pct_gt_256": round(float(np.mean(arr > 256) * 100), 3),
        "pct_gt_512": round(float(np.mean(arr > 512) * 100), 3),
    }


def analyze_token_lengths(
    model_name: str = MODEL_NAME,
    sample_size: int = DEFAULT_SAMPLE_SIZE,
    data_path: Path | None = None,
    output_path: Path = OUTPUT_PATH,
) -> dict[str, Any]:
    """Tokeniza sin truncamiento y genera el reporte de longitud de tokens."""
    from transformers import AutoTokenizer

    print(f"Cargando tokenizador oficial: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    pairs = load_pairs(sample_size=sample_size, data_path=data_path)
    print(f"Total de pares cargados para análisis: {len(pairs)}")

    texts_es = [p[0] for p in pairs]
    texts_en = [p[1] for p in pairs]

    print("Tokenizando texto en español (input) sin truncamiento...")
    encoded_es = tokenizer(texts_es, truncation=False, add_special_tokens=True)
    lengths_es = [len(ids) for ids in encoded_es["input_ids"]]

    print("Tokenizando texto en inglés (target) sin truncamiento...")
    encoded_en = tokenizer(text_target=texts_en, truncation=False, add_special_tokens=True)
    lengths_en = [len(ids) for ids in encoded_en["input_ids"]]

    stats_es = compute_length_stats(lengths_es)
    stats_en = compute_length_stats(lengths_en)

    # Determinar recomendación
    # Se busca que el truncamiento sea < 1% en ambos idiomas (cobertura >= 99%)
    p99_max = max(stats_es["p99"], stats_en["p99"])
    pct_gt_128_max = max(stats_es["pct_gt_128"], stats_en["pct_gt_128"])
    pct_gt_256_max = max(stats_es["pct_gt_256"], stats_en["pct_gt_256"])

    if pct_gt_128_max <= 1.0:
        recommendation = 128
        justification = (
            f"El 99% de las oraciones tiene <= {p99_max:.0f} tokens (solo {pct_gt_128_max:.2f}% excede 128). "
            f"max_length = 128 es óptimo en eficiencia y minimiza el padding."
        )
    elif pct_gt_256_max <= 0.5:
        recommendation = 256
        justification = (
            f"{pct_gt_128_max:.2f}% de las oraciones excede 128 tokens, pero solo {pct_gt_256_max:.2f}% excede 256. "
            f"max_length = 256 cubre prácticamente todo el corpus con costo computacional moderado."
        )
    else:
        recommendation = 512
        justification = (
            f"Existen oraciones extensas ({pct_gt_256_max:.2f}% > 256). "
            f"max_length = 512 preserva integridad a costo de mayor memoria."
        )

    results = {
        "model_name": model_name,
        "sample_size": len(pairs),
        "spanish_source_tokens": stats_es,
        "english_target_tokens": stats_en,
        "recommendation": recommendation,
        "justification": justification,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResultados guardados en: {output_path}")

    # Imprimir resumen en consola
    print("\n" + "=" * 60)
    print("RESUMEN DE ANÁLISIS DE LONGITUD DE TOKENS")
    print("=" * 60)
    print(f"Muestras analizadas: {len(pairs)}")
    print(f"Español (ES) -> Media: {stats_es['mean']}, Mediana: {stats_es['median']}, "
          f"p90: {stats_es['p90']}, p95: {stats_es['p95']}, p99: {stats_es['p99']}, Max: {stats_es['max']}")
    print(f"             % > 128: {stats_es['pct_gt_128']}%, % > 256: {stats_es['pct_gt_256']}%, % > 512: {stats_es['pct_gt_512']}%")
    print(f"Inglés  (EN) -> Media: {stats_en['mean']}, Mediana: {stats_en['median']}, "
          f"p90: {stats_en['p90']}, p95: {stats_en['p95']}, p99: {stats_en['p99']}, Max: {stats_en['max']}")
    print(f"             % > 128: {stats_en['pct_gt_128']}%, % > 256: {stats_en['pct_gt_256']}%, % > 512: {stats_en['pct_gt_512']}%")
    print("-" * 60)
    print(f"RECOMENDACIÓN EMPÍRICA: max_length = {recommendation}")
    print(f"Justificación: {justification}")
    print("=" * 60)

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Analizar longitud de tokens en OPUS-100 para NMT.")
    parser.add_argument("--sample-size", type=int, default=DEFAULT_SAMPLE_SIZE, help="Cantidad de pares a analizar.")
    parser.add_argument("--data-path", type=Path, default=None, help="Ruta al CSV local con columnas text_es, text_en.")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH, help="Ruta de salida JSON.")
    args = parser.parse_args()

    analyze_token_lengths(
        sample_size=args.sample_size,
        data_path=args.data_path,
        output_path=args.output,
    )


if __name__ == "__main__":
    main()
