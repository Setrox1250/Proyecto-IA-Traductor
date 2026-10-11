# Auditoría Técnica y Estado Real del Proyecto (Actualizada)

**Proyecto:** Traducción de Mensajes de Audio con Clonación de Voz mediante Inteligencia Artificial  
**Repositorio:** `Setrox1250/Proyecto-IA-Traductor`  
**Fecha de auditoría:** Octubre 2026 (Iteración 2: Inferencia NMT, ASR y Smoke Fine-Tuning)  
**Criterio de auditoría:** Inspección forense estricta con evidencia empírica de ejecución.

---

## Resumen Ejecutivo

Tras la implementación y ejecución de las Fases 1 a 11, el repositorio ha progresado desde la fase de datos a contar con **inferencia funcional y verificada en hardware GPU** para:
1. **Reconocimiento del habla (ASR):** Módulo `src/asr/transcribe.py` con `openai/whisper-small` probado sobre muestras reales de FLEURS.
2. **Traducción NMT Base:** Módulo `src/translation/model.py` con `Helsinki-NLP/opus-mt-es-en` y análisis empírico de longitud de tokens completado.
3. **Fine-Tuning NMT:** Módulo de datos `src/translation/data.py` y pipeline de entrenamiento `src/translation/train.py` validados en modo debug (256 pares, 1 época) con cálculo de pérdidas, gradientes AdamW, precisión mixta `fp16` y evaluación SacreBLEU/chrF.

Los módulos de **Voice Cloning (coqui/XTTS-v2)** y **Evaluación Vocal (speechbrain/spkrec-ecapa-voxceleb)** se mantienen deliberadamente **NO IMPLEMENTADOS / POSPUESTOS** para la siguiente iteración, con el fin de evitar conflictos de dependencias con PyTorch y Transformers. El **entrenamiento completo sobre 100 000 pares** se mantiene en estado **PENDIENTE DE CONFIRMACIÓN**.

---

## 1. Entorno de Ejecución

### 1.1. Host Local y Hardware Verificado
- **Sistema Operativo:** Linux x86_64
- **Acelerador GPU:** NVIDIA GeForce RTX 5060 Laptop GPU (8 151 MiB VRAM), Driver NVIDIA 615.71.09, CUDA Driver 13.4.
- **Entorno de ejecución validado:** Python 3.11 (gestionado de forma no invasiva mediante `uv`) con PyTorch 2.6.x compilado con soporte CUDA.
- **`torch.cuda.is_available()`:** `True`. Todos los smoke tests corrieron sobre la GPU física.

