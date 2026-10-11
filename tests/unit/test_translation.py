"""Pruebas unitarias para los módulos de traducción y ASR sin descargar pesos grandes."""

from __future__ import annotations

import numpy as np
import pytest

from src.asr.transcribe import load_asr_config
from src.translation.analyze_lengths import compute_length_stats
from src.translation.data import get_data_collator, preprocess_function_factory
from src.translation.model import load_translation_config


def test_translation_config_loads_empirical_defaults():
    cfg = load_translation_config()
    assert cfg["model_name"] == "Helsinki-NLP/opus-mt-es-en"
    assert cfg["max_length"] == 128
    assert cfg["num_beams"] == 4
    assert cfg["seed"] == 42


def test_asr_config_loads_whisper_defaults():
    cfg = load_asr_config()
    assert cfg["model_name"] == "openai/whisper-small"
    assert cfg["sample_rate"] == 16000
    assert cfg["language"] == "es"
    assert cfg["task"] == "transcribe"


def test_compute_length_stats_percentiles():
    # Longitudes sintéticas: 100 secuencias de longitud 50, y una de 200
    lengths = [50] * 100 + [200]
    stats = compute_length_stats(lengths)

    assert stats["count"] == 101
    assert stats["median"] == 50.0
    assert stats["max"] == 200
    assert stats["pct_gt_128"] > 0.0
    assert stats["pct_gt_256"] == 0.0


class DummyTokenizer:
    """Tokenizer simulado para probar la estructura del pipeline sin descargar modelos."""

    def __init__(self):
        self.pad_token_id = 0

    def __call__(self, text=None, max_length=128, truncation=True, padding=False, text_target=None):
        if text_target is not None:
            text = text_target
        if text is None:
            text = []

        if isinstance(text, str):
            text = [text]

        input_ids = []
        attention_mask = []
        for t in text:
            # Simular tokens basados en palabras
            tokens = [1] + [ord(w[0]) % 50 + 2 for w in t.split() if w] + [2]
            if truncation and len(tokens) > max_length:
                tokens = tokens[:max_length]
            input_ids.append(tokens)
            attention_mask.append([1] * len(tokens))

        return {"input_ids": input_ids, "attention_mask": attention_mask}


def test_preprocess_function_factory_produces_labels():
    tokenizer = DummyTokenizer()
    preprocess_fn = preprocess_function_factory(tokenizer, max_length=10)

    batch = {
        "text_es": ["Hola mundo desde la prueba unitaria", "Segunda frase"],
        "text_en": ["Hello world from unit test", "Second sentence"],
    }

    processed = preprocess_fn(batch)
    assert "input_ids" in processed
    assert "attention_mask" in processed
    assert "labels" in processed
    assert len(processed["input_ids"]) == 2
    assert len(processed["labels"]) == 2
    # Truncado a max_length = 10
    assert len(processed["input_ids"][0]) <= 10


def test_get_data_collator_configuration():
    tokenizer = DummyTokenizer()
    collator = get_data_collator(tokenizer)
    assert collator.label_pad_token_id == -100
    assert collator.padding is True
