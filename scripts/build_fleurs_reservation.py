"""Construye la reserva FLEURS es_419 desde el split oficial `test`.

Uso:
    python scripts/build_fleurs_reservation.py --n-samples 20
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.evaluation.fleurs_benchmark import build_official_reservation


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT
        / "data"
        / "processed"
        / "manifests"
        / "fleurs_evaluation_v2_official_test.csv",
    )
    parser.add_argument("--n-samples", type=int, default=20)
    args = parser.parse_args()
    build_official_reservation(args.output, n_samples=args.n_samples)


if __name__ == "__main__":
    main()
