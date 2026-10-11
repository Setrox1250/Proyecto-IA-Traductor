"""Módulo de Reconocimiento Automático del Habla (ASR) con openai/whisper-small.

Proporciona transcripción de voz a texto en español para audios mono de 16 kHz.
Opera exclusivamente en modo transcripción (es -> es) sin traducción.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

import numpy as np
import soundfile as sf
import torch
import yaml
from transformers import WhisperForConditionalGeneration, WhisperProcessor


DEFAULT_MODEL_NAME = "openai/whisper-small"
DEFAULT_CONFIG_PATH = Path("configs/asr.yaml")
TARGET_SAMPLE_RATE = 16_000


def load_asr_config(config_path: str | Path = DEFAULT_CONFIG_PATH) -> dict:
    """Carga configuración desde configs/asr.yaml si existe."""
    path = Path(config_path)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {
        "model_name": DEFAULT_MODEL_NAME,
        "sample_rate": TARGET_SAMPLE_RATE,
        "language": "es",
        "task": "transcribe",
    }


def load_and_preprocess_audio(audio_source: Union[str, Path, np.ndarray], target_sr: int = TARGET_SAMPLE_RATE) -> np.ndarray:
    """Carga un archivo de audio, lo convierte a mono y asegura 16 kHz float32."""
    if isinstance(audio_source, (str, Path)):
        path = Path(audio_source)
        if not path.exists():
            raise FileNotFoundError(f"Archivo de audio no encontrado: {path}")
        audio_array, sr = sf.read(str(path), dtype="float32", always_2d=False)
    elif isinstance(audio_source, np.ndarray):
        audio_array = audio_source.astype(np.float32)
        sr = target_sr
    else:
        raise TypeError(f"Fuente de audio no soportada: {type(audio_source)}")

    # Convertir estéreo a mono
    if audio_array.ndim == 2:
        audio_array = audio_array.mean(axis=1)

    # Resamplear si difiere de 16 kHz
    if sr != target_sr:
        import librosa
        audio_array = librosa.resample(audio_array, orig_sr=sr, target_sr=target_sr)

    return audio_array


class WhisperTranscriber:
    """Transcriptor de voz a texto en español utilizando openai/whisper-small."""

    def __init__(
        self,
        model_name_or_path: str | None = None,
        device: str | torch.device | None = None,
        language: str = "es",
    ) -> None:
        cfg = load_asr_config()
        self.model_name = model_name_or_path or cfg.get("model_name", DEFAULT_MODEL_NAME)
        self.language = language or cfg.get("language", "es")
        self.task = "transcribe"  # Estrictamente transcribir (es -> es), nunca traducir

        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        print(f"Cargando modelo ASR ({self.model_name}) en {self.device}...")
        self.processor = WhisperProcessor.from_pretrained(self.model_name)
        self.model = WhisperForConditionalGeneration.from_pretrained(self.model_name)
        self.model.to(self.device)
        self.model.eval()

        # Forzar generación en español sin traducción
        self.forced_decoder_ids = self.processor.get_decoder_prompt_ids(
            language=self.language,
            task=self.task,
        )

    def transcribe(self, audio_source: Union[str, Path, np.ndarray]) -> str:
        """Transcribe un archivo de audio o array a texto en español."""
        audio = load_and_preprocess_audio(audio_source, target_sr=TARGET_SAMPLE_RATE)

        inputs = self.processor(
            audio,
            sampling_rate=TARGET_SAMPLE_RATE,
            return_tensors="pt",
        )
        input_features = inputs.input_features.to(self.device)

        with torch.no_grad():
            predicted_ids = self.model.generate(
                input_features,
                forced_decoder_ids=self.forced_decoder_ids,
            )

        transcription = self.processor.batch_decode(predicted_ids, skip_special_tokens=True)
        return transcription[0].strip() if transcription else ""


def transcribe(audio_path: str, model_name: str = DEFAULT_MODEL_NAME) -> str:
    """Función de interfaz directa para transcribir un archivo de audio."""
    transcriber = WhisperTranscriber(model_name_or_path=model_name)
    return transcriber.transcribe(audio_path)