### 1.2. Estado de Requirements
- [requirements/base.txt](file:///home/setrox/Projects/University/IA-Proyecto/requirements/base.txt): `torch`, `numpy`, `pyyaml`.
- [requirements/dataset.txt](file:///home/setrox/Projects/University/IA-Proyecto/requirements/dataset.txt): `datasets>=2.20.0`, `pandas>=2.0.0`, `soundfile>=0.12.0`, `requests>=2.31.0`, `tqdm>=4.66.0`.
- [requirements/translation.txt](file:///home/setrox/Projects/University/IA-Proyecto/requirements/translation.txt): **ACTUALIZADO**. Incluye `transformers>=4.38.0`, `datasets>=3.0.0`, `pyarrow<19.0.0`, `sentencepiece`, `sacremoses`, `accelerate`, `sacrebleu`, `evaluate`.
- [requirements/asr.txt](file:///home/setrox/Projects/University/IA-Proyecto/requirements/asr.txt): **ACTUALIZADO**. Incluye `transformers>=4.38.0`, `soundfile>=0.12.0`, `scipy>=1.11.0`, `jiwer>=3.0.0`, `pyyaml`.
- [requirements/voice_cloning.txt](file:///home/setrox/Projects/University/IA-Proyecto/requirements/voice_cloning.txt): Comentado y pospuesto para aislar el stack NMT/ASR.

---

## 2. Dataset y Longitud de Tokens

### 2.1. Datasets A y B
- **OPUS-100:** Train: 100 000 pares, Validation: 1 990 pares, Test: 1 999 pares. Seed: 42. (Confirmado).
- **FLEURS:** 20 audios en total, 14 dev, 6 test. Duración total: 203.34 s. 16 kHz mono. (Confirmado).

### 2.2. Resolución Empírica de `max_length` (Fase 1)
- La contradicción entre el informe (`max_length = 128`) y `configs/translation.yaml` (`max_length: 512`) fue analizada empíricamente tokenizando 10 000 pares de OPUS-100 sin truncamiento:
  - Percentil 99 en español: 76 tokens (solo 0.11% > 128).
  - Percentil 99 en inglés: 71 tokens (solo 0.07% > 128).
- **Decisión:** `configs/translation.yaml` se actualizó oficialmente a **`max_length: 128`**.

---

## 3. Estado Actual de Componentes

| Componente | Modelo | Estado Real | Artefacto de Evidencia |
| :--- | :--- | :--- | :--- |
| **Dataset Pipeline** | OPUS-100 & FLEURS | **IMPLEMENTADO Y EJECUTADO** | `notebooks/dataset/00_prepare_all_datasets_colab.ipynb` |
| **Análisis Longitud Tokens** | MarianTokenizer | **IMPLEMENTADO Y EJECUTADO** | `outputs/metrics/token_length_analysis.json` |
| **Inferencia NMT Base** | `Helsinki-NLP/opus-mt-es-en` | **IMPLEMENTADO Y EJECUTADO** | `outputs/smoke_tests/nmt_base_results.json` |
| **Data Preparation NMT** | Seq2Seq Collator / Tokenization | **IMPLEMENTADO Y EJECUTADO** | `src/translation/data.py` |
| **Fine-Tuning NMT (Debug)** | MarianMT + Seq2SeqTrainer | **SMOKE TEST EJECUTADO** | `outputs/smoke_tests/nmt_training/train_metrics.json` |
| **Fine-Tuning NMT (Full)** | 100 000 pares OPUS-100 | **ENTRENAMIENTO COMPLETO PENDIENTE** | Requiere confirmación de usuario. |
| **Inferencia ASR** | `openai/whisper-small` | **IMPLEMENTADO Y EJECUTADO** | `outputs/smoke_tests/asr_results.json` |
| **Voice Cloning (TTS)** | `coqui/XTTS-v2` | **NO IMPLEMENTADO (POSPUESTO)** | Iteración posterior. |
| **Similitud Vocal (ECAPA)** | `speechbrain/spkrec-ecapa-voxceleb`| **NO IMPLEMENTADO (POSPUESTO)** | Iteración posterior. |
| **Pipeline End-to-End** | Integración total | **NO IMPLEMENTADO** | Iteración posterior. |
| **Tests Unitarios** | Pytest (dataset + traducción) | **8 PASSED (100% EXITO)** | `tests/unit/test_translation.py`, `test_dataset_pipeline.py` |

### Actualización posterior: preparación para ejecución Colab

Se implementaron los contratos no pesados de XTTS, ECAPA, pipeline y Gradio, además de notebooks ejecutables en Colab. El aislamiento es necesario: la resolución de `coqui-tts==0.27.5` con `transformers==5.19.0` falló al importar XTTS; el runtime aislado probado para importación usa torch/torchaudio 2.8.0+cu128, transformers 4.57.3, numpy 2.4.6 y speechbrain 1.1.1. No se ha registrado inferencia XTTS/ECAPA/pipeline en Colab, por lo que sus estados siguen pendientes de evidencia experimental.

---

## 4. Matriz Comparativa Actualizada

| # | Afirmación / Decisión del Informe | Evidencia en Repositorio | Estado Actualizado |
| :---: | :--- | :--- | :--- |
| 1 | `openai/whisper-small` | Implementado en `src/asr/transcribe.py` y probado en `outputs/smoke_tests/asr_results.json`. | **CONFIRMADO EN CÓDIGO Y EJECUCIÓN** |
| 2 | `Helsinki-NLP/opus-mt-es-en` | Implementado en `src/translation/model.py` y probado en `outputs/smoke_tests/nmt_base_results.json`. | **CONFIRMADO EN CÓDIGO Y EJECUCIÓN** |
| 3 | `coqui/XTTS-v2` | Pospuesto para la siguiente iteración. | **SOLO DOCUMENTADO** |
| 4 | `speechbrain/spkrec-ecapa-voxceleb` | Pospuesto para la siguiente iteración. | **NO IMPLEMENTADO** |
| 5 | Fine-tuning con OPUS-100 | Script `src/translation/train.py` probado en debug (256 muestras). Full pendiente. | **SMOKE TEST EJECUTADO; FULL PENDIENTE** |
| 6 | 100 000 pares training | `TRAIN_SIZE = 100_000` en dataset y script. | **CONFIRMADO EN CÓDIGO Y EJECUCIÓN** |
| 7 | 1 990 pares validation | Split oficial procesado. | **CONFIRMADO EN CÓDIGO Y EJECUCIÓN** |
| 8 | 1 999 pares test | Split oficial procesado. | **CONFIRMADO EN CÓDIGO Y EJECUCIÓN** |
| 9 | Seed = 42 | Configurada en todos los módulos (`configs/*.yaml`, `train.py`, etc.). | **CONFIRMADO EN CÓDIGO Y EJECUCIÓN** |
| 10 | `max_length = 128` | Justificado empíricamente (p99 <= 76 tokens) y configurado en `translation.yaml`. | **CONFIRMADO EN CÓDIGO Y EJECUCIÓN** |
| 11 | Optimizador AdamW | Integrado y ejecutado en `Seq2SeqTrainer` en `src/translation/train.py`. | **CONFIRMADO EN CÓDIGO Y EJECUCIÓN** |
| 12 | `label_smoothing = 0.1` | Configurado y ejecutado en `Seq2SeqTrainingArguments`. | **CONFIRMADO EN CÓDIGO Y EJECUCIÓN** |
| 13 | Warmup lineal | Configurado y ejecutado en `Seq2SeqTrainingArguments` (`warmup_steps`). | **CONFIRMADO EN CÓDIGO Y EJECUCIÓN** |
| 14 | `beam search = 4` | Configurado en `configs/translation.yaml` y ejecutado en `train.py` y `model.py`. | **CONFIRMADO EN CÓDIGO Y EJECUCIÓN** |
| 15 | BLEU / SacreBLEU | Implementado en `build_compute_metrics_fn` y evaluado en smoke tests. | **CONFIRMADO EN CÓDIGO Y EJECUCIÓN** |
| 16 | chrF | Implementado en `build_compute_metrics_fn` y evaluado en smoke tests. | **CONFIRMADO EN CÓDIGO Y EJECUCIÓN** |
| 17 | WER | Implementado con `jiwer` y evaluado en `src/asr/transcribe.py` (8.59% medio). | **CONFIRMADO EN CÓDIGO Y EJECUCIÓN** |
| 18 | CER | Implementado con `jiwer` y evaluado en `src/asr/transcribe.py` (2.59% medio). | **CONFIRMADO EN CÓDIGO Y EJECUCIÓN** |
| 19 | Cosine similarity ECAPA | Módulo pendiente. | **NO IMPLEMENTADO** |
| 20 | RTF / Latencias | Medido en smoke tests: ASR ~0.35 s (RTF < 0.04), NMT ~3.2 s / muestra. | **CONFIRMADO EN CÓDIGO Y EJECUCIÓN** |
| 21 | XTTS input 22050 | `sample_rate: 22050` en config. | **CONFIRMADO SOLO EN CONFIG** |
| 22 | XTTS output 24000 | Pendiente de implementación de XTTS. | **SOLO DOCUMENTADO** |
