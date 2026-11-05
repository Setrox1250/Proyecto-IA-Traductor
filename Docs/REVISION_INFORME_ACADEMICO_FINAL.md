# Revisión del informe académico final — capítulos I a VI

**Documento revisado:** `Traducción de Mensajes de Audio con Clonación de Voz mediante Inteligencia Artificial hasta punto vi (1).docx` (documento externo, no incluido en el repositorio por ruta privada).
**SHA-256 del documento:** `12c3b4c8c357c6f42e268e204af17a35e1b0840bb16815d39dcc9ed24dfa840b`
**Tamaño:** 362 958 bytes.
**Páginas del PDF convertido:** 44.
**Párrafos extraídos:** 699.
**Referencia de comparación:** ejecución final `outputs/final_eval/master_20261104_082658/` (commit de ejecución registrado: `e2df599`, historial anterior a la limpieza).
**Fecha de revisión:** 2026-11-04.

> Las páginas citadas corresponden al PDF generado con LibreOffice a partir del `.docx`. La paginación en Word puede variar ligeramente. Se cita también el número de sección para evitar ambigüedad.

---

## 1. Resumen ejecutivo

El documento entregado **ya incluye los capítulos I a VI** y representa una mejora sustancial frente a la versión anterior del documento académico, que solo contenía I y II. En particular:

- Incluye el experimento controlado de 10 000 pares en el Capítulo V.
- Presenta correctamente la comparación base vs checkpoint en OPUS-100:
  - Base: BLEU 43,4140; chrF 64,4179; eval loss 1,3532.
  - Checkpoint 10k: BLEU 42,6499; chrF 63,6674; eval loss 1,4047.
- Reconoce que el checkpoint no mejoró al base.
- Reconoce que el pipeline usa MarianMT base.
- Reconoce la ausencia de MOS.
- Reconoce que el sistema no es de tiempo real.
- Reconoce que la clonación es aproximada.
- Incluye Gradio y limitaciones.

Sin embargo, **todavía no está listo para presentarse como evaluación final**. El problema principal es que la evaluación de Dataset B sigue usando la reserva histórica v1:

- 20 audios, 14 dev / 6 test.
- 203,34 s.
- Seis muestras de prueba.
- Métricas antiguas: WER 20,52 %, BLEU 31,5131, BLEU pipeline 29,4115, ECAPA 0,3996, RTF 0,3535.

La ejecución final del repositorio usa otra reserva:

- 20 muestras del split oficial `test` de FLEURS `es_419`.
- 0 dev / 20 test.
- 228,12 s.
- 0 exclusiones.
- Métricas finales: WER 11,73 %, WER normalizado 6,13 %, CER 2,52 %, BLEU aislado 23,94, BLEU pipeline 20,27, ECAPA 0,4502, RTF hot 0,1776.

Además, el documento contiene una contradicción interna:

- La sección 4.2.4 (p. 30) dice que el **único** entrenamiento ejecutado fue el smoke test de 256 pares.
- La sección 5.1.1 (pp. 34–35) y la sección 6.1.2 (p. 39) describen correctamente el experimento de 10 000 pares.

También hay desactualizaciones puntuales:

- Dice “12 pruebas unitarias y 1 de integración” (p. 28); la suite actual tiene **15 unitarias + 2 de integración = 17**.
- La Tabla 5 (p. 24) dice que el NMT se ajusta con **100 000 pares**; el ajuste ejecutado usó **10 000**.
- El texto dice que el entrenamiento de 100 000 pares “no se ejecutó y no se sabe si mejoraría” (p. 41); debe decir también que **no está implementado** y que está fuera del alcance.
- La Tabla 14 (p. 37) usa muestras v1 y el audio silencioso `0008`; la muestra final `test_0008` es otra y no es silenciosa.

**Veredicto:** el documento tiene una base académica sólida y una estructura correcta, pero **requiere una corrección obligatoria de Dataset B, métricas finales, número de pruebas y contradicción 256/10k antes de la revisión final**.

---

## 2. Fortalezas que deben conservarse

