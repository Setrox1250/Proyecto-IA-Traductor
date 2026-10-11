"""Demo académica mínima de Gradio para el pipeline Speech-to-Speech."""

from __future__ import annotations

import tempfile
from pathlib import Path

from src.pipeline.runner import process_audio


def _run_demo(audio_path: str):
    if not audio_path:
        raise ValueError("Carga o graba un audio antes de ejecutar el pipeline.")
    with tempfile.TemporaryDirectory(prefix="s2s_demo_") as tmp_dir:
        result = process_audio(audio_path, tmp_dir)
        output = Path(result["audio"]["output_path"])
        # Gradio necesita un archivo que sobreviva al TemporaryDirectory.
        persisted = Path(tempfile.mkstemp(suffix=".wav", prefix="s2s_output_")[1])
        persisted.write_bytes(output.read_bytes())
    return (
        result["transcription_es"],
        result["translation_en"],
        str(persisted),
        f"{result['timings']['total_sec']:.2f} s",
        f"{result['speaker_similarity']:.4f}",
    )


def create_demo():
    """Construye, sin lanzar, la interfaz Gradio para facilitar pruebas."""
    import gradio as gr

    with gr.Blocks(title="Traductor Speech-to-Speech con clonación de voz") as demo:
        gr.Markdown("# Traducción ES→EN con Whisper, MarianMT, XTTS-v2 y ECAPA")
        audio_input = gr.Audio(
            sources=["upload", "microphone"], type="filepath", label="Audio en español"
        )
        run = gr.Button("Procesar")
        transcription = gr.Textbox(label="Transcripción en español")
        translation = gr.Textbox(label="Traducción al inglés")
        audio_output = gr.Audio(label="Audio generado en inglés")
        total_time = gr.Textbox(label="Tiempo total")
        similarity = gr.Textbox(label="Similitud vocal ECAPA (coseno)")
        run.click(
            _run_demo,
            inputs=audio_input,
            outputs=[transcription, translation, audio_output, total_time, similarity],
        )
    return demo


if __name__ == "__main__":
    create_demo().launch()
