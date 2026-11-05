# Auditoría Técnica — Estado Final del Proyecto

**Proyecto:** Traducción de Mensajes de Audio con Clonación de Voz mediante Inteligencia Artificial
**Fecha de actualización:** 2026-11-04
**Estado:** posterior a la limpieza profunda y a la reescritura del historial Git.
**Commit de ejecución del notebook:** `e2df5999daf5a0635c8986794742fef35f179b1d` (registrado en las métricas; pertenece al historial anterior a la limpieza).
**Run final:** `outputs/final_eval/master_20261104_082658/`

> Este documento es la fuente de verdad del estado técnico. Los documentos marcados como históricos conservan valores anteriores y no deben citarse como resultados finales.

---

## 1. Resumen ejecutivo

El proyecto es un prototipo funcional de traducción de voz ES→EN con clonación aproximada. La cadena completa se ejecutó con modelos reales:

```text
Audio ES → Whisper-small → MarianMT base → XTTS-v2 → ECAPA-TDNN
```

| Componente | Estado |
|---|---|
| Whisper-small | Implementado y ejecutado en 20 muestras |
| MarianMT base | Implementado y ejecutado; modelo final del pipeline |
| MarianMT 10k | Entrenado y evaluado; no mejoró al base; no es el modelo final |
| XTTS-v2 | Implementado y ejecutado; 20/20 salidas WAV 24 kHz |
| ECAPA-TDNN | Implementado y ejecutado; 20 comparaciones coseno |
| Pipeline S2S | Implementado y ejecutado; 20/20 procesadas, 0 excluidas |
| Gradio | Ejecutado localmente; sin despliegue público |
| Notebook maestro | 22 celdas, 10 de código, 10 ejecutadas, 0 errores |
| Dataset B | FLEURS `es_419`, split oficial `test`, 20 muestras |
| Entrenamiento 100k | No implementado y no ejecutado |
| MOS | No realizado |
| Expo | Maqueta visual independiente, no integrada |

---

## 2. Evaluación final FLEURS

**Fuente:** `outputs/final_eval/master_20261104_082658/datasetB/aggregate_metrics.json`

| Métrica | Valor | Interpretación |
|---|---:|---|
| WER raw | 0.117339 | Errores de palabras de Whisper |
| WER normalizado | 0.061313 | WER tras normalizar puntuación/mayúsculas |
| CER | 0.025203 | Errores de caracteres |
| BLEU aislado | 23.9378 | Traducción de referencia ES, sin errores ASR |
| chrF aislado | 55.6260 | chrF de traducción aislada |
| BLEU pipeline | 20.2742 | Traducción de la salida de Whisper |
| chrF pipeline | 54.1448 | chrF de la traducción del pipeline |
| ECAPA media | 0.450238 | Similitud coseno media |
| ECAPA mediana | 0.445236 | Mediana de similitud |
| ECAPA std | 0.076674 | Desviación estándar |
| ECAPA mín / máx | 0.281780 / 0.621371 | Rango observado |
| Tiempo total medio | 3.183755 s | 20 muestras |
| RTF hot medio | 0.177611 | 19 muestras en caliente |

- Muestras reservadas: 20.
- Muestras evaluadas: 20.
- Muestras excluidas: 0.
- Salidas WAV: 20/20.
- Errores: 0.
- Modelo NMT: `Helsinki-NLP/opus-mt-es-en` base.

> BLEU/chrF miden calidad textual de la traducción. ECAPA mide similitud entre embeddings vocales y **no es un porcentaje de identidad**.

Las cifras de la reserva histórica v1 no son válidas como evaluación final y se retiraron del repositorio.

---

## 3. Dataset B — FLEURS

### 3.1 Reserva final

- Dataset: `google/fleurs`.
- Configuración: `es_419`.
- Split: `test`.
- Archivo: `data/processed/manifests/fleurs_evaluation_v2_official_test.csv`.
- Muestras: 20.
- Duración: 228,12 s.
- Audio: WAV mono, 16 kHz.
- Referencia inglesa: TSV oficial de FLEURS por `sentence_id`.
- Filtro: duración ≥ 1 s, RMS ≥ `1e-4`.
- Exclusiones finales: 0.