1. **Estructura completa I–VI.** El documento ya tiene introducción, requerimientos, dataset, aprendizaje, comprobación y evaluación.
2. **Descripción de la arquitectura modular.** Whisper → MarianMT → XTTS-v2 → ECAPA está bien explicada.
3. **Justificación de `max_length=128`.** Usa el análisis de 10 000 pares y los percentiles 99 (76 ES / 71 EN).
4. **Reconocimiento del resultado negativo del fine-tuning.** No oculta que el checkpoint 10k quedó por debajo del base.
5. **Selección del modelo base.** Está justificada en el texto y coincide con `configs/translation.yaml`.
6. **Advertencia sobre clonación aproximada.** No afirma identidad perfecta ni conservación de emoción/prosodia.
7. **Reconocimiento de MOS pendiente.** No inventa evaluación perceptual.
8. **Reconocimiento de no streaming.** El alcance está bien delimitado.
9. **Inclusión de Gradio.** Ya no se presenta solo como “construido”; se indica que fue probado localmente.
10. **Limitaciones explícitas.** La sección 6.2.3 es honesta y útil.
11. **Valores del smoke 256 verificados.** `duration_seconds=10.82`, `peak_vram_mb=1716.62`, `train_loss=2.2569`, `eval_loss=2.5663`, `eval_bleu=41.63`, `eval_chrf=64.74` corresponden a la ejecución local del smoke test de 256 pares; el artefacto se retiró del repositorio durante la limpieza.
12. **Valores del experimento 10k verificados.** La Tabla 12 y la sección 6.1.2 coinciden con `Docs/NMT_CONTROLLED_EXPERIMENT_10K.json`.

---

## 3. Problemas críticos que bloquean la versión final

### P0-1. Dataset B sigue siendo la reserva histórica v1

**Páginas:** 17–18, 28–29, 34–36, 39–41.
**Texto actual:** “20 grabaciones”, “203,34 segundos”, “14 dev / 6 test”, “seis grabaciones de prueba”.
**Problema:** la evaluación final no usa esa reserva. La reserva v1 se construyó sobre `source_split=train`, no sobre el split oficial `test`, y además contiene audios silenciosos.
**Evidencia del repositorio:**

- `data/processed/manifests/fleurs_evaluation_v2_official_test.csv`
- `outputs/final_eval/master_20261104_082658/datasetB/dataset_summary.json`
- `outputs/final_eval/master_20261104_082658/datasetB/aggregate_metrics.json`

**Corrección obligatoria:**

- Cambiar “20 grabaciones, 14 dev / 6 test, 203,34 s” por “20 muestras del split oficial `test`, 228,12 s, 16 kHz mono, 0 dev / 20 test”.
- Cambiar “seis grabaciones de prueba” por “20 muestras de prueba”.
- Sustituir la Tabla 13 completa.
- Sustituir las métricas de las secciones 6.1.3, 6.2.1 y 6.2.2.
- Sustituir los ejemplos de la Tabla 14.
- Añadir una nota: la reserva v1 se conserva como evidencia histórica, no como evaluación final.

### P0-2. Contradicción 256 vs 10 000 pares

**Páginas:** 29–31 frente a 34–35 y 39.
**Texto actual:**

- Sección 4.2.4, p. 30: “El único proceso de aprendizaje ejecutado hasta esta entrega corresponde al smoke test de fine-tuning de MarianMT. Se entrenaron 256 pares…”.
- Sección 5.1.1, p. 34: “se ejecutó un experimento de entrenamiento controlado sobre 10 000 pares…”.
- Sección 6.1.2, p. 39: tabla del experimento de 10 000 pares.

**Problema:** el documento se contradice. El smoke de 256 es una prueba técnica; el experimento principal es el de 10 000.

**Corrección obligatoria:**

- Reescribir 4.2.3/4.2.4/4.2.5 para distinguir:
  1. Smoke test de 256/64/1: valida el flujo.
  2. Experimento controlado de 10 000/1 000/1: experimento principal.
  3. Entrenamiento 100k: no implementado y no ejecutado.
- Añadir el experimento 10k a la Tabla 7 o separar en dos tablas.
- No decir “único proceso de aprendizaje” sin aclarar que el 10k se documenta en el Capítulo V.

### P0-3. Tabla 5 dice fine-tuning con 100 000 pares

