from __future__ import annotations

import numpy as np
import soundfile as sf

from src.voice_cloning import audio, synthesize as synth_module


def test_prepare_reference_audio_creates_independent_mono_22050_wav(tmp_path):
    source = tmp_path / "master.wav"
    reference = tmp_path / "reference.wav"
    stereo = np.column_stack((np.linspace(-0.2, 0.2, 4_410), np.linspace(0.2, -0.2, 4_410)))
    sf.write(source, stereo, 44_100, subtype="FLOAT")

    result = audio.prepare_reference_audio(source, reference)

    assert result == str(reference)
    assert sf.info(source).samplerate == 44_100
    assert sf.info(reference).samplerate == 22_050
    converted, _ = sf.read(reference, always_2d=True)
    assert converted.shape[1] == 1
    assert audio.validate_audio(reference, 22_050)["duration_sec"] > 0


def test_synthesize_uses_reference_and_returns_wav_path(tmp_path, monkeypatch):
    reference = tmp_path / "reference.wav"
    output = tmp_path / "generated.wav"
    sf.write(reference, np.linspace(-0.1, 0.1, 2_205), 22_050, subtype="FLOAT")
    observed = {}

    class FakeTTS:
        def tts_to_file(self, **kwargs):
            observed.update(kwargs)
            sf.write(kwargs["file_path"], np.linspace(-0.1, 0.1, 2_400), 24_000)

    monkeypatch.setattr(synth_module, "get_xtts_model", lambda: FakeTTS())
    result = synth_module.synthesize("A short English sentence.", str(reference), str(output))

    assert result == str(output)
    assert observed["speaker_wav"] == str(reference)
    assert observed["language"] == "en"
    assert sf.info(output).samplerate == 24_000
