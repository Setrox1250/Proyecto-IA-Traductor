# Evidencia Empírica para la Sección 4.2 del Informe Académico

Este documento recopila la evidencia técnica, experimental y cuantitativa extraída directamente de las ejecuciones reales en el repositorio, estructurada para su inserción y citación en las secciones 4.2.1 a 4.2.4 del informe final.

---

## 4.2.1 Entorno de Ejecución

### Hardware y Sistema Operativo
- **Sistema Operativo:** Linux x86_64 (Kernel 6.16)
- **Unidad de Procesamiento Gráfico (GPU):** NVIDIA GeForce RTX 5060 Laptop GPU
- **Memoria VRAM Total:** 8 151 MiB
- **Versión de Driver NVIDIA:** 615.71.09
- **Soporte de CUDA en Driver:** 13.4

### Ecosistema de Software y Librerías Principales
- **Intérprete Python:** 3.11.15
- **Framework de Deep Learning:** PyTorch 2.6.x (con soporte `cuda:0` activado)
- **Hugging Face Transformers:** 5.0.0.dev0 / 4.49.x
- **Tokenizadores y Procesamiento Textual:** SentencePiece 0.1.99, Sacremoses 0.1.1
- **Hugging Face Datasets:** 4.0.0 (con `pyarrow 18.1.0` para garantizar compatibilidad binaria)
- **Evaluación y Métricas:** SacreBLEU 2.5.1, Evaluate 0.4.3, JIWER 3.1.0
- **Audio y Señales:** SoundFile 0.13.1, SciPy 1.15.2

---

## 4.2.2 Preparación del Corpus y Tokenización

### Tokenizador Oficial
- **Identificador del Modelo:** `Helsinki-NLP/opus-mt-es-en`
- **Tipo:** Modelo Sequence-to-Sequence basado en la arquitectura Marian Transformer (encoder-decoder).
- **Vocabulario:** SentencePiece BPE bilingüe español-inglés.

