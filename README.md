# IA-Proyecto — Traducción ES→EN con clonación de voz zero-shot

Prototipo académico que recibe un mensaje de audio en español y genera una traducción hablada al inglés, usando el mismo audio como referencia vocal. Incluye una **aplicación web funcional** (Expo Web + FastAPI) además del pipeline y la demo Gradio:

```text
Audio ES
   │
   ▼
Whisper-small (ASR, español)
   │
   ▼
MarianMT base (NMT, ES→EN)
   │
   ▼
XTTS-v2 (TTS + clonación aproximada)
   │
   ▼
ECAPA-TDNN (similitud vocal)
   │
   ▼
Audio EN + transcripción + traducción + métricas
```

## 1. Descripción

El proyecto integra reconocimiento automático del habla, traducción automática neuronal, síntesis de voz condicionada por una referencia y evaluación objetiva de similitud vocal. Es un **prototipo académico por lotes**, no un servicio de traducción en tiempo real.

El modelo de traducción seleccionado para el pipeline es **MarianMT base** (`Helsinki-NLP/opus-mt-es-en`). El ajuste fino controlado con 10 000 pares se conserva como experimento, pero no se usa por defecto porque no mejoró las métricas del modelo base.

## 2. Arquitectura y modelos

| Etapa | Modelo / tecnología | Función |
|---|---|---|
| ASR | `openai/whisper-small` | Transcribir audio español a texto |
| NMT | `Helsinki-NLP/opus-mt-es-en` base | Traducir español a inglés |
| TTS / clonación | `coqui/XTTS-v2` vía Coqui TTS | Sintetizar inglés con referencia vocal |
| Evaluación vocal | `speechbrain/spkrec-ecapa-voxceleb` | Embeddings ECAPA y similitud coseno |
| API web | FastAPI 0.143.0 + Uvicorn | Validación, cola secuencial, resultados temporales |
| Interfaz web | Expo SDK 58 / React Native Web | App funcional responsive |
| Demo alternativa | Gradio 5.49.1 | Demo local |
| Evaluación | FLEURS `es_419` | 20 muestras oficiales `test` |
| Entrenamiento NMT | OPUS-100 | 10 000 pares usados en el experimento controlado |

### Flujo de ejecución

1. Validación de audio: existencia, duración mínima, RMS mínimo y amplitud.
2. Preparación de una copia ASR a 16 kHz y una referencia XTTS a 22 050 Hz.
3. Transcripción con Whisper en español.
4. Traducción con MarianMT base.
5. Síntesis XTTS-v2 en inglés a 24 000 Hz.
6. Similitud coseno ECAPA entre audio original y generado.
7. Escritura de `metadata.json` y artefactos intermedios.

## 3. Estructura del repositorio

```text
configs/                  Configuración YAML
data/processed/manifests/ Reserva FLEURS v2 y manifiestos
deploy/backend/           API FastAPI, Dockerfile y configuración
deploy/frontend/          App Expo Web funcional y pruebas Playwright
Docs/                     Documentación, guías y evidencias de despliegue
models/                   Checkpoints locales (no versionados)
notebooks/                Notebook maestro e históricos
outputs/                  Resultados de ejecución (no versionados)
requirements/             Dependencias fijadas (incluye web.txt)
scripts/                  Descarga, preparación y evaluación
src/                      Código fuente del pipeline
tests/                    Pruebas unitarias, integración y API
```

## 4. Requisitos

- Python 3.11.
- GPU NVIDIA con CUDA para la ejecución validada.
- `COQUI_TOS_AGREED=1` para cargar XTTS-v2.
- ffmpeg y ffprobe para la API web.
- Node.js 20+ para el frontend Expo Web.
- Espacio para pesos de modelos y audios de evaluación.
- Los datasets y pesos **no están incluidos** en el repositorio.

Entorno validado de la ejecución final:

| Componente | Versión |
|---|---|
| Python | 3.11.15 |
| PyTorch | 2.8.0+cu128 |
| CUDA | 12.8 |
| Transformers | 4.57.3 |
| Datasets | 3.6.0 |
| Coqui TTS | 0.27.5 |
| SpeechBrain | 1.1.1 |
| Gradio | 5.49.1 |
| GPU | NVIDIA GeForce RTX 5060 Laptop GPU, 8 GB |

## 5. Instalación

```bash
python -m venv .venv-xtts
source .venv-xtts/bin/activate
pip install --upgrade pip
pip install -r requirements/base.txt
pip install -r requirements/dataset.txt
pip install -r requirements/asr.txt
pip install -r requirements/translation.txt
pip install -r requirements/voice_cloning.txt
# API web (incluye las dependencias anteriores + FastAPI/Uvicorn):
pip install -r requirements/web.txt
```

Las versiones están fijadas para evitar conflictos entre Coqui TTS, Transformers y PyTorch. Si se resuelven dependencias libremente, puede ser necesario un entorno separado para XTTS.

