"""Ejecuta la evaluación final del pipeline sobre FLEURS es_419 oficial.

Uso:
    python scripts/run_final_evaluation.py --output-dir outputs/final_eval/run1
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.evaluation.fleurs_benchmark import run_benchmark, write_report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reservation",
        type=Path,
        default=ROOT
        / "data"
        / "processed"
        / "manifests"
        / "fleurs_evaluation_v2_official_test.csv",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--translation-model", default=None)
    args = parser.parse_args()

    aggregate = run_benchmark(
        args.reservation,
        args.output_dir,
        limit=args.limit,
        translation_model_name_or_path=args.translation_model,
    )
    report = write_report(args.output_dir)
    print(json.dumps(aggregate, indent=2, ensure_ascii=False))
    print(f"Reporte: {report}")


if __name__ == "__main__":
    main()
