from __future__ import annotations

from io import BytesIO

import numpy as np
import pandas as pd
import soundfile as sf

from src.dataset import fleurs, manifest, parallel


class FakeSplit(list):
    def shuffle(self, seed: int, buffer_size: int):
        del seed, buffer_size
        return self


def _row(es: str, en: str) -> dict:
    return {"translation": {"es": es, "en": en}}


def test_prepare_parallel_splits_normalizes_and_prevents_leakage():
    dataset = {
        "test": FakeSplit([_row("Prueba", "Test"), _row("Prueba", "Test")]),
        "validation": FakeSplit(
            [_row("Validación", "Validation"), _row("Prueba", "Different")]
        ),
        "train": FakeSplit(
            [
                _row("  Hola   mundo  ", " Hello   world "),
                _row("Prueba", "Forbidden source"),
                _row("Otra", "Validation"),
                _row("Segundo", "Second"),
            ]
        ),
    }

    splits = parallel.prepare_opus100_splits(
        dataset, train_size=2, seed=42, shuffle_buffer=10
    )

    assert splits["test"].to_dict("records") == [
        {"text_es": "Prueba", "text_en": "Test"}
    ]
    assert splits["validation"].to_dict("records") == [
        {"text_es": "Validación", "text_en": "Validation"}
    ]
    assert splits["train"].to_dict("records") == [
        {"text_es": "Hola mundo", "text_en": "Hello world"},
        {"text_es": "Segundo", "text_en": "Second"},
    ]


def test_decode_audio_from_bytes_without_torchcodec():
    expected = np.linspace(-0.5, 0.5, 160, dtype=np.float32)
    encoded = BytesIO()
    sf.write(encoded, expected, 16_000, format="WAV", subtype="FLOAT")

    decoded, sample_rate = fleurs.decode_audio(
        {"bytes": encoded.getvalue(), "path": None}
    )

    assert sample_rate == 16_000
    np.testing.assert_allclose(decoded, expected)


def test_apply_fleurs_references_uses_sentence_id():
    frame = pd.DataFrame(
        {
            "sample_id": ["sample_0", "sample_1"],
            "sentence_id": [56, 225],
        }
    )
    result = manifest.apply_fleurs_references(
        frame, {"56": "First reference", "225": "Second reference"}
    )

    assert result["translation_en"].tolist() == [
        "First reference",
        "Second reference",
    ]