**Página:** 24.
**Texto actual:** en la Tabla 5, NMT: “Supervisado: fine-tuning con 100 000 pares”.
**Problema:** el ajuste ejecutado usó 10 000 pares; 100 000 es el dataset disponible, no el usado.
**Corrección:** cambiar a “Supervisado: fine-tuning con 10 000 pares (experimento controlado)” y añadir una nota de que el corpus disponible era 100 000.

### P0-4. Tabla 13 y métricas de Dataset B son de v1

**Páginas:** 36, 39–41.
**Texto actual (Tabla 13):**

- WER ortográfico 20,52 %.
- WER normalizado 18,18 %.
- CER 17,62 %.
- SacreBLEU aislado 31,5131.
- chrF aislado 57,3362.
- SacreBLEU pipeline 29,4115.
- chrF pipeline 47,2016.
- ECAPA media 0,3996.
- ECAPA mediana 0,4965.
- ECAPA mínimo/máximo 0,1332/0,5047.
- Tiempo total medio 9,235 s.
- RTF hot 0,3535.
- N=6.

**Problema:** estas cifras provienen de la reserva v1 y del audio silencioso `0008`. No son la evaluación final.

**Corrección:** reemplazar por la Tabla 13 del repositorio:

| Métrica | Resultado final (N=20) |
|---|---:|
| WER ortográfico medio | 11,7339 % |
| WER normalizado medio | 6,1313 % |
| CER medio | 2,5203 % |
| SacreBLEU NMT aislado | 23,9378 |
| chrF NMT aislado | 55,6260 |
| SacreBLEU pipeline | 20,2742 |
| chrF pipeline | 54,1448 |
| ECAPA media | 0,4502 |
| ECAPA mediana | 0,4452 |
| ECAPA mínimo / máximo | 0,2818 / 0,6214 |
| Tiempo total medio | 3,1838 s |
| RTF hot medio | 0,1776 |

Fuente: `outputs/final_eval/master_20261104_082658/datasetB/aggregate_metrics.json`.

### P0-5. Tabla 14 usa audios v1 y el `0008` silencioso

**Página:** 37.
**Texto actual:** ejemplos `fleurs_es_419_0002` y `fleurs_es_419_0008`; el segundo produjo `"y"`/`"and"`.
**Problema:** la Tabla 14 pertenece a la reserva v1. El `0008` v1 era silencioso. La muestra final `fleurs_es_419_test_0008` es otra (sentence_id 1783) y es válida.
**Corrección:**

- Reemplazar por ejemplos del run final, por ejemplo `fleurs_es_419_test_0000`, `0001`, `0005`, etc.
- O conservar la Tabla 14 como “caso histórico v1” con una nota explícita y no usarla como evidencia final.
- No mezclar identificadores v1 con identificadores v2.

### P0-6. Número de pruebas desactualizado

**Página:** 28.
**Texto actual:** “12 pruebas unitarias y 1 prueba de integración aprobadas”.
**Problema:** la suite actual tiene **15 unitarias + 2 de integración = 17**.
**Corrección:** “15 pruebas unitarias y 2 de integración; 17 aprobadas, 0 fallidas, 0 omitidas”.

### P0-7. “100 000 pares no se ejecutó” sin decir “no implementado”

**Páginas:** 28, 41.
**Texto actual:** “El entrenamiento completo… permanece pendiente”; “no se ejecutó y no se sabe si mejoraría”.
**Problema:** es cierto que no se ejecutó, pero además la ruta `--full` de `src/translation/train.py` lanza `NotImplementedError`. No es solo “pendiente”: **no está implementado**.
**Corrección:** “El entrenamiento de 100 000 pares no está implementado y no se ejecutó; está fuera del alcance de esta entrega. No se afirma que mejoraría o empeoraría.”

### P0-8. Evaluación final mezcla smoke tests con resultados finales

**Páginas:** 29–33 y 39–41.
**Problema:** se presentan resultados de tres muestras `validation` (smoke) y de seis muestras v1 como si fueran la comprobación final. La entrega final tiene 20 muestras oficiales `test`.
**Corrección:**

- Mantener los N=3 como “smoke test histórico” claramente etiquetado.
- Añadir la evaluación final N=20.
- En 6.1.3/6.2 usar N=20, no N=6.
- En 6.2.3 cambiar “20 grabaciones, 6 de prueba” por “20 muestras de prueba”.

---

