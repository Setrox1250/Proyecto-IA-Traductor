# 4.2 Desarrollo e Implementación del Modelo

## 4.2.1 Entorno y organización del repositorio

NMT y ASR cuentan con evidencia ejecutada previa en Colab Tesla T4. Para XTTS/ECAPA se incorporó un runtime independiente reproducible: Python 3.11.15, torch/torchaudio 2.8.0+cu128, transformers 4.57.3, coqui-tts 0.27.5, speechbrain 1.1.1 y numpy 2.4.6. La combinación y los modelos se ejecutaron localmente en una RTX 5060 Laptop GPU; los notebooks conservan el procedimiento reproducible para Colab.

La organización incorpora `src/voice_cloning/audio.py`, `synthesize.py`, `src/evaluation/speaker_similarity.py`, `src/pipeline/runner.py` y `demo.py`. NMT y ASR previamente validados no fueron modificados.

## 4.2.2 Preparación de los datos para el entrenamiento

Dataset A: OPUS-100, 100 000 train, 1 990 validation, 1 999 test, seed 42. Dataset B: FLEURS es_419, 20 audios, 14 dev y 6 test, 203.34 s, WAV mono 16 kHz y sin `speaker_id`. Marian usa su tokenizador oficial, `max_length=128`, padding dinámico y `DataCollatorForSeq2Seq`. La justificación de 128 procede de 10 000 pares: p99 ES=76 y EN=71.

## 4.2.3 Configuración de hiperparámetros

**Ejecutados en smoke test:** batch 8, LR 5e-5, AdamW, weight decay 0.01, label smoothing 0.1, FP16, beam 4, max length 128 y seed 42.

**Propuestos para full training (no ejecutados):** 100 000 pares, 1 990 validation y 3 épocas. No deben presentarse como experimentos realizados.

## 4.2.4 Entrenamiento (fine-tuning) del modelo

El único entrenamiento ejecutado es debug: 256 pares train, 64 validation y una época; AdamW y FP16. Validó el proceso técnico. Full training 100 000: **PENDIENTE**.

## 4.2.5 Comparación entre modelo base y modelo ajustado

En una comparación preliminar sobre 64 ejemplos idénticos de validación, el modelo MarianMT base obtuvo una pérdida de evaluación de 2.5513, un SacreBLEU de 42.33 y un chrF de 64.80. El modelo ajustado durante el smoke test de fine-tuning con 256 pares y una época obtuvo una pérdida de 2.5663, un SacreBLEU de 41.63 y un chrF de 64.74. Las diferencias fueron de +0.0150 en pérdida, −0.70 BLEU y −0.06 chrF. Estos resultados no demuestran una mejora lingüística, sino que confirman el funcionamiento estable del procedimiento de entrenamiento, evaluación y generación antes de ejecutar el ajuste completo sobre los 100 000 pares.

## 4.2.6 Integración del pipeline Speech-to-Speech

La integración ejecutada es Whisper-small → MarianMT base → XTTS-v2 → ECAPA, manteniendo deliberadamente el checkpoint MarianMT base. Se procesaron tres muestras FLEURS `es_419` del split oficial `validation`, empleado como DEV para este smoke test. Cada ejecución dejó `input.wav`, entrada ASR a 16 kHz, referencia XTTS a 22,05 kHz, transcripción, traducción, salida WAV 24 kHz y `metadata.json` en `outputs/smoke_tests/pipeline/<sample_id>/`.

| Muestra | Total (s) | RTF total | Similitud ECAPA |
|---|---:|---:|---:|
| `fleurs_es_419_dev_00` | 39.1977 | 3.9355 | 0.547525 |
| `fleurs_es_419_dev_01` | 1.8358 | 0.1937 | 0.341537 |
| `fleurs_es_419_dev_02` | 2.8732 | 0.2064 | 0.567304 |

La primera muestra incluye carga fría de modelos; las dos restantes corresponden al régimen caliente, con RTF medio 0.2001. El caso `dev_02` conserva una limitación observada: un error ASR en “jinete” se propagó a una traducción inglesa defectuosa y XTTS sintetizó ese contenido. Es evidencia de propagación de errores propia de una arquitectura en cascada, no una corrección manual.

## 4.2.7 Evaluación de la similitud vocal e interfaz de demostración

ECAPA está implementado como coseno continuo entre embeddings preentrenados, sin umbral de “misma voz”. Sobre las tres síntesis XTTS con texto de referencia inglés oficial obtuvo 0.599170, 0.396744 y 0.555145; media 0.517020, mínimo 0.396744 y máximo 0.599170. Estas cifras confirman que el módulo puede comparar audio de referencia y síntesis de manera objetiva, pero N=3 no constituye una evaluación definitiva ni un porcentaje de voz conservada.

La plantilla humana permanece en `evaluation/voice_cloning/mos_template.csv` sin evaluadores ni resultados fabricados. La interfaz de demostración `src/pipeline/demo.py` se construyó localmente con Gradio 5.49.1 como `Blocks`, y se expone también mediante `notebooks/pipeline/01_gradio_demo.ipynb`; no se realizó despliegue cloud persistente.

## Discrepancias y trazabilidad

| Afirmación | Evidencia | Estado |
|---|---|---|
| Whisper-small | Notebook y JSON ASR ejecutados; WER 8.59%, CER 2.59% | CONFIRMADO SOLO COMO SMOKE TEST |
| MarianMT base | Notebook y JSON NMT ejecutados; BLEU 36.33, chrF 68.82 | CONFIRMADO SOLO COMO SMOKE TEST |
| XTTS-v2 | Tres WAV reales 24 kHz, resultados JSON y RTX 5060 | CONFIRMADO SOLO COMO SMOKE TEST |
| ECAPA | Tres cosenos sobre síntesis XTTS reales | CONFIRMADO SOLO COMO SMOKE TEST |
| max_length 128 | Análisis sobre 10 000 pares | CONFIRMADO |
| beam 4 | Configuración y smoke NMT | CONFIRMADO SOLO COMO SMOKE TEST |
| AdamW, label smoothing 0.1, FP16 | Smoke fine-tuning 256/64/1 época | CONFIRMADO SOLO COMO SMOKE TEST |
| NMT full training | No ejecutado por decisión explícita | PENDIENTE |
| Pipeline S2S | Tres ejecuciones reales y metadata por muestra | CONFIRMADO SOLO COMO SMOKE TEST |
| speaker similarity | ECAPA continuo sobre tres pares reales | CONFIRMADO SOLO COMO SMOKE TEST |
| Gradio | Interfaz de demostración construida localmente, sin despliegue persistente | CONFIRMADO SOLO COMO SMOKE TEST |
