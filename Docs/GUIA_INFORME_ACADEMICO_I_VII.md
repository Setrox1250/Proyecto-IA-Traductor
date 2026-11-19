# Guía para redactar el informe académico I–VII

**Proyecto:** Traducción de mensajes de audio ES→EN con clonación de voz aproximada mediante IA.  
**Base de esta guía:** implementación y evidencias vigentes al 2026-11-18.

## Uso de esta guía y fuentes de evidencia

Esta es una plantilla para construir el informe solicitado. Las afirmaciones
cuantitativas deben citar una fuente del repositorio:

- Resultados finales: `outputs/final_eval/master_20261104_082658/datasetB/aggregate_metrics.json`.
- Experimento NMT: `Docs/NMT_CONTROLLED_EXPERIMENT_10K.md`.
- Pruebas web y E2E: `Docs/END_TO_END_TEST_REPORT.md`.
- Estado de despliegue: `Docs/DEPLOYMENT_STATUS.md`.
- Correcciones al informe previo I–VI: `Docs/REVISION_INFORME_ACADEMICO_FINAL.md`.

> No afirmar despliegue público, identidad vocal perfecta, tiempo real, MOS ni
> entrenamiento de 100 000 pares: no están demostrados en esta entrega.

> **Entornos a diferenciar en el informe:** el entrenamiento del experimento NMT
> se realizó en Google Colab con GPU. La RTX local se utilizó para desarrollo,
> pruebas de integración, evaluación y validación de la aplicación web; no debe
> presentarse como la plataforma de entrenamiento.

---

## I. Introducción

### 1.1 Título del proyecto

**Título sugerido:**

> Sistema de traducción de mensajes de audio del español al inglés con clonación
> de voz zero-shot aproximada mediante inteligencia artificial.

Como subtítulo técnico se puede indicar: *Whisper, MarianMT, XTTS-v2 y
ECAPA-TDNN*.

### 1.2 Antecedentes

Desarrollar dos a cuatro párrafos que cubran:

1. La barrera lingüística en el intercambio de mensajes de audio ES–EN.
2. La integración de reconocimiento automático del habla (ASR), traducción
   automática neuronal (NMT) y síntesis de voz (TTS).
3. La diferencia entre traducir texto y entregar una salida hablada condicionada
   por una referencia vocal.
4. La limitación ética y técnica: ECAPA mide cercanía de embeddings, no identidad
   vocal, emoción, prosodia ni naturalidad perceptual.

Modelos a presentar: Whisper-small (ASR), MarianMT ES→EN (NMT), XTTS-v2 (TTS)
y ECAPA-TDNN (similitud).

### 1.3 Problema a resolver

Formular una necesidad verificable. Texto base:

> Los usuarios que intercambian mensajes de voz en español e inglés requieren
> comprender el contenido en otro idioma sin perder por completo la referencia
> vocal del emisor. El uso separado de transcripción, traducción y síntesis exige
> pasos manuales y no produce un audio traducido integrado.

Delimitar: audios previamente grabados, dirección ES→EN y procesamiento por
lotes. Excluir streaming, conversación bidireccional, cuentas y garantía de
identidad vocal.

### 1.4 Objetivos

**Objetivo general sugerido**

> Diseñar e implementar un sistema de IA que reciba un audio en español,
> transcriba su contenido, lo traduzca al inglés y genere un audio en inglés
> condicionado por la voz de referencia, junto con métricas de calidad y
> similitud.

**Objetivos específicos sugeridos**

1. Integrar Whisper-small para transcribir español.
2. Traducir ES→EN con MarianMT y comparar el modelo base con un ajuste fino
   controlado.
3. Sintetizar la traducción con XTTS-v2 usando el audio de entrada como referencia.
4. Medir ASR, traducción, similitud vocal y rendimiento del pipeline.
5. Implementar una API y una interfaz web para carga, consulta y descarga.
6. Documentar limitaciones técnicas, seguridad, licencias y despliegue.

---

## II. Requerimientos

### 2.1 Definición del dominio