## 4. Revisión capítulo por capítulo

### 4.1 Capítulo I — Introducción

| Página | Afirmación | Estado | Comentario |
|---|---|---|---|
| 4–7 | Título, antecedentes, problema, objetivos | `VERIFICADO` | Coherente con el proyecto |
| 7 | Objetivo específico: adaptar NMT y evaluar frente al base | `PARCIAL` | Se cumplió con 10k; aclarar que el base fue seleccionado |
| 7 | “El módulo de traducción será adaptado mediante fine-tuning” | `VERIFICADO` | Se ejecutó el experimento 10k |
| 7 | Clonación aproximada, no copia exacta | `VERIFICADO` | Correcto |

**Acción:** conservar; ajustar el objetivo específico para que no sugiera que el modelo ajustado es el usado en producción.

### 4.2 Capítulo II — Requerimientos

| Página | Afirmación | Estado | Comentario |
|---|---|---|---|
| 8–10 | Dominio, alcance, no streaming, un solo hablante | `VERIFICADO` | Correcto |
| 9 | “Google Colab con GPU” | `PARCIAL` | La corrida final fue local RTX 5060; no hay evidencia Colab final |
| 9 | “FFmpeg para decodificación/extracción” | `NO VERIFICADO` | El pipeline usa soundfile/librosa/scipy; no se verificó FFmpeg |
| 9 | “Video opcional” | `NO IMPLEMENTADO` | No hay extractor de video |
| 9 | “Audios con autorización” | `VERIFICADO CON MATIZ` | FLEURS es público; revisar licencia |
| 10 | “Interfaz compatible con Google Colab” | `PARCIAL` | Gradio local verificado; Colab no |
| 10 | “El modelo ajustado será el usado” | `DESACTUALIZADO` | El pipeline usa base |

**Acción:** conservar requisitos; aclarar estado real de Colab, video y modelo seleccionado.

### 4.3 Capítulo III — Dataset

| Página | Afirmación | Estado | Comentario |
|---|---|---|---|
| 16 | OPUS-100 100k/1990/1999, semilla 42 | `VERIFICADO` | Dataset disponible; no todo usado |
| 17 | FLEURS 20 audios, 203,34 s, 14/6 | `INCORRECTO` | Usa v1 train; reemplazar por v2 test |
| 18 | Tabla 2: 20 grabaciones / 203,34 s, 14/6 | `INCORRECTO` | Reemplazar |
| 28–29 | 20 audios, 14/6, 203,34 s, 3 validation | `INCORRECTO` | Reemplazar por 20 test, 228,12 s |
| 29 | Tres muestras validation para smoke | `HISTÓRICO` | Puede conservarse como smoke, no como final |

**Acción:** reescribir Dataset B y Tabla 2; añadir la reserva v1 como histórica.

### 4.4 Capítulo IV — Aprendizaje

| Página | Afirmación | Estado | Comentario |
|---|---|---|---|
| 24 | Tabla 5: NMT fine-tuning con 100 000 pares | `INCORRECTO` | Fue 10 000 |
| 29 | Tabla 7: smoke 256 / full 100k | `PARCIAL` | Falta el experimento 10k |
| 30 | “Único proceso de aprendizaje: 256” | `INCORRECTO` | Contradice 10k |
| 30–31 | Comparación base vs debug 256 | `HISTÓRICO` | Correcto como smoke, no como principal |
| 33 | Gradio construido/probado localmente | `VERIFICADO` | Correcto; se puede reforzar con el run final |
| 33 | N=3 ECAPA | `HISTÓRICO` | Correcto como smoke; no final |
| 28 | 12 unitarias + 1 integración | `DESACTUALIZADO` | Son 17 |

**Acción:** añadir 10k como experimento principal; mantener 256 como smoke; corregir Tabla 5 y tests.

### 4.5 Capítulo V — Comprobación

| Página | Afirmación | Estado | Comentario |
|---|---|---|---|
| 34 | 10k/1k/1, hyperparameters | `VERIFICADO` | Correcto |
| 35 | Tabla 12 base vs checkpoint | `VERIFICADO` | Correcto |
| 35–36 | Dataset B seis test, Tabla 13 | `INCORRECTO` | Usa v1; reemplazar por 20 test |
| 36 | WER/BLEU/ECAPA/RTF antiguos | `INCORRECTO` | Reemplazar |
| 37 | Tabla 14 con `0002`/`0008` | `INCORRECTO` | Usa v1 y audio silencioso |

