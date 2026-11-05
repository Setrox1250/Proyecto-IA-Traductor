# Reporte final Dataset B — FLEURS es_419

**Ejecución de referencia:** `outputs/final_eval/master_20261104_082658/` (local, RTX 5060 Laptop GPU)
**Notebook:** `notebooks/Proyecto_IA_Traductor_MASTER_COLAB.ipynb`
**Commit de ejecución:** `e2df5999daf5a0635c8986794742fef35f179b1d`
**Reserva:** `data/processed/manifests/fleurs_evaluation_v2_official_test.csv`

## 1. Configuración

- Dataset: `google/fleurs`, configuración `es_419`.
- Split oficial: `test`.
- Muestras reservadas: 20.
- Muestras evaluadas: 20.
- Muestras excluidas: 0.
- Filtro de calidad: duración ≥ 1 s y RMS ≥ 1e-4.
- Traducción: MarianMT base (`Helsinki-NLP/opus-mt-es-en`).
- XTTS-v2: referencia 22 050 Hz, salida 24 000 Hz.
- Speaker encoder: ECAPA-TDNN (`speechbrain/spkrec-ecapa-voxceleb`).

## 2. Métricas

| Métrica | Valor |
|---|---:|
| WER raw | 0.1173 |
| WER normalizado | 0.0613 |
| CER | 0.0252 |
| BLEU aislado | 23.94 |
| chrF aislado | 55.63 |
| BLEU pipeline | 20.27 |
| chrF pipeline | 54.14 |
| ECAPA media | 0.4502 |
| ECAPA mediana | 0.4452 |
| ECAPA mínima | 0.2818 |
| ECAPA máxima | 0.6214 |
| ECAPA desviación estándar | 0.0767 |
| Tiempo medio por muestra | 3.1838 s |
| RTF hot medio | 0.1776 |

## 3. Interpretación

- El WER normalizado (0.0613) es menor que el WER raw (0.1173), consistente con diferencias de puntuación y normalización ortográfica.
- El BLEU de pipeline (20.27) es menor que el BLEU aislado (23.94): los errores de ASR se propagan a la traducción.
- La similitud ECAPA media (0.4502) es un coseno continuo; **no** es un porcentaje de voz conservada.
- El RTF hot medio (0.1776) indica que, una vez cargados los modelos, el pipeline procesa más rápido que tiempo real. La primera muestra incluye cold start y no se usa para el RTF hot.

## 4. Gradio y errores

- Gradio se lanzó y procesó una muestra real; el servidor se cerró después.
- Se rechazaron correctamente: audio silencioso, audio demasiado corto, archivo inexistente y texto vacío para XTTS.

## 5. Limitaciones

- MOS no realizado.
- Clonación aproximada; no garantiza emociones, prosodia ni identidad perfecta.
- No es transmisión en tiempo real.
- FLEURS no expone `speaker_id`; no se puede medir leakage de hablante.
- XTTS-v2/Coqui usa CPML, no MIT; revisar licencia antes de distribuir pesos.
