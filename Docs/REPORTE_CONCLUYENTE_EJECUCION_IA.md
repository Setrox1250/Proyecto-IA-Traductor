# Dossier Concluyente de Evidencia Experimental y Técnica
## Para la Redacción del Informe Académico (Capítulo 4: Implementación y Evaluación)

> **Destinatario del Documento:** Agente IA / Redactor Académico encargado de redactar el informe técnico y memoria del proyecto.  
> **Proyecto:** *“Traducción de Mensajes de Audio con Clonación de Voz mediante Inteligencia Artificial”*  
> **Repositorio Auditado y Ejecutado:** [Setrox1250/Proyecto-IA-Traductor](https://github.com/Setrox1250/Proyecto-IA-Traductor.git)  
> **Fecha de Actualización:** Octubre 2026 (Revisión técnica exhaustiva con cotejo 1:1 frente a notebooks ejecutados)  
> **Estado de Validación:** Evidencia empírica verificada directamente en los notebooks ejecutados en **Google Colab sobre GPU NVIDIA Tesla T4** (`15 GB VRAM`, PyTorch `2.11.0+cu130`, CUDA `13.0`) y contrastada con el entorno de desarrollo local (`RTX 5060 Laptop GPU`). Cero errores de ejecución, métricas contrastadas sin extrapolaciones no demostradas.

---

## 1. Guía Rápida de Instrucciones para la IA Redactora

Cuando uses la información de este dossier para redactar las secciones del informe (especialmente el Capítulo 4), debes adherirte estrictamente a las siguientes directrices metodológicas:

1. **Rigor Cuantitativo Estricto:** Emplea exactamente los valores numéricos documentados en este informe. No inventes métricas de evaluación final sobre los 100 000 pares, ya que dicho entrenamiento aún no se ha ejecutado.
2. **Distinción Epistemológica Fundamental:** Distingue con total claridad entre:
   - **Pruebas de Humo (Smoke Tests / Debug):** Experimentos de verificación técnica diseñados para comprobar la operatividad del grafo computacional, el consumo de memoria VRAM, la ausencia de desbordamiento (*Out Of Memory*, OOM), la dinámica del optimizador AdamW con precisión mixta FP16, y la generación de secuencias con búsqueda por haz.
   - **Evaluación Final del Sistema:** La fase cuantitativa sobre el corpus completo de 100 000 pares, la cual se encuentra técnicamente planificada y lista para ejecutarse pero no forma parte de esta iteración de validación de pipeline.
3. **Honestidad Intelectual en Resultados:** No presentes la ligera variación de BLEU del smoke test como una "mejora". La conclusión metodológica correcta es que el smoke test demuestra que el pipeline es funcional y estable, sin pretender evaluar la ganancia lingüística con solo 256 pares.
4. **Justificación Técnica Precisa:** Presenta las decisiones de diseño con rigor arquitectural (por ejemplo, el papel de `max_length = 128` como límite de truncamiento combinado con padding dinámico por lote mediante `DataCollatorForSeq2Seq`).
5. **Estrategia Modular Acordada:** Destaca que la arquitectura completa se validará primero de extremo a extremo integrando `XTTS-v2` y `ECAPA-TDNN` sobre el modelo NMT base, antes de incurrir en el coste computacional del entrenamiento masivo de 100 000 pares.

---

## 2. Ficha Técnica de los Entornos de Ejecución

Para la sección de **Entorno Experimental y Plataforma**, se dispone del contraste formal entre el entorno cloud donde se ejecutaron los notebooks adjuntos y el entorno de desarrollo local:

| Componente | Entorno Cloud (Ejecución Notebooks Colab) | Entorno Local de Desarrollo |
| :--- | :--- | :--- |
| **GPU** | NVIDIA Tesla T4 | NVIDIA GeForce RTX 5060 Laptop GPU |
| **Memoria VRAM Total** | 14 912.69 MB (~15 GB) | 8 151.00 MB (~8 GB) |
| **CUDA Runtime / Driver** | CUDA 13.0 | CUDA 13.4 (Driver 615.71.09) |
| **Sistema Operativo** | Linux Ubuntu (Runtime Colab) | Linux x86_64 (Kernel 6.16) |
| **Intérprete Python** | 3.10.12 / 3.11 | 3.11.15 |
| **Framework Deep Learning** | PyTorch 2.11.0+cu130 | PyTorch 2.6.x+cu126 |
| **Hugging Face Transformers**| >= 4.38.0 | 4.49.x / 5.0.0.dev0 |
| **Librerías de Datasets** | datasets >= 3.0.0 | datasets 4.0.0 / pyarrow 18.1.0 |
| **Evaluación de Métricas** | SacreBLEU 2.5.x, Evaluate 0.4.x, JIWER 3.1.x | SacreBLEU 2.5.1, Evaluate 0.4.3, JIWER 3.1.0 |

---

## 3. Preparación del Corpus y Análisis de Longitud

### 3.1 Dimensiones de los Datasets del Proyecto

- **Dataset A: OPUS-100 Español→Inglés (Módulo NMT)**
  - Partición de Entrenamiento (`train`): **100 000 pares** (96.16%)
  - Partición de Validación (`validation`): **1 990 pares** (1.91%)
  - Partición de Prueba (`test`): **1 999 pares** (1.92%)
  - Semilla de partición: `seed = 42` (con aislamiento estricto bilingüe y eliminación de solapamientos).
- **Dataset B: FLEURS `es_419` (Módulo ASR y Speech-to-Speech)**
  - Muestras totales: **20 audios** (formato WAV, 16 000 Hz, monocanal, float32).
  - Partición Dev: **14 audios** (70%)
  - Partición Test: **6 audios** (30%)
  - Duración acumulada: **203.34 segundos** (media: 10.17 s, min: 6.06 s, max: 18.12 s).
  - Identificador de locutor: No provisto en FLEURS (`speaker_id = None`), sin valores inventados.

### 3.2 Decisión de Ingeniería: Resolución y Justificación de `max_length = 128`

En la auditoría inicial se identificó una discrepancia entre el informe teórico (`max_length = 128`) y una configuración residual heredada (`max_length = 512`).  
Se ejecutó un análisis estadístico empírico sobre **10 000 pares de oraciones** de OPUS-100 sin truncamiento mediante el tokenizador SentencePiece oficial de `Helsinki-NLP/opus-mt-es-en`:

```
Estadísticas de Longitud de Tokens (Muestra representativa N = 10 000 pares):

• Español (Texto de entrada / Encoder):
  - Longitud Media: 14.57 tokens (Desviación estándar: 15.11)
  - Mediana (p50): 9.0 tokens
  - Percentil 75 (p75): 18.0 tokens
  - Percentil 90 (p90): 31.1 tokens
  - Percentil 95 (p95): 47.0 tokens
  - Percentil 99 (p99): 76.01 tokens
  - % de oraciones con longitud > 128 tokens: 0.11% (solo 11 de 10 000)
  - % de oraciones con longitud > 256 tokens: 0.02%
  - % de oraciones con longitud > 512 tokens: 0.01%

• Inglés (Texto objetivo / Decoder):
  - Longitud Media: 14.46 tokens (Desviación estándar: 14.15)
  - Mediana (p50): 10.0 tokens
  - Percentil 75 (p75): 18.0 tokens
  - Percentil 90 (p90): 30.0 tokens
  - Percentil 95 (p95): 42.0 tokens
  - Percentil 99 (p99): 71.0 tokens
  - % de oraciones con longitud > 128 tokens: 0.07% (solo 7 de 10 000)
  - % de oraciones con longitud > 256 tokens: 0.02%
  - % de oraciones con longitud > 512 tokens: 0.01%
```

#### Redacción Metodológicamente Correcta para el Informe:
> *"El análisis sobre 10 000 pares demostró que fijar `max_length = 128` cubre el **99.89%** de las secuencias en español y el **99.93%** de las inglesas sin truncamiento. Se seleccionó este límite para acotar la longitud máxima procesable y controlar el coste de memoria y cómputo ante secuencias atípicas excesivamente extensas. Asimismo, dado que el pipeline implementa **padding dinámico por lote** mediante `DataCollatorForSeq2Seq` (manteniendo `padding = False` durante la tokenización previa), cada lote de entrenamiento se ajusta dinámicamente a la longitud efectiva de sus ejemplos, optimizando la ocupación en memoria sin desperdiciar cómputo en relleno artificial."*

---

## 4. Inferencia del Modelo NMT Base (MarianMT ES→EN)

### 4.1 Configuración de la Prueba de Inferencia
- **Modelo Preentrenado:** `Helsinki-NLP/opus-mt-es-en`
- **Algoritmo de Decodificación:** Beam Search con anchura de haz $k = 4$.
- **Límite de Longitud:** 128 tokens.
- **Entorno de Ejecución:** Google Colab sobre GPU NVIDIA Tesla T4.
- **Muestras:** 5 oraciones reales extraídas del split oficial `test` de OPUS-100 mediante streaming con normalización NFKC.

### 4.2 Tabla de Traducciones Reales (Cotejada 1:1 con el Notebook Ejecutado)

La siguiente tabla refleja exactamente los textos procesados y generados en la celda 6 de [notebooks/translation/00_nmt_base_smoke_test.ipynb](file:///home/setrox/Projects/University/IA-Proyecto/notebooks/translation/00_nmt_base_smoke_test.ipynb):

| Muestra ID | Texto Fuente en Español (`SOURCE_ES`) | Traducción de Referencia (`REFERENCE_EN`) | Predicción MarianMT Base (`PREDICTION_BASE`) |
| :---: | :--- | :--- | :--- |
| **0** | *Si su país produjo SAO para estos usos, sírvase anotar en la columna 6 del formulario de datos 3 la cantidad correspondiente”.* | *If your country produced ODS for this purpose, please enter the amount so produced in column 6 on Data Form 3.”* | *If your country has produced ODS for these uses, please enter the corresponding amount in column 6 of data form 3.”* |
| **1** | *# Juvie el gran hombre, ¿quién podría ser sino yo?* | *♪ juvie the great man, who else could it be but I?* | *# Juvie the great man, who could it be but me?* |
| **2** | *El planeta madre se está agotando.* | *The home planet is running out.* | *Mother planet's running low.* |
| **3** | *Las chicas no matan a sus madres? .* | *Oon't girls ever kill their mothers?* | *Girls don't kill their mothers.* |
| **4** | *Actividades humanitarias, de recuperación y de desarrollo* | *Humanitarian, recovery and development activities* | *Humanitarian, recovery and development activities* |

### 4.3 Métricas Cuantitativas y Latencia de la Ejecución Registrada
- **Métricas de Calidad Textual:**
  - **SacreBLEU:** **36.33**
  - **chrF:** **68.82**
- **Latencia de Inferencia Registrada en el Notebook:**
  - **Tiempo total del smoke test NMT:** **2.6195 segundos** para las 5 oraciones.
  - **Latencia promedio por oración:** **523.90 ms / oración** (en la ejecución documentada en GPU Tesla T4).
  - *Nota metodológica para el informe:* Esta cifra corresponde al tiempo medido de ejecución en celda del smoke test; en entornos de producción con lotes de mayor tamaño y modelos en memoria continua, la latencia por oración decrece significativamente.

---

## 5. Smoke Test de Fine-Tuning NMT (MarianMT Adaptado)

### 5.1 Propósito y Rigor Metodológico
El smoke test de fine-tuning tiene como finalidad exclusiva certificar que la infraestructura de entrenamiento opera sin fallos:
1. Verificación del cálculo de gradientes (*forward/backward pass*) y actualización de pesos con **AdamW**.
2. Estabilidad de la precisión mixta automática en punto flotante de 16 bits (**FP16**).
3. Eficacia del suavizado de etiquetas (**label smoothing = 0.1**) para mitigar sobreconfianza probabilística.
4. Consumo de memoria VRAM y descarte de fugas o errores de memoria (*Out of Memory*).
5. Evaluación periódica integrada con generación por haz ($k = 4$) y cálculo de métricas SacreBLEU y chrF.

### 5.2 Hiperparámetros Contrastados: Smoke Test vs. Configuración Propuesta Completa

| Parámetro | Configuración Smoke Test (Ejecutada en Colab) | Configuración Propuesta para Entrenamiento Completo (100k pares) |
| :--- | :---: | :---: |
| **Volumen Train** | 256 pares | 100 000 pares |
| **Volumen Eval** | 64 pares | 1 990 pares |
| **Épocas** | 1.0 época (32 pasos totales) | 3.0 épocas (propuesta planificada) |
| **Tamaño de Lote (Batch Size)** | 8 por dispositivo | 16 o 32 (con acumulación de gradiente) |
| **Tasa de Aprendizaje (LR)** | $5 \times 10^{-5}$ | $5 \times 10^{-5}$ |
| **Planificador de LR** | Warmup lineal (3 pasos, ~10%) | Warmup lineal (~1 000 pasos, ~10%) |
| **Regularización (Weight Decay)**| 0.01 | 0.01 |
| **Label Smoothing** | 0.1 | 0.1 |
| **Precisión Numérica** | FP16 (`fp16 = True`) | FP16 (`fp16 = True`) |
| **Estrategia Decodificación** | Beam Search ($k = 4$) | Beam Search ($k = 4$) |
| **Frecuencia de Evaluación** | Cada 16 pasos | Cada 2 000 pasos / Por época |
| **Semilla Aleatoria** | 42 | 42 |

### 5.3 Resultados Registrados en Ejecución (Google Colab — Tesla T4)
- **Tiempo de entrenamiento (32 pasos):** **15.76 segundos** (en GPU Tesla T4).
- **Consumo Pico de Memoria VRAM:** **1 669.87 MB** (~1.67 GB, ocupando únicamente el 11.2% de la capacidad de la GPU T4).
- **Evolución de la Pérdida de Entrenamiento:**
  - Paso 16: `Training Loss = 2.3742` | `Validation Loss = 2.5618`
  - Paso 32: `Training Loss = 2.1961` | `Validation Loss = 2.5663`
- **Pérdida Media de Entrenamiento del Ciclo:** **2.2612**

### 5.4 Comparación Preliminar durante el Smoke Test (64 Muestras Idénticas)

Ambos modelos fueron evaluados sobre exactamente las mismas 64 muestras de validación con decodificación por haz ($k = 4$):

| Modelo | Pérdida de Validación (`Loss`) | SacreBLEU | chrF |
| :--- | :---: | :---: | :---: |
| **MarianMT Base** (pesos congelados preentrenados) | **2.5514** | **42.33** | **64.80** |
| **MarianMT Debug** (adaptado en smoke test: 256 pares, 1 época) | **2.5663** | **40.93** | **64.33** |
| **Diferencia ($\Delta$)** | $+0.0149$ | $-1.40$ | $-0.47$ |

#### Conclusión Metodológicamente Rigurosa para el Informe:
> *"La ligera diferencia observada ($\Delta = -1.40$ BLEU, $\Delta = -0.47$ chrF) es un comportamiento esperable: un ciclo exploratorio mínimo de 256 muestras no tiene capacidad estadística para desplazar el conocimiento global de un modelo preentrenado sobre millones de oraciones. **El smoke test demostró con éxito que el proceso de fine-tuning es técnica y computacionalmente funcional y estable**, pero no permite ni pretende concluir una mejora del modelo lingüístico frente a la base preentrenada hasta que se aborde el entrenamiento formal sobre el corpus completo de 100 000 pares."*

### 5.5 Origen de los Datos en el Smoke Test y Salvaguarda Arquitectural para el Modo Completo
- En el notebook de Google Colab, al no disponer de los archivos CSV locales en la instancia remota efímera, el smoke test utilizó pares extraídos en streaming oficial de Hugging Face (`Helsinki-NLP/opus-100` con normalización).
- **Salvaguarda Técnica Incorporada:** Para el futuro entrenamiento a escala completa de 100 000 pares, el módulo de datos ([src/translation/data.py](file:///home/setrox/Projects/University/IA-Proyecto/src/translation/data.py)) y el script de entrenamiento ([src/translation/train.py](file:///home/setrox/Projects/University/IA-Proyecto/src/translation/train.py)) han sido configurados con el parámetro `require_local_files = not debug_mode`. De este modo, en modo `--full` el sistema **exige estrictamente la presencia física de `train.csv`, `validation.csv` y `test.csv` del Dataset A preparado por el proyecto**, fallando con un error explícito si no se encuentran y bloqueando cualquier sustitución inadvertida.

---

## 6. Inferencia ASR con Whisper-Small (`openai/whisper-small`)

### 6.1 Configuración de Reconocimiento del Habla
- **Modelo:** `openai/whisper-small` (244 millones de parámetros).
- **Idioma Forzado:** Español (`language = "es"`).
- **Tarea Forzada:** Transcripción pura (`task = "transcribe"`), impidiendo cualquier traducción cruzada implícita dentro de Whisper para preservar la modularidad del pipeline global.
- **Formato de Entrada:** Señales de audio a 16 000 Hz, monocanal, decodificadas con `soundfile` a formato float32.
- **Origen de las Muestras:** Se seleccionaron 3 muestras de FLEURS `es_419` mediante streaming directo del split oficial con selección reproducible utilizando semilla 42 (y no del split dev de 14 audios del Dataset B local).

### 6.2 Tabla de Transcripciones y Métricas (WER / CER)

La siguiente tabla refleja exactamente los resultados registrados en la celda 4 de [notebooks/asr/00_whisper_smoke_test.ipynb](file:///home/setrox/Projects/University/IA-Proyecto/notebooks/asr/00_whisper_smoke_test.ipynb):

| Identificador de Muestra | Duración Audio (s) | Tiempo Inferencia (s) | Transcripción Real (Ground Truth) | Transcripción Generada por Whisper | WER (%) | CER (%) |
| :---: | :---: | :---: | :--- | :--- | :---: | :---: |
| `fleurs_es_419_smoke_00` | 8.88 | 3.597 s *(en frío)* | *Exactamente a las 8:46 a. m., la ciudad se volvió silencio, marcando el preciso instante en el que el primer avión alcanzó su objetivo.* | *Exactamente a las 8.46 a.m. la ciudad se volvió silencio, marcando de preciso instante en el que el primer avión alcanzó su objetivo.* | **16.67%** | **3.70%** |
| `fleurs_es_419_smoke_01` | 8.94 | 0.566 s *(en caliente)* | *Por lo general, las hembras se relacionan estrechamente entre sí, lo que las hace una gran familia de hermanas e hijas.* | *Por lo general, las hembras se relacionan estrechamente entre sí, lo que las hace una gran familia de hermanas e hijas.* | **0.00%** | **0.00%** |
| `fleurs_es_419_smoke_02` | 8.64 | 0.668 s *(en caliente)* | *Recuerde incluir los gastos adicionales, los impuestos de partida, el transporte terrestre, etc. para todos los lugares que visite fuera de África.* | *Recuerda incluir los gastos adicionales, los impuestos de partida, el transporte terrestre, etcétera para todos los lugares que visite fuera de África.* | **9.09%** | **4.08%** |

### 6.3 Métricas Globales y Conclusión Defendible
- **Métricas Registradas:**
  - **WER promedio (Word Error Rate):** **8.59%**
  - **CER promedio (Character Error Rate):** **2.59%**
- **Desglose de Tiempos y Factor de Tiempo Real (RTF):**
  - Primera ejecución (en frío, incluyendo carga de buffers y compilación en GPU): **3.597 s**.
  - Ejecuciones subsecuentes (en caliente): **0.566 s** y **0.668 s** para audios de ~8.8 segundos.
  - **Tiempo promedio global registrado:** **1.61 s**.
  - **Factor de Tiempo Real (RTF) aproximado en inferencias calientes:**
    $$\text{RTF}_{\text{caliente}} = \frac{0.566 + 0.668}{2 \times 8.8} = \frac{0.617}{8.8} \approx \mathbf{0.070}$$
    (lo que representa una velocidad de procesamiento unas 14 veces más rápida que el tiempo real de reproducción del habla).
- **Conclusión Académica para el Informe:**
  > *"Los resultados del smoke test muestran que Whisper-small transcribe de forma correcta y precisa las muestras seleccionadas, permitiendo validar técnicamente el funcionamiento del módulo ASR en GPU. Debido al reducido número de ejemplos evaluados ($N = 3$), estos valores constituyen una verificación técnica de operatividad y no deben interpretarse como una evaluación general del modelo."*
- **Recomendación Metodológica para la Evaluación Final:**
  El cálculo actual emplea un **WER ortográfico crudo directo** (`jiwer.wer(ground_truth, prediction)`), penalizando variaciones tipográficas menores como `8:46 a. m.` vs `8.46 a.m.` o la expansión de abreviaturas (`etc.` vs `etcétera`). Para la evaluación formal del sistema sobre el conjunto completo de prueba se recomienda reportar dos variantes:
  1. **WER ortográfico:** mide la concordancia exacta incluyendo signos y convenciones.
  2. **WER normalizado:** evalúa la fidelidad léxico-acústica aislando puntuación, mayúsculas y abreviaturas.

---

## 7. Tabla Síntesis de Estado del Proyecto (Checklist para el Informe)

| Componente / Hito | Estado Demostrado | Evidencia en Repositorio | Observación Metodológica |
| :--- | :---: | :--- | :--- |
| **Dataset A (OPUS-100)** | ✅ **Completado y Auditado** | [data/processed/translation/](file:///home/setrox/Projects/University/IA-Proyecto/data/processed/translation/) | 100k train, 1990 val, 1999 test. Aislamiento estricto comprobado. |
| **Dataset B (FLEURS)** | ✅ **Completado y Auditado** | [data/raw/audio/](file:///home/setrox/Projects/University/IA-Proyecto/data/raw/audio/) | 20 audios a 16 kHz mono (203.34 s totales). Manifiestos listos. |
| **Análisis `max_length = 128`** | ✅ **Completado y Justificado** | [outputs/metrics/token_length_analysis.json](file:///home/setrox/Projects/University/IA-Proyecto/outputs/metrics/token_length_analysis.json) | Justificado empíricamente con 10k pares (>99.89% de cobertura). |
| **NMT Base Inferencia** | ✅ **Completado y Registrado** | [notebooks/translation/00_nmt_base_smoke_test.ipynb](file:///home/setrox/Projects/University/IA-Proyecto/notebooks/translation/00_nmt_base_smoke_test.ipynb) | SacreBLEU: 36.33, chrF: 68.82 en split test oficial. |
| **Fine-Tuning Smoke Test** | ✅ **Completado y Registrado** | [notebooks/translation/01_nmt_finetuning_smoke_test.ipynb](file:///home/setrox/Projects/University/IA-Proyecto/notebooks/translation/01_nmt_finetuning_smoke_test.ipynb) | 15.76 s en Tesla T4, VRAM pico 1 669.87 MB. Proceso validado. |
| **ASR (Whisper-Small)** | ✅ **Completado y Registrado** | [notebooks/asr/00_whisper_smoke_test.ipynb](file:///home/setrox/Projects/University/IA-Proyecto/notebooks/asr/00_whisper_smoke_test.ipynb) | WER: 8.59%, CER: 2.59%, RTF caliente $\approx 0.07$. Modo transcripción. |
| **Pruebas Unitarias** | ✅ **100% Aprobadas (8/8)** | [tests/unit/test_translation.py](file:///home/setrox/Projects/University/IA-Proyecto/tests/unit/test_translation.py) | `pytest tests/unit/` pasa en 3.92 s sin errores. |
| **Entrenamiento Completo 100k**| ❌ **No Ejecutado (Planificado)**| [src/translation/train.py](file:///home/setrox/Projects/University/IA-Proyecto/src/translation/train.py) | Requiere datasets locales obligatorios; pospuesto conscientemente. |
| **XTTS-v2 (Clonación de Voz)** | ❌ **No Ejecutado (Siguiente fase)** | Planificado en arquitectura | Pospuesto para la segunda iteración modular. |
| **ECAPA-TDNN (Similitud Vocal)**| ❌ **No Ejecutado (Siguiente fase)** | Planificado en arquitectura | Pospuesto para la segunda iteración modular. |
| **Pipeline Speech-to-Speech** | ❌ **No Ejecutado (Siguiente fase)** | Planificado en arquitectura | Se integrará primero con MarianMT base. |

---

## 8. Estrategia Consensuada para la Siguiente Iteración

Antes de incurrir en el gasto computacional y temporal de entrenar el modelo NMT sobre los 100 000 pares, la metodología del proyecto abordará la **Segunda Iteración Modular**:

```
Audio Español
      │
      ▼
[Whisper-small (ASR)]  ✅ Validado en Smoke Test
      │
      ▼ Texto Español
[MarianMT Base (NMT)]  ✅ Validado en Smoke Test
      │
      ▼ Texto Inglés
[XTTS-v2 (TTS + Voice Cloning)]  ⏳ Siguiente paso a implementar
      │
      ▼ Audio Inglés con Voz Clonada
[ECAPA-TDNN (Evaluación de Similitud Vocal)]  ⏳ Siguiente paso a implementar
```

**Justificación Estratégica:**  
Validar en primer término la arquitectura completa Speech-to-Speech con el modelo de traducción base permite comprobar la interoperabilidad acústica y el flujo extremo a extremo antes de dedicar recursos masivos al fine-tuning. Una vez corroborado el funcionamiento integral del sistema, se abordará el entrenamiento completo de 100 000 pares en NMT para sustituir el modelo base y medir el salto cuantitativo final.

---

## 9. Texto Modelo Sugerido para Conclusiones del Capítulo 4

La IA redactora puede adaptar el siguiente texto para cerrar la sección de resultados técnicos:

> *"Los ensayos experimentales y pruebas de verificación técnica confirman la estabilidad y viabilidad de los módulos centrales de procesamiento de voz y texto. En primer lugar, el estudio de distribución de longitudes de tokens sobre 10 000 pares de OPUS-100 permitió fundamentar técnicamente la selección de una longitud máxima de 128 tokens, la cual retiene más del 99.89% de los enunciados del español sin truncamiento, reduciendo de manera sustancial la demanda máxima en memoria mientras el mecanismo de padding dinámico ajusta cada lote a su longitud efectiva. En segundo lugar, el modelo base MarianMT demostró una sólida capacidad de traducción en inferencia sobre muestras del conjunto de prueba oficial (SacreBLEU: 36.33, chrF: 68.82), sirviendo como referencia sólida para el pipeline. La ejecución del ciclo de fine-tuning debug ratificó la estabilidad computacional del grafo de aprendizaje bajo el optimizador AdamW y precisión mixta FP16, manteniendo una demanda contenida de memoria de video (1 669.87 MB en GPU Tesla T4) y garantizando la ausencia de desbordamientos de memoria de cara al futuro entrenamiento completo. Finalmente, el módulo Whisper-small operando en modo de transcripción forzada en español alcanzó un error de palabra promedio del 8.59% sobre muestras reales de FLEURS, con una velocidad de inferencia en régimen caliente 14 veces superior al tiempo real ($\text{RTF} \approx 0.07$). Estos hallazgos validan técnicamente los componentes de entrada y procesamiento textual, permitiendo avanzar de forma segura hacia la siguiente iteración modular orientada a la síntesis con clonación vocal mediante XTTS-v2 y su evaluación objetiva con ECAPA-TDNN."*

---

## 10. Preparación de la iteración XTTS/ECAPA para Google Colab

Se añadieron implementaciones y notebooks de Colab para XTTS-v2, ECAPA, pipeline end-to-end y Gradio. El runtime aislado de referencia utiliza Python 3.11.15, torch/torchaudio 2.8.0+cu128, coqui-tts 0.27.5, transformers 4.57.3, speechbrain 1.1.1 y numpy 2.4.6. La combinación se comprobó hasta importación local en GPU; `transformers 5.19.0` no es compatible con XTTS por ausencia de `isin_mps_friendly`.

No se añaden números de XTTS, ECAPA, RTF total o MOS porque aún no se ejecutó el notebook en Colab. La evidencia del pipeline real deberá generarse con los tres DEV y guardarse en `outputs/smoke_tests/xtts/`, `voice_similarity.json` y `outputs/smoke_tests/pipeline/<sample_id>/`.

### Actualización de evidencia local RTX 5060

La ejecución posterior generó tres salidas XTTS a 24000 Hz y calculó ECAPA: 0.599170, 0.396744 y 0.555145 (media 0.517020). El pipeline real produjo RTF 3.9355 en frío y 0.1937/0.2064 en caliente. Estas cifras son smoke test N=3; no constituyen resultado general ni porcentaje de conservación vocal. MOS continúa pendiente y no se han inventado evaluadores.