**Acción:** conservar 5.1.1; reescribir 5.1.2 y Tablas 13–14.

### 4.6 Capítulo VI — Evaluación

| Página | Afirmación | Estado | Comentario |
|---|---|---|---|
| 39 | 6.1.2 10k table | `VERIFICADO` | Correcto |
| 39–40 | 6.1.3 N=6, WER 20,52/18,18/17,62, ECAPA 0,3996 | `INCORRECTO` | Usar N=20 y métricas finales |
| 40 | 6.2.1 BLEU 31,5131/29,4115; caída 2,10/10,13 | `INCORRECTO` | Usar 23,9378/20,2742; caída 3,6635/1,4812 |
| 41 | 6.2.2 9,235 s, RTF 0,3535 | `INCORRECTO` | Usar 3,1838 s, RTF 0,1776 |
| 41 | 6.2.3 “20 grabaciones, 6 de prueba” | `INCORRECTO` | Usar 20 test |
| 41 | 100k “no se ejecutó y no se sabe” | `PARCIAL` | Añadir “no implementado” |
| 41 | MOS pendiente | `VERIFICADO` | Correcto |
| 41 | ECAPA no es porcentaje | `VERIFICADO` | Correcto |

**Acción:** reemplazar todas las métricas de 6.1.3–6.2.2 con el run final; actualizar limitaciones.

---

## 5. Tabla de reemplazo de métricas

| Indicador | Documento actual (v1/N=6) | Valor final correcto (N=20) | Fuente |
|---|---:|---:|---|
| WER ortográfico medio | 20,52 % | **11,7339 %** | `aggregate_metrics.json` |
| WER normalizado medio | 18,18 % | **6,1313 %** | `aggregate_metrics.json` |
| CER medio | 17,62 % | **2,5203 %** | `aggregate_metrics.json` |
| SacreBLEU NMT aislado | 31,5131 | **23,9378** | `aggregate_metrics.json` |
| chrF NMT aislado | 57,3362 | **55,6260** | `aggregate_metrics.json` |
| SacreBLEU pipeline | 29,4115 | **20,2742** | `aggregate_metrics.json` |
| chrF pipeline | 47,2016 | **54,1448** | `aggregate_metrics.json` |
| ECAPA media | 0,3996 | **0,4502** | `aggregate_metrics.json` |
| ECAPA mediana | 0,4965 | **0,4452** | `aggregate_metrics.json` |
| ECAPA mínimo / máximo | 0,1332 / 0,5047 | **0,2818 / 0,6214** | `aggregate_metrics.json` |
| Tiempo total medio | 9,235 s | **3,1838 s** | `aggregate_metrics.json` |
| RTF hot medio | 0,3535 | **0,1776** | `aggregate_metrics.json` |
| N | 6 | **20** | `dataset_summary.json` |

> **No comparar directamente** las métricas v1/N=6 con las finales/N=20. La reserva, el conjunto y la dificultad cambiaron. La diferencia no debe presentarse como “mejora” o “degradación” sin un análisis pareado.

### 5.1 Caída aislado → pipeline

Documento actual: “2,10 puntos de SacreBLEU y 10,13 de chrF”.
Valor final:

- BLEU: 23,9378 − 20,2742 = **3,6635 puntos**.
- chrF: 55,6260 − 54,1448 = **1,4812 puntos**.

Corregir la frase de 6.2.1.

### 5.2 Tiempos

Documento actual: 9,235 s, RTF 0,3535.
Valor final:

- Tiempo total medio: **3,1838 s**.
- RTF hot: **0,1776**.
- Frío: 25,4282 s, RTF 1,9804.
- Caliente: 2,0130 s de media, 19 muestras.

Corregir 6.2.2 y la tabla si se añade.

---

## 6. Texto sugerido para las secciones que deben reemplazarse

### 6.1 Dataset B — reemplazo para 3.2 y 4.2.2

