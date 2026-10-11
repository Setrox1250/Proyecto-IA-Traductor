from __future__ import annotations

import torch
import pytest

from src.evaluation import speaker_similarity as module


def test_speaker_similarity_returns_continuous_cosine(monkeypatch):
    embeddings = iter((torch.tensor([3.0, 4.0]), torch.tensor([0.0, 5.0])))
    monkeypatch.setattr(module, "extract_embedding", lambda _: next(embeddings))

    similarity = module.speaker_similarity("reference.wav", "generated.wav")

    assert isinstance(similarity, float)
    assert similarity == pytest.approx(0.8)


def test_load_audio_for_ecapa_rejects_missing_file(tmp_path):
    missing = tmp_path / "missing.wav"
    try:
        module.load_audio_for_ecapa(missing)
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("Se esperaba FileNotFoundError para un archivo inexistente.")
