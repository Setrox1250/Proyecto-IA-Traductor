"""Inferencia con el modelo de traducción neuronal NMT (Helsinki-NLP/opus-mt-es-en).

Encapsula la carga de tokenizer y modelo MarianMT, soportando inferencia
individual y por lotes en CPU y GPU con decodificación beam search.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import torch
import yaml
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from src.paths import project_path

DEFAULT_MODEL_NAME = "Helsinki-NLP/opus-mt-es-en"
DEFAULT_CONFIG_PATH = project_path("configs", "translation.yaml")


def load_translation_config(config_path: str | Path = DEFAULT_CONFIG_PATH) -> dict:
    """Carga la configuración base desde configs/translation.yaml si existe."""
    path = Path(config_path)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {
        "model_name": DEFAULT_MODEL_NAME,
        "max_length": 128,
        "num_beams": 4,
        "seed": 42,
        "use_controlled_checkpoint": False,
        "checkpoint_path": None,
    }


def resolve_translation_model(model_name_or_path: str | None = None) -> tuple[str, str]:
    """Resuelve el modelo NMT y etiqueta si es base o un checkpoint controlado.

    El valor por defecto es el modelo base. El checkpoint de 10 000 pares solo
    se usa si ``use_controlled_checkpoint: true`` está configurado y la ruta
    existe, porque el experimento controlado obtuvo métricas inferiores.
    """
    cfg = load_translation_config()
    if model_name_or_path:
        checkpoint_name = Path(str(model_name_or_path)).name.lower()
        kind = "controlled_10k" if "controlled" in checkpoint_name else "explicit"
        return str(model_name_or_path), kind

    if bool(cfg.get("use_controlled_checkpoint", False)):
        checkpoint = cfg.get("checkpoint_path")
        if not checkpoint:
            raise ValueError(
                "use_controlled_checkpoint está activo pero checkpoint_path está vacío."
            )
        checkpoint_path = Path(str(checkpoint))
        if not checkpoint_path.is_absolute():
            checkpoint_path = project_path(str(checkpoint))
        if not checkpoint_path.exists():
            raise FileNotFoundError(
                f"No existe el checkpoint NMT configurado: {checkpoint_path}"
            )
        return str(checkpoint_path), "controlled_10k"

    return str(cfg.get("model_name", DEFAULT_MODEL_NAME)), "base"


class MarianTranslator:
    """Traductor español -> inglés basado en MarianMT."""

    def __init__(
        self,
        model_name_or_path: str | None = None,
        device: str | torch.device | None = None,
        max_length: int | None = None,
        num_beams: int | None = None,
    ) -> None:
        cfg = load_translation_config()
        self.model_name_or_path, self.checkpoint_kind = resolve_translation_model(
            model_name_or_path
        )
        self.max_length = max_length or int(cfg.get("max_length", 128))
        # num_beams=4 es un HIPERPARÁMETRO INICIAL de baseline, no un resultado definitivo.
        self.num_beams = num_beams or int(cfg.get("num_beams", 4))

        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name_or_path)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name_or_path)
        self.model.to(self.device)
        self.model.eval()

    def translate(self, text: str, max_length: int | None = None, num_beams: int | None = None) -> str:
        """Traduce una oración de español a inglés."""
        if not text or not text.strip():
            return ""
        batch_result = self.translate_batch([text], max_length=max_length, num_beams=num_beams)
        return batch_result[0] if batch_result else ""

    def translate_batch(
        self,
        texts: Sequence[str],
        batch_size: int = 16,
        max_length: int | None = None,
        num_beams: int | None = None,
    ) -> list[str]:
        """Traduce una lista de oraciones en lotes utilizando torch.no_grad()."""
        if not texts:
            return []

        out_max_length = max_length or self.max_length
        out_num_beams = num_beams or self.num_beams
        results: list[str] = []

        for i in range(0, len(texts), batch_size):
            batch = list(texts[i : i + batch_size])
            inputs = self.tokenizer(
                batch,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=out_max_length,
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                generated_tokens = self.model.generate(
                    **inputs,
                    max_length=out_max_length,
                    num_beams=out_num_beams,
                )

            decoded = self.tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)
            results.extend([s.strip() for s in decoded])

        return results


def translate(text: str, model_name_or_path: str = DEFAULT_MODEL_NAME) -> str:
    """Función de interfaz directa para traducir un solo texto."""
    translator = MarianTranslator(model_name_or_path=model_name_or_path)
    return translator.translate(text)


def translate_batch(texts: list[str], model_name_or_path: str = DEFAULT_MODEL_NAME) -> list[str]:
    """Función de interfaz directa para traducir un lote de textos."""
    translator = MarianTranslator(model_name_or_path=model_name_or_path)
    return translator.translate_batch(texts)