### Variable obligatoria para XTTS-v2

```bash
export COQUI_TOS_AGREED=1
```

XTTS-v2/Coqui usa la licencia **CPML**, no MIT. Ver `THIRD_PARTY_LICENSES.md`.

## 6. Preparación de datasets

### FLEURS — evaluación final

La reserva final usa el split oficial `test` de `google/fleurs`, configuración `es_419`:

```bash
python scripts/build_fleurs_reservation.py --n-samples 20
```

Salida:

`data/processed/manifests/fleurs_evaluation_v2_official_test.csv`

- 20 muestras.
- 0 dev / 20 test.
- 228,12 s.
- 16 kHz mono.
- 0 exclusiones en la ejecución final.

La reserva histórica `fleurs_evaluation_v1_reservation.csv` usaba `source_split=train` y no es válida como evaluación final.

### OPUS-100 — experimento NMT

```bash
python scripts/prepare_data.py --dataset opus100 --train-size 10000
```

Los CSV se generan en `data/processed/translation/`. No están incluidos en el repositorio.

## 7. Uso del pipeline

```python
from src.pipeline.runner import process_audio

result = process_audio("entrada_es.wav", "outputs/ejemplo")
print(result["transcription_es"])
print(result["translation_en"])
print(result["audio"]["output_path"])
print(result["speaker_similarity"])
```

Artefactos generados:

- `input.wav`
- `asr_input.wav`
- `xtts_reference.wav`
- `output.wav`
- `transcription.txt`
- `translation.txt`
- `metadata.json`

Para usar explícitamente el checkpoint controlado:

```python
result = process_audio(
    "entrada_es.wav",
    "outputs/ejemplo_checkpoint",
    translation_model_name_or_path="models/checkpoints/controlled_10k",
)
```

El valor por defecto es MarianMT base (`configs/translation.yaml`: `use_controlled_checkpoint: false`).

## 8. Aplicación web funcional

La app web reutiliza el pipeline existente. El frontend está en
`deploy/frontend/` y la API en `deploy/backend/`.

### 8.1 Backend

```bash
cd deploy/backend
cp .env.example .env       # ajusta COQUI_TOS_AGREED=1 si aceptas CPML
./run.sh
```

API: `http://localhost:8000` · Swagger: `http://localhost:8000/docs`

Endpoints:

- `GET /health`
- `GET /api/v1/status`
- `POST /api/v1/translate` (`multipart/form-data`, campo `file`)
- `GET /api/v1/results/{id}/audio` (reproducción/descarga con TTL)

La inferencia es secuencial y los resultados expiran (1 hora por defecto). No se
usa base de datos.

### 8.2 Frontend

```bash
cd deploy/frontend
npm install
npm run web
```

Abre `http://localhost:8081`. Para un dispositivo en la misma red:

```bash
EXPO_PUBLIC_API_URL=http://<IP-LAN>:8000 npm run web
```

Funcionalidades: selección de audio, validaciones, estado del motor,
procesamiento con aviso de primera carga, transcripción ES, traducción EN,
reproductor real y descarga del WAV. Build estático: `npm run build:web`.

### 8.3 Gradio (alternativa)

```bash
python -m src.pipeline.demo
```

Se conserva como demo local del pipeline. La app web es la interfaz principal de
esta entrega.

**No hay despliegue público.** El estado exacto está en
`Docs/DEPLOYMENT_STATUS.md`.

## 9. Evaluación final FLEURS

Fuente oficial:

`outputs/final_eval/master_20261104_082658/datasetB/aggregate_metrics.json`

Configuración:

- Split oficial `test` de FLEURS `es_419`.
- 20 muestras evaluadas.
- 0 excluidas.
- Modelo NMT: MarianMT base.

| Métrica | Valor | Qué mide |
|---|---:|---|
| WER raw | 0.117339 | Errores de palabras de Whisper sin normalizar |
| WER normalizado | 0.061313 | WER tras normalizar puntuación/mayúsculas |
| CER | 0.025203 | Errores de caracteres de Whisper |
| BLEU aislado | 23.9378 | Traducción de la referencia ES, sin errores ASR |
| chrF aislado | 55.6260 | chrF de la traducción aislada |
| BLEU pipeline | 20.2742 | Traducción de la salida de Whisper |
| chrF pipeline | 54.1448 | chrF de la traducción del pipeline |
| ECAPA media | 0.450238 | Similitud coseno media voz original/generada |
| ECAPA mediana | 0.445236 | Mediana de similitud coseno |
| ECAPA std | 0.076674 | Desviación estándar de similitud |
| Tiempo total medio | 3.183755 s | Tiempo medio de las 20 muestras |
| RTF hot | 0.177611 | Tiempo de proceso / duración, régimen caliente |