### Justificación Empírica de `max_length = 128`
Ante la discrepancia inicial entre la especificación teórica del informe (`max_length = 128`) y el archivo de configuración original (`max_length = 512`), se desarrolló el script [src/translation/analyze_lengths.py](file:///home/setrox/Projects/University/IA-Proyecto/src/translation/analyze_lengths.py).

Se evaluaron **10 000 pares de oraciones** del split de entrenamiento de OPUS-100 `en-es` sin truncamiento ([outputs/metrics/token_length_analysis.json](file:///home/setrox/Projects/University/IA-Proyecto/outputs/metrics/token_length_analysis.json)):

- **Español (Texto de entrada):**
  - Longitud promedio: 14.57 tokens
  - Mediana: 9.0 tokens
  - Percentil 90 (p90): 31.1 tokens
  - Percentil 95 (p95): 47.0 tokens
  - Percentil 99 (p99): 76.01 tokens
  - Secuencias mayores a 128 tokens: **0.11%** (11 de cada 10 000)
  - Secuencias mayores a 256 tokens: 0.02%
  - Secuencias mayores a 512 tokens: 0.01%
- **Inglés (Texto de referencia/objetivo):**
  - Longitud promedio: 14.46 tokens
  - Mediana: 10.0 tokens
  - Percentil 90 (p90): 30.0 tokens
  - Percentil 95 (p95): 42.0 tokens
  - Percentil 99 (p99): 71.0 tokens
  - Secuencias mayores a 128 tokens: **0.07%** (7 de cada 10 000)
  - Secuencias mayores a 256 tokens: 0.02%
  - Secuencias mayores a 512 tokens: 0.01%

**Conclusión experimental:** Establecer `max_length = 128` retiene de forma intacta más del **99.89%** de las oraciones en español y el **99.93%** en inglés. Fijar una longitud de 512 hubiera supuesto un 75% de padding artificial innecesario, cuadruplicando la complejidad cuadrática $O(N^2)$ de la atención en memoria. Por tanto, `max_length = 128` queda validado empíricamente.

### Estrategia de Colación y Padding
- **Componente:** `DataCollatorForSeq2Seq` implementado en [src/translation/data.py](file:///home/setrox/Projects/University/IA-Proyecto/src/translation/data.py).
- **Padding:** Dinámico por lote (rellena hasta la longitud máxima observada dentro de cada minilote, no hasta 128).
- **Enmascaramiento de etiquetas:** Los tokens de relleno (`pad_token_id`) en la secuencia de destino se asignan a `-100` para excluirlos del cómputo de la función de pérdida de entropía cruzada.

### Dimensiones de los Datasets
- **Dataset A — OPUS-100 (Fine-Tuning NMT):**
  - Entrenamiento (`train`): 100 000 pares (96.164%)
  - Validación (`validation`): 1 990 pares (1.914%)
  - Prueba (`test`): 1 999 pares (1.922%)
  - Semilla pseudoaleatoria: 42
  - Criterio de aislamiento: Eliminación bidireccional estricta de solapamientos entre las particiones retenidas y el conjunto de entrenamiento.
- **Dataset B — FLEURS `es_419` (Evaluación Modular y Speech-to-Speech):**
  - Muestras totales: 20 archivos de audio (16 kHz mono)
  - Split Dev: 14 muestras (70%)
  - Split Test: 6 muestras (30%)
  - Duración acumulada: **203.34 segundos** (mínima: 6.06 s, máxima: 18.12 s, media: 10.167 s)
  - Identificador de locutor: No provisto en FLEURS (`speaker_id = None`). División estratificada por oración mediante semilla 42.

---

## 4.2.3 Hiperparámetros de Entrenamiento

Para preservar el rigor metodológico, se distingue formalmente entre los parámetros evaluados en el **Smoke Test / Debug** y la **Configuración Final Pendiente**:

| Parámetro / Decisión | Configuración Smoke Test (Ejecutada) | Configuración Final (Prevista para 100k) | Justificación Metodológica |
| :--- | :---: | :---: | :--- |
| **Muestras Train** | 256 pares | 100 000 pares | Validar el grafo computacional sin coste masivo de GPU. |
| **Muestras Validation**| 64 pares | 1 990 pares | Evaluación rápida de convergencia. |
| **Épocas** | 1.0 (32 pasos) | 3.0 (estimadas) | Verificación de forward/backward y optimizador. |
| **Batch Size (por dispositivo)** | 8 | 16 o 32 (según VRAM) | Evitar OOM en GPU de 8 GB. |
| **Gradient Accumulation** | 1 | 2 o 4 | Tamaño de lote efectivo mayor en GPU estándar. |
| **Optimizador** | AdamW | AdamW | Optimizador estándar con desacoplamiento de weight decay. |
| **Learning Rate** | $5 \times 10^{-5}$ | $5 \times 10^{-5}$ | Tasa de aprendizaje adaptativa para fine-tuning fino. |
| **Weight Decay** | 0.01 | 0.01 | Regularización $L_2$ contra sobreajuste. |
| **Warmup** | 4 pasos lineales (~10%) | 1 000 pasos lineales (~10%) | Estabilización inicial de gradientes en capas profundas. |
| **Label Smoothing** | 0.1 | 0.1 | Previene sobreconfianza en probabilidades de salida. |
| **Precisión Mixta** | FP16 (`fp16 = True`) | FP16 (`fp16 = True`) | Aceleración en Tensor Cores y reducción a la mitad de uso de VRAM. |
| **Decodificación Eval** | Beam Search ($k=4$) | Beam Search ($k=4$) | Búsqueda por haz para traducción consistente. |
| **Longitud Máxima** | 128 | 128 | Respaldada por el análisis de percentiles del corpus. |
| **Semilla (Seed)** | 42 | 42 | Reproducibilidad estricta de particiones y pesos. |

---

## 4.2.4 Evidencia de Fine-Tuning y Smoke Tests Ejecutados

### A. Ejecución del Smoke Test de Fine-Tuning (Modo Debug)
- **Script ejecutado:** [src/translation/train.py](file:///home/setrox/Projects/University/IA-Proyecto/src/translation/train.py) con argumento `--debug`.
- **Notebook interactivo:** [notebooks/translation/01_nmt_finetuning_smoke_test.ipynb](file:///home/setrox/Projects/University/IA-Proyecto/notebooks/translation/01_nmt_finetuning_smoke_test.ipynb).
- **Registro JSON de métricas:** [outputs/smoke_tests/nmt_training/train_metrics.json](file:///home/setrox/Projects/University/IA-Proyecto/outputs/smoke_tests/nmt_training/train_metrics.json).

#### Métricas registradas:
- **Dispositivo empleado:** `NVIDIA GeForce RTX 5060 Laptop GPU`
- **Pico máximo de memoria VRAM:** **1 716.62 MB** (consumo muy moderado, 21% de la GPU disponible).
- **Tiempo total de entrenamiento (32 pasos):** **10.82 segundos** (24.23 muestras/segundo).
- **Pérdida final de entrenamiento (Train Loss):** 2.2569
- **Pérdida de validación (Eval Loss):** 2.5663
- **SacreBLEU en validación debug:** 41.63
- **chrF en validación debug:** 64.74

### B. Comparación Controlada: Modelo Base vs. Modelo Debug
- **Registro JSON comparativo:** [outputs/smoke_tests/nmt_base_vs_debug.json](file:///home/setrox/Projects/University/IA-Proyecto/outputs/smoke_tests/nmt_base_vs_debug.json).
- **Procedimiento:** Evaluación sobre exactamente los mismos 64 pares de validación antes y después del fine-tuning debug.

| Modelo Evaluado | Pérdida de Validación (Loss) | SacreBLEU | chrF |
| :--- | :---: | :---: | :---: |
| **MarianMT Base** (pesos congelados preentrenados) | 2.5513 | 42.33 | 64.80 |
| **MarianMT Debug** (adaptado 256 muestras, 1 época) | 2.5663 | 41.63 | 64.74 |
| **Diferencia ($\Delta$)** | +0.0150 | -0.70 | -0.06 |

*Interpretación:* La pequeña variación ($\Delta = -0.70$ BLEU) es teóricamente coherente: un ciclo breve de 256 pares introduce una adaptación local sin desplazar los millones de pares del preentrenamiento. La prueba valida que la canalización completa (forward, backward, opt, evaluación generativa y métricas) funciona de forma robusta.

### C. Inferencia ASR con Whisper-Small
- **Módulo ejecutado:** [src/asr/transcribe.py](file:///home/setrox/Projects/University/IA-Proyecto/src/asr/transcribe.py).
- **Notebook interactivo:** [notebooks/asr/00_whisper_smoke_test.ipynb](file:///home/setrox/Projects/University/IA-Proyecto/notebooks/asr/00_whisper_smoke_test.ipynb).
- **Registro JSON:** [outputs/smoke_tests/asr_results.json](file:///home/setrox/Projects/University/IA-Proyecto/outputs/smoke_tests/asr_results.json).
- **Muestras:** 3 audios reales de FLEURS `es_419` procesados en GPU a 16 kHz mono.
- **Resultados:**
  - **WER promedio:** **8.59%**
  - **CER promedio:** **2.59%**
  - **Latencia por audio de ~9 segundos:** **0.31 - 0.35 s** (Real-Time Factor $\text{RTF} \approx 0.038$).
  - Una de las muestras obtuvo transcripción 100% idéntica (WER 0.0%, CER 0.0%).