Definir el dominio como **traducción automática de voz a voz ES→EN** dentro de
NLP y procesamiento de audio. Añadir este flujo:

```text
Audio ES → ASR → texto ES → NMT → texto EN → TTS condicionado → audio EN
                                                    └→ ECAPA: similitud vocal
```

Actores: usuario que carga el audio y operador que configura el servicio.
Entradas: WAV, MP3, M4A, OGG, FLAC o WEBM. Salidas: transcripción ES, traducción
EN, WAV EN, tiempos y similitud ECAPA.

### 2.2 Determinación de requisitos

Separar funcionales y no funcionales:

| Tipo | Requisito verificable | Evidencia / estado |
|---|---|---|
| Funcional | Cargar y validar audio permitido | API y `tests/api/` |
| Funcional | Transcribir español | Whisper-small integrado |
| Funcional | Traducir ES→EN | MarianMT base integrado |
| Funcional | Generar WAV EN condicionado | XTTS-v2; requiere CPML |
| Funcional | Mostrar y descargar resultado | Frontend Expo Web |
| Funcional | Eliminar resultados temporales | TTL y `ResultStore` |
| No funcional | Límite de 20 MB y 120 s por defecto | Configuración de API |
| No funcional | Una inferencia a la vez | Lock para proteger la GPU |
| No funcional | Trazabilidad de errores | `request_id` y errores normalizados |
| Restricción | GPU NVIDIA recomendada, 8 GB VRAM | Entorno validado localmente |

Registrar como fuera de alcance: streaming, grabación de micrófono, cuentas,
MOS, evaluación humana y despliegue público.

---

## III. Planteamiento del dataset y preprocesamiento

### 3.1 Datos, fuentes y características

Explicar que el sistema combina modelos preentrenados y aprendizaje supervisado:

| Uso | Fuente | Contenido | Papel |
|---|---|---|---|
| Ajuste NMT | OPUS-100 ES–EN | pares de texto | Experimento controlado |
| Evaluación integral | FLEURS `es_419`, split oficial `test` | audio ES y referencias | Test final |
| Modelos | Hugging Face / Coqui | pesos y tokenizadores | ASR, NMT, TTS y ECAPA |

**Datos finales obligatorios:** FLEURS `es_419`, 20 muestras del split oficial
`test`, 228,12 s, WAV mono 16 kHz y 0 exclusiones. No usar como evaluación final
la reserva histórica v1 de 14 dev / 6 test.

Características a explicar:

- Audio: frecuencia, canales, duración, RMS y amplitud.
- ASR: audio a 16 kHz mono.
- NMT: pares ES–EN, `max_length=128` y semilla 42.
- TTS: referencia de 22 050 Hz y texto inglés.
- ECAPA: embeddings normalizados y similitud coseno.

### 3.2 Normalización y filtrado

Describir el procedimiento en orden:

1. Validación de existencia, extensión, MIME, tamaño y duración.
2. Rechazo de audio vacío, corrupto, silencioso o fuera de límites.
3. Preparación para ASR a 16 kHz mono.
4. Preparación de referencia XTTS a 22 050 Hz mono.
5. Normalización/decodificación mediante ffmpeg en la API web.
6. Generación del WAV final a 24 kHz y limpieza por TTL.

### 3.3 Training, validación y test

No mezclar los experimentos. Usar una tabla como la siguiente:

| Actividad | Training | Validación | Test | Estado |
|---|---:|---:|---:|---|
| Smoke test NMT | 256 pares | 64 pares | — | verificación técnica histórica |
| NMT controlado | 10 000 pares | 1 000 pares | 1 999 pares OPUS-100 | ejecutado, 1 época |
| Evaluación end-to-end | — | — | 20 audios FLEURS | evaluación final |

Indicar que el experimento NMT de 10 000 pares se entrenó en Google Colab con
GPU. FLEURS no usa validación cruzada: las 20 muestras se reservaron como test
final. El entrenamiento de 100 000 pares no está implementado ni ejecutado.

---

## IV. Aprendizaje

