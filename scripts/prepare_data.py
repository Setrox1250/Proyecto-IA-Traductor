"""Prepara los datasets del proyecto de forma explícita y reproducible.

Ejemplos:
    python scripts/prepare_data.py --dataset opus100 --train-size 10000
    python scripts/prepare_data.py --dataset fleurs --n-samples 20
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.dataset.parallel import (
    OUTPUT_DIR,
    load_opus100,
    prepare_opus100_splits,
    save_parallel_splits,
)
from src.evaluation.fleurs_benchmark import build_official_reservation


def prepare_opus100(train_size: int) -> None:
    dataset = load_opus100(streaming=True)
    splits = prepare_opus100_splits(dataset, train_size=train_size)
    save_parallel_splits(splits, OUTPUT_DIR)


def prepare_fleurs(n_samples: int) -> None:
    output = (
        ROOT
        / "data"
        / "processed"
        / "manifests"
        / "fleurs_evaluation_v2_official_test.csv"
    )
    build_official_reservation(output, n_samples=n_samples)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=["opus100", "fleurs"], required=True)
    parser.add_argument("--train-size", type=int, default=10_000)
    parser.add_argument("--n-samples", type=int, default=20)
    args = parser.parse_args()
    if args.dataset == "opus100":
        prepare_opus100(args.train_size)
    else:
        prepare_fleurs(args.n_samples)


if __name__ == "__main__":
    main()