### 3.2 Reserva histórica v1

- `source_split=train`.
- 20 audios, 14 dev / 6 test.
- Audios `0008`, `0016` y `0019` prácticamente silenciosos.
- `0008` produjo Whisper `"y"`, NMT `"and"` y WER 1.0.
- La reserva v1 se retiró del repositorio; **no se usa para resultados finales**.

La muestra final `fleurs_es_419_test_0008` es otra muestra (`sentence_id=1783`) y no es el audio silencioso histórico.

---

## 4. NMT — experimento controlado de 10 000 pares

**Fuente:** `Docs/NMT_CONTROLLED_EXPERIMENT_10K.json`.

| Parámetro | Valor |
|---|---:|
| Modelo base | `Helsinki-NLP/opus-mt-es-en` |
| Train disponible | 100 000 |
| Train usado | 10 000 |
| Validation usada | 1 000 |
| Test | 1 999 |
| Épocas | 1 |
| Batch size | 8 |
| Learning rate | 5e-5 |
| Optimizador | AdamW |
| Weight decay | 0.01 |
| Label smoothing | 0.1 |
| FP16 | Sí, en CUDA |
| `max_length` | 128 |
| `num_beams` | 4 |
| Semilla | 42 |
| Tiempo | 101,194 s |
| Training loss | 2,641712 |
| VRAM pico | 2,713 GiB |

Comparación sobre el mismo test de OPUS-100 (1 999 pares):

| Métrica | Base | Checkpoint 10k | Delta |
|---|---:|---:|---:|
| SacreBLEU | 43.4140 | 42.6499 | −0,7641 |
| chrF | 64.4179 | 63.6674 | −0,7506 |
| Eval loss | 1.3532 | 1.4047 | +0,0514 |

El checkpoint no mejoró en los valores observados. No se realizó prueba de significancia; no debe afirmarse “degradación estadísticamente comprobada”. El pipeline usa base.

El entrenamiento de **100 000 pares no está implementado ni ejecutado**. La ruta `--full` de `src/translation/train.py` lanza `NotImplementedError`; `train_controlled.py` limita a 10 000.

El checkpoint canónico está en `models/checkpoints/controlled_10k`, ignorado por Git. Su `model.safetensors` tiene SHA-256 `91324a018bbf0d49a5f58d3290612957b172721889a88eec32a402060af1b7a9`.

---

## 5. Módulos

### 5.1 ASR — Whisper-small

- Modelo: `openai/whisper-small`.
- Idioma: español.
- Tarea: `transcribe`.
- Entrada: 16 kHz mono.
- Evaluación final: 20 muestras FLEURS.
- WER raw: 0.117339.
- WER normalizado: 0.061313.
- CER: 0.025203.

El smoke test histórico de 3 muestras (WER 8,59 %, CER 2,59 %) no forma parte de la evidencia publicada y no es la evaluación final.

### 5.2 NMT — MarianMT

- Modelo final: `Helsinki-NLP/opus-mt-es-en` base.
- `max_length=128`.
- `num_beams=4`.
- BLEU aislado: 23.9378.
- chrF aislado: 55.6260.
- BLEU pipeline: 20.2742.
- chrF pipeline: 54.1448.

La caída aislado → pipeline es consistente con propagación de errores ASR:
- BLEU: 3,6635 puntos.
- chrF: 1,4812 puntos.

No comparar estos valores con el BLEU de OPUS-100: usan datasets y referencias distintas.

### 5.3 TTS — XTTS-v2

- Modelo: `coqui/XTTS-v2` vía `tts_models/multilingual/multi-dataset/xtts_v2`.
- Referencia: WAV mono 22 050 Hz.
- Salida: WAV 24 000 Hz.
- 20/20 muestras generadas.
- Duración de salida: 3,7127–17,3560 s.
- Requiere `COQUI_TOS_AGREED=1`.
- Licencia CPML.
- No se realizó MOS ni evaluación perceptual.