### 4.1 Planteamiento del modelo de aprendizaje

Presentar la arquitectura compuesta:

| Módulo | Modelo | Función |
|---|---|---|
| ASR | Whisper-small | Transcripción ES |
| NMT | MarianMT base | Traducción ES→EN |
| TTS | XTTS-v2 | Síntesis zero-shot condicionada |
| Similitud | ECAPA-TDNN | Embeddings y coseno |

El aprendizaje propio evaluado es el fine-tuning supervisado de MarianMT. El
modelo final es el **base** porque el checkpoint de 10 000 pares no mejoró las
métricas del experimento.

### 4.2 Desarrollo e implementación

Documentar los componentes y decisiones:

- Orquestación: `src/pipeline/runner.py`.
- Configuración: `configs/asr.yaml`, `configs/translation.yaml` y
  `configs/voice_cloning.yaml`.
- API: `deploy/backend/app/`, FastAPI, una inferencia por vez y resultados con TTL.
- Web: `deploy/frontend/`, Expo Web, Nginx y Playwright.
- NMT: `max_length=128`, `num_beams=4`, semilla 42.
- Experimento 10k: 1 época, batch 8, learning rate `5e-5`, AdamW, weight decay
  0,01, label smoothing 0,1 y FP16 en CUDA.

Añadir un diagrama de componentes y justificar: inferencia secuencial, modelos
cacheados, ausencia de base de datos y uso de MarianMT base en producción.

---

## V. Comprobación

### 5.1 Entrenamiento y pruebas

Separar la comprobación de aprendizaje de las pruebas de software.

**Resultados del experimento NMT (OPUS-100, 1 999 pares):**

| Métrica | MarianMT base | Checkpoint 10k |
|---|---:|---:|
| SacreBLEU | 43,4140 | 42,6499 |
| chrF | 64,4179 | 63,6674 |
| Eval loss | 1,3532 | 1,4047 |

Conclusión: el ajuste de 10 000 pares no superó al base; por tanto,
`use_controlled_checkpoint: false` es correcto. No afirmar degradación
estadísticamente significativa porque no se hizo una prueba de significancia.

**Pruebas de implementación vigentes:**

- 33 pruebas Python aprobadas: unitarias, integración y API.
- 8 pruebas Playwright de interfaz aprobadas con API interceptada.
- Build web estático y configuración Compose validados.
- E2E real previo con FLEURS aprobado en host GPU; citarlo como evidencia
  histórica, no como validación actual de inferencia GPU dentro de Docker.

Describir los casos: entradas inválidas, licencia XTTS, CORS, expiración TTL,
subida, descarga, errores del backend y desconexión.

---

## VI. Evaluación

### 6.1 Métricas y evaluación del modelo

Definir WER/CER (ASR), SacreBLEU/chrF (traducción), ECAPA (similitud de
embeddings) y RTF (rendimiento). ECAPA no es porcentaje de identidad.

Usar solo la evaluación final FLEURS (N=20):

| Métrica | Resultado |
|---|---:|
| WER raw | 0,117339 |
| WER normalizado | 0,061313 |
| CER | 0,025203 |
| BLEU aislado | 23,9378 |
| chrF aislado | 55,6260 |
| BLEU pipeline | 20,2742 |
| chrF pipeline | 54,1448 |
| ECAPA media | 0,450238 |
| ECAPA mediana | 0,445236 |
| ECAPA desviación estándar | 0,076674 |
| Tiempo total medio | 3,183755 s |
| RTF hot | 0,177611 |

Explicar la caída de NMT aislado a pipeline: 3,6635 puntos BLEU y 1,4812 chrF,
coherente con propagación de errores del ASR. No comparar estas métricas FLEURS
con OPUS-100, porque los conjuntos y referencias son distintos.

### 6.2 Evaluación de desempeño del sistema

Interpretar con límites:

