# Resultados de Smoke Tests y Verificación de Ejecución

**Proyecto:** Traducción de Mensajes de Audio con Clonación de Voz mediante Inteligencia Artificial  
**Fecha:** Octubre 2026  
**Entorno de Ejecución:** Linux x86_64 / NVIDIA GeForce RTX 5060 Laptop GPU (8 151 MiB VRAM, Driver 615.71.09, CUDA 13.4)

---

## 1. Verificación del Entorno y GPU

Se validó la disponibilidad de aceleración por hardware con PyTorch sobre la GPU local del sistema:
- **Dispositivo:** `NVIDIA GeForce RTX 5060 Laptop GPU` (`cuda:0`)
- **PyTorch:** 2.6.x (con CUDA activado)
- **VRAM Total:** 8 151 MiB
- **`torch.cuda.is_available()`:** `True`

---

## 2. Análisis Empírico de Longitud de Tokens (Fase 1)

**Script:** `src/translation/analyze_lengths.py`  
**Artefacto generado:** [outputs/metrics/token_length_analysis.json](file:///home/setrox/Projects/University/IA-Proyecto/outputs/metrics/token_length_analysis.json)  
**Tokenizador oficial:** `Helsinki-NLP/opus-mt-es-en`  
**Muestra evaluada:** 10 000 pares aleatorios de OPUS-100 `en-es` (sin truncamiento).

### Métricas de distribución de tokens:

| Métrica | Español (Fuente ES) | Inglés (Destino EN) |
| :--- | :---: | :---: |
| **Muestras** | 10 000 | 10 000 |
| **Media** | 14.57 tokens | 14.46 tokens |
| **Mediana** | 9.0 tokens | 10.0 tokens |
| **Percentil 90 (p90)** | 31.1 tokens | 30.0 tokens |
| **Percentil 95 (p95)** | 47.0 tokens | 42.0 tokens |
| **Percentil 99 (p99)** | 76.0 tokens | 71.0 tokens |
| **Máximo observado** | 798 tokens | 867 tokens |
| **% Secuencias > 128** | **0.11%** | **0.07%** |
| **% Secuencias > 256** | 0.02% | 0.02% |
| **% Secuencias > 512** | 0.01% | 0.01% |

### Resolución empírica de la discrepancia (Informe vs. Config):
- **Evidencia:** El 99.89% de las oraciones en español y el 99.93% en inglés tienen menos de 128 tokens.
- **Decisión adoptada:** Se adopta **`max_length = 128`** (ratificando el informe técnico y corrigiendo el valor obsoleto de 512 en `configs/translation.yaml`). Esto reduce el consumo de memoria cuadrático en los bloques de atención y acelera el entrenamiento sin apenas truncamiento lingüístico.

---

## 3. Smoke Test de Inferencia NMT Base (Fases 2 y 3)

**Módulo:** [src/translation/model.py](file:///home/setrox/Projects/University/IA-Proyecto/src/translation/model.py) (`MarianTranslator`)  
**Notebook:** [notebooks/translation/00_nmt_base_smoke_test.ipynb](file:///home/setrox/Projects/University/IA-Proyecto/notebooks/translation/00_nmt_base_smoke_test.ipynb)  
**Artefacto generado:** [outputs/smoke_tests/nmt_base_results.json](file:///home/setrox/Projects/University/IA-Proyecto/outputs/smoke_tests/nmt_base_results.json)  
**Modelo:** `Helsinki-NLP/opus-mt-es-en` (pesos preentrenados oficiales)  
**Parámetros:** `device = cuda`, `num_beams = 4` (hiperparámetro inicial provisional), `max_length = 128`.

### Resultados de inferencia sobre 5 muestras de OPUS-100 TEST:

| # | Texto Español (SOURCE_ES) | Referencia Inglés (REFERENCE_EN) | Predicción MarianMT Base (PREDICTION_BASE) |
| :---: | :--- | :--- | :--- |
| 1 | Si su país produjo SAO para estos usos, sírvase anotar en la columna 6 del formulario de datos 3 la cantidad correspondiente”. | If your country produced ODS for this purpose, please enter the amount so produced in column 6 on Data Form 3.” | If your country has produced ODS for these uses, please enter the corresponding amount in column 6 of data form 3.” |
| 2 | # Juvie el gran hombre, ¿quién podría ser sino yo? | ♪ juvie the great man, who else could it be but I? | # Juvie the great man, who could it be but me? |
| 3 | El planeta madre se está agotando. | The home planet is running out. | Mother planet's running low. |
| 4 | Las chicas no matan a sus madres? . | Oon't girls ever kill their mothers? | Girls don't kill their mothers. |
| 5 | Actividades humanitarias, de recuperación y de desarrollo | Humanitarian, recovery and development activities | Humanitarian, recovery and development activities |

### Métricas de ejecución:
- **Dispositivo:** CUDA (`NVIDIA GeForce RTX 5060 Laptop GPU`)
- **Latencia promedio:** 3 265.31 ms / muestra (con beam search = 4)
- **SacreBLEU (Smoke Test):** 36.33
- **chrF (Smoke Test):** 68.82
- *Aviso:* SMOKE TEST — ESTAS MÉTRICAS NO REPRESENTAN LA EVALUACIÓN FINAL DEL MODELO.

---

## 4. Smoke Test de Fine-Tuning NMT (Fases 4, 5 y 6)

**Módulo de datos:** [src/translation/data.py](file:///home/setrox/Projects/University/IA-Proyecto/src/translation/data.py)  
**Script de entrenamiento:** [src/translation/train.py](file:///home/setrox/Projects/University/IA-Proyecto/src/translation/train.py)  
**Notebook:** [notebooks/translation/01_nmt_finetuning_smoke_test.ipynb](file:///home/setrox/Projects/University/IA-Proyecto/notebooks/translation/01_nmt_finetuning_smoke_test.ipynb)  
**Artefacto generado:** [outputs/smoke_tests/nmt_training/train_metrics.json](file:///home/setrox/Projects/University/IA-Proyecto/outputs/smoke_tests/nmt_training/train_metrics.json)

### Configuración Debug Ejecutada:
- **Train Samples:** 256 pares
- **Eval Samples:** 64 pares
- **Épocas:** 1.0 (32 pasos globales)
- **Batch Size:** 8
- **Optimizador:** AdamW (`lr = 5e-5`, `weight_decay = 0.01`)
- **Warmup:** 4 pasos lineales
- **Label Smoothing:** 0.1
- **Precisión Mixta:** `fp16 = True` (CUDA)
- **Decodificación de evaluación:** `predict_with_generate = True`, `num_beams = 4`, `max_length = 128`

### Resultados reales de la ejecución:
- **Estado:** Completado sin errores de memoria ni colapso de gradientes.
- **Duración total:** 10.82 segundos
- **Pico de VRAM:** 1 716.62 MB (muy holgado en 8 GB de GPU)
- **Pérdida de entrenamiento (Train Loss):** 2.2569
- **Pérdida de evaluación (Eval Loss):** 2.5663
- **SacreBLEU Smoke:** 41.63
- **chrF Smoke:** 64.74

---

## 5. Comparación: Modelo Base vs. Modelo Debug (Fase 7)

**Artefacto generado:** [outputs/smoke_tests/nmt_base_vs_debug.json](file:///home/setrox/Projects/University/IA-Proyecto/outputs/smoke_tests/nmt_base_vs_debug.json)  
**Conjunto de evaluación idéntico:** 64 pares del split de validación.

| Métrica | Modelo Base (Sin entrenar) | Modelo Debug (256 pares, 1 época) | Delta |
| :--- | :---: | :---: | :---: |
| **Eval Loss** | 2.5513 | 2.5663 | +0.0150 |
| **SacreBLEU** | 42.33 | 41.63 | -0.70 |
| **chrF** | 64.80 | 64.74 | -0.06 |

> **Interpretación metodológica:** El test comparativo demuestra que la integración del pipeline de evaluación y fine-tuning opera de manera correcta y estable. Con solo 256 pares y 1 época no se pretende superar los pesos preentrenados de MarianMT; el objetivo era validar de forma no invasiva la canalización de entrenamiento antes de autorizar el ciclo completo de 100 000 pares.

---

## 6. Smoke Test de Inferencia ASR con Whisper-Small (Fases 8 y 9)

**Módulo:** [src/asr/transcribe.py](file:///home/setrox/Projects/University/IA-Proyecto/src/asr/transcribe.py)  
**Notebook:** [notebooks/asr/00_whisper_smoke_test.ipynb](file:///home/setrox/Projects/University/IA-Proyecto/notebooks/asr/00_whisper_smoke_test.ipynb)  
**Artefacto generado:** [outputs/smoke_tests/asr_results.json](file:///home/setrox/Projects/University/IA-Proyecto/outputs/smoke_tests/asr_results.json)  
**Modelo:** `openai/whisper-small`  
**Configuración:** Audio 16 kHz mono, `language = "es"`, `task = "transcribe"` (sin traducción cruzada).  
**Conjunto de prueba:** 3 muestras de FLEURS `es_419` descargadas en [outputs/smoke_tests/audio/](file:///home/setrox/Projects/University/IA-Proyecto/outputs/smoke_tests/audio/).

### Resultados de transcripción:

| Muestra ID | Duración (s) | Latencia (s) | Transcripción Ground Truth (FLEURS) | Predicción Whisper-Small | WER (%) | CER (%) |
| :--- | :---: | :---: | :--- | :--- | :---: | :---: |
| `fleurs_es_419_smoke_00` | 8.88 s | 6.20 s | Exactamente a las 8:46 a. m., la ciudad se volvió silencio, marcando el preciso instante en el que el primer avión alcanzó su objetivo. | Exactamente a las 8.46 a.m. la ciudad se volvió silencio, marcando de preciso instante en el que el primer avión alcanzó su objetivo. | 16.67% | 3.70% |
| `fleurs_es_419_smoke_01` | 8.94 s | 0.31 s | Por lo general, las hembras se relacionan estrechamente entre sí, lo que las hace una gran familia de hermanas e hijas. | Por lo general, las hembras se relacionan estrechamente entre sí, lo que las hace una gran familia de hermanas e hijas. | **0.00%** | **0.00%** |
| `fleurs_es_419_smoke_02` | 8.64 s | 0.35 s | Recuerde incluir los gastos adicionales, los impuestos de partida, el transporte terrestre, etc. para todos los lugares que visite fuera de África. | Recuerda incluir los gastos adicionales, los impuestos de partida, el transporte terrestre, etcétera para todos los lugares que visite fuera de África. | 9.09% | 4.08% |

### Métricas resumen ASR:
- **WER Promedio:** 8.59%
- **CER Promedio:** 2.59%
- **Tiempo de inferencia promedio:** 2.285 s (tiempo en caliente: ~0.30 - 0.35 s por audio de 8.9 s, Real-Time Factor < 0.04)
- *Aviso:* SMOKE TEST — 3 MUESTRAS. NO ES UNA EVALUACIÓN GLOBAL DE WHISPER.

---

## 7. Pruebas Unitarias Automatizadas (Fase 11)

Se ejecutó la suite de tests unitarios completa con `pytest`:
- **Comando:** `pytest tests/unit/`
- **Archivos probados:**
  - [tests/unit/test_dataset_pipeline.py](file:///home/setrox/Projects/University/IA-Proyecto/tests/unit/test_dataset_pipeline.py): 3 tests (fleurs streaming, decodificación sin torchcodec, split paralelo).
  - [tests/unit/test_translation.py](file:///home/setrox/Projects/University/IA-Proyecto/tests/unit/test_translation.py): 5 tests (configs ASR/NMT, percentiles de tokens, preprocesamiento con DummyTokenizer, collator).
- **Resultado:** **8 PASSED (100% de éxito en 2.52 segundos)**.

## 8. Preparación XTTS-v2, ECAPA y Pipeline para Google Colab (sin resultados inventados)

Se añadieron los módulos y notebooks de ejecución para Colab: `notebooks/voice_cloning/00_xtts_smoke_test.ipynb`, `01_xtts_ecapa_evaluation.ipynb`, `notebooks/pipeline/00_end_to_end_smoke_test.ipynb` y `01_gradio_demo.ipynb`. La combinación aislada importada localmente fue Python 3.11.15, torch/torchaudio 2.8.0+cu128, transformers 4.57.3, coqui-tts 0.27.5, speechbrain 1.1.1 y numpy 2.4.6.

La resolución libre con `transformers 5.19.0` **falló**: XTTS no pudo importar `isin_mps_friendly`; por ello no se usa. La ejecución XTTS, ECAPA, pipeline y Gradio en Colab está pendiente y no existen valores de similitud, RTF total ni resultados MOS que puedan reportarse todavía.

La suite de contratos actualizada se ejecutó en el entorno aislado: **13 passed en 3.07 s** (`pytest tests/unit/ tests/integration/`).