### 5.4 ECAPA-TDNN

- Modelo: `speechbrain/spkrec-ecapa-voxceleb`.
- Entrada mono 16 kHz.
- Embeddings L2-normalizados.
- Similitud coseno.
- 20 comparaciones.
- Media 0.450238; mediana 0.445236; std 0.076674; mín 0.281780; máx 0.621371.

No es un porcentaje de identidad. FLEURS no expone `speaker_id`; no se puede medir leakage de hablante.

---

## 6. Pipeline, Gradio y rendimiento

### 6.1 Pipeline

- 20/20 muestras procesadas.
- 0 exclusiones.
- 0 errores.
- Artefactos por muestra: `input.wav`, `asr_input.wav`, `xtts_reference.wav`, `output.wav`, `transcription.txt`, `translation.txt`, `metadata.json`.

### 6.2 Gradio

- Interfaz `gr.Blocks`.
- Servidor lanzado localmente y cerrado.
- Muestra `fleurs_es_419_test_0000.wav` procesada.
- `output_exists=true`, `server_launched=true`.
- Tiempo mostrado: 1,90 s.
- Similitud mostrada: 0,5518.

No hay despliegue público ni captura de pantalla en el repositorio. `deploy/frontend/` es una maqueta Expo independiente.

### 6.3 Tiempos

| Régimen | ASR | NMT | XTTS | ECAPA | Total |
|---|---:|---:|---:|---:|---:|
| Media 20 (incluye frío) | 0.339385 s | 0.114375 s | 2.411455 s | 0.095455 s | 3.183755 s |
| Media caliente 19 | 0.256300 s | 0.097274 s | 1.623384 s | 0.025663 s | 2.012995 s |
| Muestra fría | 1.9180 s | 0.4393 s | 17.3848 s | 1.4215 s | 25.4282 s |

- RTF cold: 1.9804.
- RTF hot: 0.177611.
- Runtime total del notebook: 87,4459 s.

Los tiempos varían entre ejecuciones; las métricas lingüísticas fueron estables en las runs finales.

---

## 7. Pruebas y reproducibilidad

- `pytest`: **17 passed**.
- Distribución: 15 unitarias + 2 de integración.
- Fallidas: 0.
- Omitidas: 0.
- Cobertura: no calculada.
- `ruff`: **All checks passed**.

Comandos:

```bash
.venv-xtts/bin/python -m pytest tests/ -q -p no:cacheprovider
.venv-xtts/bin/ruff check src scripts tests --no-cache
```

Las pruebas usan mocks y contratos; no cargan modelos reales.

Reproducibilidad:

- `requirements/` fijado.
- `librosa` incluido en ASR.
- Rutas ancladas con `src/paths.py`.
- `COQUI_TOS_AGREED=1` documentado.
- Manifiesto FLEURS v2 versionado.
- Notebook maestro intacto.
- CSV de OPUS-100 no incluidos; deben regenerarse.
- Checkpoint 10k no versionado.

---

## 8. Limitaciones y licencias

- MOS no realizado.
- Clonación aproximada.
- Sin streaming.
- Sin evaluación perceptual humana.
- N=20; sin intervalos de confianza.
- FLEURS sin `speaker_id`.
- Sin despliegue público, monitoreo, CI/CD ni prueba de concurrencia.
- XTTS-v2/Coqui usa CPML; el MIT del código no cubre pesos.
- Whisper, MarianMT, ECAPA y datasets conservan sus licencias.

Ver `THIRD_PARTY_LICENSES.md`.

---

## 9. Documentos relacionados

- `README.md` — instalación, uso y métricas finales.
- `Docs/INDEX.md` — índice documental.
- `Docs/REPORTE_DATASET_B_FINAL.md` — evaluación final FLEURS.
- `Docs/NMT_CONTROLLED_EXPERIMENT_10K.md` — experimento 10k.
- `Docs/REVISION_INFORME_ACADEMICO_FINAL.md` — revisión del documento académico.
- `Docs/auditoria_limpieza/INFORME_LIMPIEZA_REPOSITORIO.md` — limpieza y consolidación documental.