- Se procesaron 20/20 muestras y se generaron 20/20 WAV.
- La primera ejecución carga modelos; el rendimiento mejora en caliente.
- XTTS concentra la mayor parte del tiempo de proceso.
- La similitud vocal es aproximada; no hay MOS ni evaluación humana.
- FLEURS no expone `speaker_id`; no se prueba independencia de hablantes.

Proponer mejoras: MOS, evaluación más extensa, intervalos de confianza, cola
persistente, concurrencia segura, seguridad y despliegue con GPU.

---

## VII. Despliegue del proyecto

### 7.1 Publicación en GitHub

No declarar una publicación o release inexistente. El trabajo web está en
`feature/web-deployment` y debe revisarse e integrarse antes de una release.

#### 7.1.1 Documentación del proyecto

Referenciar:

- `README.md`: resumen, instalación, métricas y licencias.
- `Docs/INDEX.md`: índice vigente.
- `Docs/API_DOCUMENTATION.md`: contratos de API.
- `Docs/DEPLOYMENT_GUIDE.md`: ejecución, Docker y GPU.
- `Docs/DEPLOYMENT_STATUS.md`: estado y bloqueadores actuales.
- `Docs/END_TO_END_TEST_REPORT.md`: pruebas y evidencias.
- `THIRD_PARTY_LICENSES.md`: licencias de terceros.

#### 7.1.2 Código del sistema

| Ruta | Contenido |
|---|---|
| `src/` | Pipeline y módulos de IA |
| `configs/` | Parámetros de ASR, NMT y TTS |
| `scripts/` | Preparación y evaluación |
| `tests/` | Unitarias, integración y API |
| `deploy/backend/` | FastAPI y Dockerfile |
| `deploy/frontend/` | Expo Web, Nginx y E2E |
| `requirements/` | Dependencias fijadas |

Aclarar que pesos, checkpoints, resultados pesados y audios de usuarios no se
versionan por tamaño, privacidad y licencias.

#### 7.1.3 Ejecución y pruebas

```bash
# Backend, integración y API
.venv-xtts/bin/python -m pytest tests/unit tests/integration tests/api -q

# Frontend
cd deploy/frontend
npm run test:e2e
npm run build:web

# Configuración de contenedores
cd ../
docker compose config
```

Indicar que E2E real y Compose con GPU requieren modelos, aceptación CPML, GPU
NVIDIA y NVIDIA Container Toolkit.

### 7.2 Deploy de la aplicación web

**Estado real:** hay Dockerfiles, Nginx, Compose y una aplicación funcional
local; no hay URL pública ni despliegue de producción.

```text
Internet → HTTPS / Nginx → Expo Web estático + proxy /api → FastAPI → GPU NVIDIA
```

**Checklist previo a publicación**

- [ ] Revisar y aceptar la licencia CPML de XTTS-v2 según el uso planificado.
- [ ] Instalar NVIDIA Container Toolkit en el host destino.
- [ ] Construir imágenes y ejecutar una traducción real con GPU en Docker.
- [ ] Configurar dominio, HTTPS, firewall y CORS con origen exacto.
- [ ] Añadir autenticación y rate limiting, o limitar el sistema a una red privada.
- [ ] Definir retención de audios, monitoreo, logs y presupuesto GPU.
- [ ] Integrar la rama de despliegue y etiquetar una release.

**Texto de cierre sugerido:**

> El proyecto cuenta con una aplicación web integrada y validada localmente. Su
> publicación pública permanece pendiente porque requiere infraestructura GPU,
> controles de seguridad, configuración HTTPS y validación de inferencia GPU en
> contenedores. La entrega demuestra preparación para una demostración controlada,
> sin afirmar operación pública en producción.

---

## Lista de comprobación final del informe

- [ ] Todas las tablas finales usan FLEURS oficial `test`, N=20.
- [ ] Se diferencia el smoke test de 256 pares del experimento principal de 10k.
- [ ] Se declara MarianMT base como modelo final.
- [ ] No se afirman 100k, MOS, streaming, identidad vocal ni deploy público.
- [ ] Las métricas incluyen fuente y fecha.
- [ ] El capítulo VII refleja con honestidad el estado del despliegue.
