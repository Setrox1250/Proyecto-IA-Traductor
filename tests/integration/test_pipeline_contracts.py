from __future__ import annotations

import json

import numpy as np
import soundfile as sf

from src.pipeline import runner


def test_process_audio_preserves_contracts_without_loading_real_models(tmp_path, monkeypatch):
    input_audio = tmp_path / "input_source.wav"
    output_dir = tmp_path / "run"
    sf.write(input_audio, np.linspace(-0.1, 0.1, 16_000), 16_000, subtype="FLOAT")

    class FakeASR:
        def transcribe(self, path):
            assert path.endswith("asr_input.wav")
            return "Hola mundo"

    class FakeTranslator:
        def translate(self, text):
            assert text == "Hola mundo"
            return "Hello world"

    def fake_synthesize(text, reference, output, language="en"):
        assert text == "Hello world"
        assert reference.endswith("xtts_reference.wav")
        assert language == "en"
        sf.write(output, np.linspace(-0.1, 0.1, 24_000), 24_000, subtype="FLOAT")
        return output

    monkeypatch.setattr(
        runner,
        "_get_pipeline_components",
        lambda: {
            "asr": FakeASR(),
            "translator": FakeTranslator(),
            "synthesize": fake_synthesize,
            "speaker_similarity": lambda reference, generated: 0.42,
        },
    )

    result = runner.process_audio(str(input_audio), str(output_dir))

    assert result["transcription_es"] == "Hola mundo"
    assert result["translation_en"] == "Hello world"
    assert result["speaker_similarity"] == 0.42
    assert result["models"]["translation_checkpoint"] == "base"
    assert result["audio"]["output_sample_rate"] == 24_000
    assert set(result["timings"]) == {
        "preprocessing_sec", "asr_sec", "translation_sec", "xtts_sec", "speaker_evaluation_sec", "total_sec"
    }
    assert (output_dir / "input.wav").exists()
    assert (output_dir / "asr_input.wav").exists()
    assert (output_dir / "xtts_reference.wav").exists()
    assert (output_dir / "output.wav").exists()
    assert json.loads((output_dir / "metadata.json").read_text(encoding="utf-8"))["rtf_total"] >= 0