> “El Dataset B final está formado por 20 muestras del split oficial `test` de FLEURS `es_419`, reservadas antes de la evaluación. La duración acumulada es de 228,12 s (mínima 5,64 s; media 11,406 s; máxima 21,36 s). Todos los archivos son WAV mono de 16 kHz. No se realizó división artificial dev/test: las 20 muestras constituyen el conjunto de prueba. La reserva histórica v1, construida sobre el split `train` y dividida en 14 dev / 6 test, se conserva únicamente como evidencia del error corregido y no se usa en los resultados finales. La reserva final no tuvo exclusiones.”

### 6.2 Entrenamiento — reemplazo para 4.2.3/4.2.4

> “Se ejecutaron dos experiencias distintas. Primero, un smoke test de 256 pares de entrenamiento, 64 de validación y una época para verificar el flujo de tokenización, cálculo de pérdida, retropropagación, AdamW, FP16 y generación. Segundo, el experimento principal de 10 000 pares de entrenamiento, 1 000 de validación y una época, cuyos resultados se presentan en el Capítulo V. El entrenamiento de 100 000 pares no está implementado y no se ejecutó; el script `--full` lanza `NotImplementedError` y el módulo controlado limita explícitamente a 10 000 pares.”

### 6.3 Tabla 5 — reemplazo de la fila NMT

> “Supervisado: fine-tuning con 10 000 pares (experimento controlado); el corpus disponible era de 100 000 pares.”

### 6.4 Tabla 13 — reemplazo

Usar la tabla de la sección 5 de este documento.

### 6.5 6.1.3 — reemplazo

> “Sobre las 20 muestras del split oficial `test`, Whisper-small obtuvo un WER ortográfico medio de 11,73 %, un WER normalizado de 6,13 % y un CER de 2,52 %. La similitud ECAPA media entre la voz original y la sintetizada fue 0,4502 (mediana 0,4452; desviación estándar 0,0767; mínimo 0,2818; máximo 0,6214). Estos valores son cercanía en el espacio de embeddings, no porcentaje de identidad vocal.”

### 6.6 6.2.1 — reemplazo

> “Al traducir la transcripción de referencia, el módulo de traducción alcanzó 23,9378 SacreBLEU y 55,6260 chrF. Al recibir la salida de Whisper, esos valores fueron 20,2742 y 54,1448. La caída de 3,6635 puntos de SacreBLEU y 1,4812 de chrF es consistente con la propagación de errores del ASR.”

### 6.7 6.2.2 — reemplazo

> “El tiempo total medio fue de 3,1838 s por muestra. El RTF medio en régimen caliente fue 0,1776; la primera muestra incluyó carga de modelos y tuvo 25,4282 s (RTF 1,9804). En caliente, el tiempo medio fue 2,0130 s para 19 muestras.”

### 6.8 6.2.3 — reemplazo de limitaciones

> “El conjunto final tiene 20 muestras de prueba. La separación no tiene dev/test porque todas son test oficial. FLEURS no proporciona `speaker_id`, por lo que no se puede garantizar independencia de hablantes. El entrenamiento de 100 000 pares no está implementado y no se ejecutó; no se afirma que mejoraría. MOS no se realizó. No se dispone de valores de referencia de ECAPA para interpretar la escala.”

### 6.9 Tabla 14 — reemplazo

Usar ejemplos del run final:

- `fleurs_es_419_test_0000`: “clima del extremo” vs “clima extremo”; la traducción usa la versión de Whisper.
- `fleurs_es_419_test_0001`: “pueden poderar” vs “puede empoderar”; la traducción omite la cita.
- `fleurs_es_419_test_0005`: “aproximar sus sacapuntas” vs “aproximarse a un sacapuntas”.
- `fleurs_es_419_test_0017`: “vidas silvestres” vs “vida silvestre”.

No usar `fleurs_es_419_0008` (v1) ni el audio silencioso.

---

## 7. Índice de páginas que deben corregirse

