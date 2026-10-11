# 4.2 Desarrollo e Implementación del Modelo

## 4.2.1 Entorno y organización del repositorio

NMT y ASR cuentan con evidencia ejecutada previa en Colab Tesla T4. Para XTTS/ECAPA se incorporó un runtime independiente reproducible: Python 3.11.15, torch/torchaudio 2.8.0+cu128, transformers 4.57.3, coqui-tts 0.27.5, speechbrain 1.1.1 y numpy 2.4.6. La combinación fue importada localmente en RTX 5060; la ejecución en Colab queda pendiente de registrar desde los notebooks.

La organización incorpora `src/voice_cloning/audio.py`, `synthesize.py`, `src/evaluation/speaker_similarity.py`, `src/pipeline/runner.py` y `demo.py`. NMT y ASR previamente validados no fueron modificados.

## 4.2.2 Preparación de los datos para el entrenamiento

Dataset A: OPUS-100, 100000 train, 1990 validation, 1999 test, seed 42. Dataset B: FLEURS es_419, 20 audios, 14 dev y 6 test, 203.34 s, WAV mono 16 kHz y sin `speaker_id`. Marian usa su tokenizador oficial, `max_length=128`, padding dinámico y `DataCollatorForSeq2Seq`. La justificación de 128 procede de 10000 pares: p99 ES=76 y EN=71.

## 4.2.3 Configuración de hiperparámetros

**Ejecutados en smoke test:** batch 8, LR 5e-5, AdamW, weight decay 0.01, label smoothing 0.1, FP16, beam 4, max length 128 y seed 42.

**Propuestos para full training (no ejecutados):** 100000 pares, 1990 validation y 3 épocas. No deben presentarse como experimentos realizados.

## 4.2.4 Entrenamiento (fine-tuning) del modelo

El único entrenamiento ejecutado es debug: 256 pares train, 64 validation y una época; AdamW y FP16. Validó el proceso técnico. Full training 100k: **PENDIENTE**.

## 4.2.5 Comparación entre modelo base y modelo ajustado

En 64 ejemplos idénticos: base: Eval Loss 2.5514, BLEU 42.33, chrF 64.80. Debug: Eval Loss 2.5663, BLEU 40.93, chrF 64.33. No se demostró mejora; sí se validó el proceso de entrenamiento.

## 4.2.6 Integración del pipeline Speech-to-Speech

La integración implementada es Whisper-small → MarianMT base → XTTS-v2 → ECAPA. Sus contratos y el flujo completo están cubiertos con mocks (13 tests en total aprobados localmente). El notebook `notebooks/pipeline/00_end_to_end_smoke_test.ipynb` está preparado para generar evidencia real sobre 3 DEV, incluyendo tiempos, RTF, WER cuando existe referencia y artefactos por muestra. **No hay aún ejecución real XTTS/pipeline registrada; esta subsección permanece pendiente de evidencia Colab.**

## 4.2.7 Evaluación de la similitud vocal e interfaz de demostración

ECAPA está implementado como coseno continuo entre embeddings preentrenados, sin umbral de “misma voz”. `notebooks/voice_cloning/01_xtts_ecapa_evaluation.ipynb` guardará media, mínimo y máximo de las tres muestras. La plantilla humana está en `evaluation/voice_cloning/mos_template.csv`; no contiene evaluadores ni resultados inventados. La interfaz está implementada en `src/pipeline/demo.py` y se expone mediante `notebooks/pipeline/01_gradio_demo.ipynb`; falta su ejecución real con los modelos en Colab.

## Discrepancias y trazabilidad

| Afirmación | Evidencia | Estado |
|---|---|---|
| Whisper-small | Notebook y JSON ASR ejecutados; WER 8.59%, CER 2.59% | CONFIRMADO SOLO COMO SMOKE TEST |
| MarianMT base | Notebook y JSON NMT ejecutados; BLEU 36.33, chrF 68.82 | CONFIRMADO SOLO COMO SMOKE TEST |
| XTTS-v2 | Código, entorno aislado importado y notebook Colab preparado | PROPUESTO / NO EJECUTADO |
| ECAPA | Código y contrato unitario; notebook de medición preparado | PROPUESTO / NO EJECUTADO |
| max_length 128 | Análisis sobre 10000 pares | CONFIRMADO |
| beam 4 | Configuración y smoke NMT | CONFIRMADO SOLO COMO SMOKE TEST |
| AdamW, label smoothing 0.1, FP16 | Smoke fine-tuning 256/64/1 época | CONFIRMADO SOLO COMO SMOKE TEST |
| NMT full training | No ejecutado por decisión explícita | PENDIENTE |
| Pipeline S2S | Contrato con mocks; no inferencia real completa | PROPUESTO / NO EJECUTADO |
| speaker similarity | Contrato ECAPA; no valores de audios XTTS reales | PROPUESTO / NO EJECUTADO |
| Gradio | Implementación disponible; no demo Colab ejecutada | PROPUESTO / NO EJECUTADO |
