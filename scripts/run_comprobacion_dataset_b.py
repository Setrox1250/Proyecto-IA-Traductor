"""Compatibilidad histórica: evaluación Dataset B con la reserva oficial v2.

El nombre se conserva porque algunos notebooks antiguos lo referencian. La
evaluación vigente está en ``scripts/run_final_evaluation.py`` y usa el split
oficial ``test`` de FLEURS.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
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
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT
        / "outputs"
        / "final_eval"
        / f"comprobacion_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}",
    )
    args = parser.parse_args()
    aggregate = run_benchmark(args.reservation, args.output_dir)
    report = write_report(args.output_dir)
    print(json.dumps(aggregate, indent=2, ensure_ascii=False))
    print(f"Reporte: {report}")


if __name__ == "__main__":
    main()