| Página | Sección | Problema | Prioridad |
|---:|---|---|---|
| 17–18 | 3.2 / Tabla 2 | FLEURS v1, 203,34 s, 14/6 | P0 |
| 24 | Tabla 5 | NMT con 100 000 pares | P0 |
| 28 | 4.2.1 | 12+1 pruebas | P1 |
| 28–29 | 4.2.2 | 20 audios, 14/6, 203,34, 3 validation | P0 |
| 29 | Tabla 7 | Falta 10k; solo 256/100k | P0 |
| 30 | 4.2.4 | “Único entrenamiento: 256” | P0 |
| 30–31 | 4.2.5 / Tabla 8 | 256 smoke como comparación principal | P1 |
| 33 | 4.2.7 | N=3 ECAPA/Gradio | P1 |
| 34–35 | 5.1.1 / Tablas 11–12 | 10k (correcto) | Conservar |
| 35–36 | 5.1.2 / Tabla 13 | Seis test y métricas v1 | P0 |
| 37 | Tabla 14 | Ejemplos v1/0008 silencioso | P0 |
| 39 | 6.1.2 | 10k (correcto) | Conservar |
| 39–40 | 6.1.3 | N=6 y métricas v1 | P0 |
| 40 | 6.2.1 | BLEU/chrF v1 | P0 |
| 41 | 6.2.2 | 9,235 s / RTF 0,3535 | P0 |
| 41 | 6.2.3 | “20 grabaciones, 6 de prueba” / 100k | P0/P1 |

---

## 8. Checklist de revisión antes de entregar

- [ ] Reemplazar todas las apariciones de “14 dev / 6 test” por “20 test oficial”.
- [ ] Reemplazar “203,34 s” por “228,12 s”.
- [ ] Reemplazar “6 muestras / seis grabaciones” por “20 muestras”.
- [ ] Reemplazar Tabla 13 completa.
- [ ] Reemplazar Tabla 14 y eliminar el `0008` v1.
- [ ] Corregir 6.1.3, 6.2.1, 6.2.2, 6.2.3.
- [ ] Corregir Tabla 5 (“100 000” → “10 000”).
- [ ] Corregir Tabla 7 (añadir 10k).
- [ ] Corregir 4.2.4 (“único” 256).
- [ ] Corregir 4.2.1 (17 pruebas).
- [ ] Añadir “100k no implementado” donde corresponda.
- [ ] Aclarar que el modelo final es base.
- [ ] Aclarar que Gradio fue local, no despliegue público.
- [ ] Aclarar que la corrida final fue local RTX 5060, no Colab.
- [ ] Añadir la reserva v1 como histórica, no final.
- [ ] Revisar que ninguna tabla mezcle N=3, N=6 y N=20.
- [ ] Revisar que ninguna cifra final use el prefijo v1 (`fleurs_es_419_0008`).
- [ ] Añadir nota de que BLEU de OPUS-100 y BLEU de FLEURS no son comparables.
- [ ] Confirmar que MOS sigue como no realizado.
- [ ] Confirmar que la clonación se describe como aproximada.
- [ ] Confirmar que no se afirma despliegue público.

---

## 9. Veredicto de la revisión

**El documento está bien estructurado y ya incorpora el experimento de 10 000 pares, pero no puede aprobarse como versión final sin corregir Dataset B y las métricas de los capítulos V y VI.**

- **Capítulos I–II:** base sólida; ajustes menores de estado (Colab, video, modelo base).
- **Capítulo III:** requiere reescritura de Dataset B.
- **Capítulo IV:** requiere resolver la contradicción 256 vs 10k y corregir Tabla 5 y pruebas.
- **Capítulo V:** conservar 5.1.1; reescribir 5.1.2 y Tablas 13–14.
- **Capítulo VI:** reemplazar todas las métricas v1/N=6 por las finales N=20.

**Estado:** `REQUIERE CORRECCIONES MAYORES` antes de la revisión final.
**Después de aplicar las correcciones de las secciones 3–8:** `LISTO PARA REVISIÓN FINAL`.

---

## 10. Evidencias de esta revisión

- `outputs/final_eval/master_20261104_082658/datasetB/aggregate_metrics.json`
- `outputs/final_eval/master_20261104_082658/datasetB/results_per_sample.csv`
- `outputs/final_eval/master_20261104_082658/datasetB/dataset_summary.json`
- `outputs/final_eval/master_20261104_082658/datasetB/exclusions.csv`
- `Docs/NMT_CONTROLLED_EXPERIMENT_10K.json`
- `Docs/TECHNICAL_AUDIT.md`

Los anexos textuales de la revisión y las salidas de auditoría se retiraron del repositorio durante la limpieza; se conservan en el respaldo externo.

**Fin de la revisión.**