> BLEU y chrF miden calidad **textual** de la traducción. ECAPA mide similitud entre embeddings vocales; **no es un porcentaje de identidad** ni una evaluación perceptual.

## 10. Experimento NMT de 10 000 pares

| Elemento | Valor |
|---|---:|
| Modelo base | `Helsinki-NLP/opus-mt-es-en` |
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

El checkpoint **no mejoró** al base. Por eso el pipeline conserva MarianMT base. No se ejecutó ni implementó el entrenamiento de 100 000 pares.

## 11. Pruebas

```bash
# Backend y pipeline (rápidas, sin cargar modelos)
python -m pytest tests/unit tests/integration tests/api -q

# Frontend (API interceptada)
cd deploy/frontend
npx playwright test e2e/translator.spec.js

# E2E real (requiere backend, GPU y licencia CPML)
E2E_LIVE=1 npx playwright test e2e/live.spec.js
```

Resultado de la validación final:

- **33 pruebas Python aprobadas** (17 existentes + 16 de API).
- **8 pruebas Playwright de UI aprobadas**.
- **1 prueba E2E real aprobada** con FLEURS `es_419`.
- Build web estático correcto.
- Imagen Docker del frontend construida correctamente.
- Las pruebas rápidas no descargan modelos pesados; el E2E real usa la GPU y los
  pesos cacheados.

Detalle: `Docs/END_TO_END_TEST_REPORT.md` y `Docs/deploy_evidence/`.

## 12. Notebook maestro

`notebooks/Proyecto_IA_Traductor_MASTER_COLAB.ipynb`

- 22 celdas.
- 10 celdas de código.
- 10 ejecutadas.
- 0 errores.
- Ejecución de referencia: `outputs/final_eval/master_20261104_082658/`.

## 13. Limitaciones

- **MOS no realizado.** Solo existe `evaluation/voice_cloning/mos_template.csv`.
- Clonación **aproximada**; no garantiza identidad, emoción, prosodia ni ritmo.
- **Sin streaming** ni latencia de tiempo real.
- **Sin evaluación perceptual humana**.
- **N=20**; no hay intervalos de confianza ni prueba de significancia.
- FLEURS no expone `speaker_id`; no se puede medir leakage de hablante.
- Los CSV de OPUS-100 no están incluidos; el experimento 10k requiere regenerarlos.
- El checkpoint 10k no está versionado.
- No hay despliegue público, monitoreo, autenticación ni CI/CD.
- La inferencia es secuencial; no hay cola persistente ni concurrencia segura.
- No hay grabación de micrófono en la interfaz web (sí selección de archivo).
- La reproducción en Expo Go nativo no se revalidó en dispositivo físico.
- La inferencia GPU dentro de Docker no se revalidó; la imagen backend y el
  proxy Nginx se validaron en CPU.
- Detalle: `Docs/DEPLOYMENT_STATUS.md` y `Docs/deploy_evidence/README.md`.

## 14. Licencias

- Código propio: MIT (`LICENSE`).
- XTTS-v2/Coqui: **CPML**, con restricciones de uso comercial y redistribución.
- Whisper: MIT.
- MarianMT: verificar model card (CC BY 4.0).
- ECAPA: verificar model card (Apache 2.0).
- FLEURS: verificar dataset card (CC BY 4.0).
- OPUS-100: verificar dataset card.

La licencia MIT del código **no cubre** los pesos de XTTS-v2 ni los datasets. Ver `THIRD_PARTY_LICENSES.md`.

## 15. Documentación complementaria

- `Docs/INDEX.md` — índice y clasificación documental.
- `Docs/DEPLOYMENT_IMPLEMENTATION_PLAN.md` — plan y auditoría inicial.
- `Docs/DEPLOYMENT_GUIDE.md` — instalación, ejecución, Docker y GPU.
- `Docs/API_DOCUMENTATION.md` — endpoints, contratos y errores.
- `Docs/END_TO_END_TEST_REPORT.md` — pruebas y resultados reales.
- `Docs/DEPLOYMENT_STATUS.md` — qué está y qué no está desplegado.
- `Docs/DEPLOYMENT_IMPLEMENTATION_REPORT.md` — informe integral.
- `Docs/deploy_evidence/` — capturas, logs y artefactos reales.
- `Docs/TECHNICAL_AUDIT.md` — estado técnico consolidado.
- `Docs/REPORTE_DATASET_B_FINAL.md` — evaluación final FLEURS.
- `Docs/NMT_CONTROLLED_EXPERIMENT_10K.md` — experimento NMT y decisión de usar base.
- `Docs/REVISION_INFORME_ACADEMICO_FINAL.md` — revisión del documento académico I–VI.
- `Docs/auditoria_limpieza/INFORME_LIMPIEZA_REPOSITORIO.md` — informe de limpieza y consolidación.
- `THIRD_PARTY_LICENSES.md` — licencias de terceros.
