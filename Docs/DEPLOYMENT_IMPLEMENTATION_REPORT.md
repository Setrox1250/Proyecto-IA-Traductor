# Informe de implementación y despliegue

- **Proyecto:** Traducción de Mensajes de Audio con Clonación de Voz mediante IA
- **Alcance de esta entrega:** aplicación web funcional de extremo a extremo
- **Rama:** `feature/web-deployment`
- **Fecha:** 2026-11-05
- **Estado:** implementación local y pruebas E2E completadas; despliegue público pendiente

---

## 1. Estado inicial

El repositorio contenía:

- Pipeline de IA funcional y evaluado: Whisper Small, MarianMT base, XTTS-v2 y
  ECAPA-TDNN.
- Demo Gradio local.
- Pruebas unitarias y de contrato (17 aprobadas).
- Evidencias de evaluación en `outputs/final_eval/`.
- Maqueta Expo/React Native en `deploy/frontend` con dos pantallas de mensajería
  **sin conexión al pipeline**.
- No existía backend web, API, almacén temporal ni integración frontend-backend.

Git estaba limpio sobre `main`. Se creó la rama `feature/web-deployment` antes de
modificar archivos.

## 2. Arquitectura encontrada

| Capa | Implementación existente |
|---|---|
| ASR | `src/asr/transcribe.py` (`openai/whisper-small`) |
| NMT | `src/translation/model.py` (MarianMT base) |
| TTS | `src/voice_cloning/synthesize.py` (XTTS-v2, CPML) |
| Similitud | `src/evaluation/speaker_similarity.py` (ECAPA) |
| Orquestación | `src/pipeline/runner.py` (`process_audio`) |
| Interfaz | Gradio en `src/pipeline/demo.py` |
| Frontend | Maqueta Expo estática |

`process_audio` ya validaba audio, preparaba copias de 16 kHz y 22.05 kHz,
mantenía los modelos en caché y devolvía transcripción, traducción, métricas y
tiempos.

## 3. Arquitectura implementada

```text
Expo Web (React Native Web)
   │  multipart/form-data
   ▼
FastAPI + Uvicorn (1 worker)
   ├── validación de metadatos y tamaño
   ├── ffprobe + ffmpeg → WAV mono 44.1 kHz
   ├── lock de inferencia secuencial
   ├── ResultStore UUID + TTL
   └── importa src.pipeline.runner.process_audio
   │
   ▼
Whisper Small → MarianMT base → XTTS-v2 → ECAPA
   │
   ▼
JSON + URL temporal del WAV
```

Decisiones:

- **FastAPI** como capa de integración sin duplicar el pipeline.
- **Una sola inferencia a la vez** para proteger la GPU de 8 GB.
- **Modelos cacheados** entre peticiones por el runner existente.
- **Sin base de datos**: resultados en disco con UUID y TTL.
- **Respuesta JSON + endpoint de audio**: no se incrusta binario en JSON.
- **Frontend Expo Web**: se conservó la identidad visual "Hilo" y se reemplazó
  la maqueta estática por un flujo funcional.
- **Sin autenticación** en esta versión; limitación documentada.

## 4. Archivos creados

### Backend

- `deploy/backend/app/__init__.py`
- `deploy/backend/app/config.py`
- `deploy/backend/app/errors.py`
- `deploy/backend/app/audio.py`
- `deploy/backend/app/result_store.py`
- `deploy/backend/app/pipeline_service.py`
- `deploy/backend/app/schemas.py`
- `deploy/backend/app/main.py`
- `deploy/backend/run.sh`
- `deploy/backend/.env.example`
- `deploy/backend/.gitignore`
- `deploy/backend/Dockerfile`

### Frontend

- `deploy/frontend/src/api/client.js`
- `deploy/frontend/src/hooks/useEngineStatus.js`
- `deploy/frontend/src/utils/audio.js`
- `deploy/frontend/src/utils/download.js`
- `deploy/frontend/src/screens/TranslatorScreen.js`
- `deploy/frontend/src/components/AudioPlayer.js`
- `deploy/frontend/src/components/EngineStatusPill.js`
- `deploy/frontend/src/components/ErrorBubble.js`
- `deploy/frontend/src/components/FileDropCard.js`
- `deploy/frontend/src/components/ProcessingBubble.js`
- `deploy/frontend/src/components/ResultCard.js`
- `deploy/frontend/src/components/SelectedAudioBubble.js`
- `deploy/frontend/src/components/TranslatorSidebar.js`
- `deploy/frontend/e2e/translator.spec.js`
- `deploy/frontend/e2e/live.spec.js`
- `deploy/frontend/e2e/fixtures/fleurs_es_419_test_0000.wav`
- `deploy/frontend/e2e/fixtures/nota.txt`
- `deploy/frontend/e2e/fixtures/README.md`
- `deploy/frontend/playwright.config.js`
- `deploy/frontend/Dockerfile`
- `deploy/frontend/nginx.conf`
- `deploy/frontend/.env.example`
- `deploy/frontend/.dockerignore`

### Pruebas y despliegue

- `tests/api/conftest.py`
- `tests/api/test_api.py`
- `requirements/web.txt`
- `requirements/web-dev.txt`
- `deploy/docker-compose.yml`
- `.dockerignore`

### Documentación

- `Docs/DEPLOYMENT_IMPLEMENTATION_PLAN.md`
- `Docs/API_DOCUMENTATION.md`
- `Docs/DEPLOYMENT_GUIDE.md`
- `Docs/END_TO_END_TEST_REPORT.md`
- `Docs/DEPLOYMENT_STATUS.md`
- `Docs/DEPLOYMENT_IMPLEMENTATION_REPORT.md` (este documento)
- `Docs/deploy_evidence/README.md`
- `Docs/deploy_evidence/ARCHITECTURE.md`
- `Docs/deploy_evidence/screenshots/` (9 capturas reales)
- `Docs/deploy_evidence/logs/` (4 logs reales)
- `Docs/deploy_evidence/artifacts/` (WAV de entrada, respuesta JSON y WAV generado)

## 5. Archivos modificados

- `deploy/frontend/App.js`: nueva pantalla funcional.
- `deploy/frontend/package.json`: dependencias web/audio/document picker y scripts.
- `deploy/frontend/package-lock.json`: lockfile actualizado.
- `deploy/frontend/.gitignore`: artefactos de pruebas y build.
- `deploy/frontend/README.md`: instrucciones del sistema funcional (actualizado).
- `.gitignore`: se dejó de ignorar todo `deploy/`, se mantienen ignorados datos
  temporales y secretos.
- `README.md`: arquitectura web, ejecución, pruebas, límites y licencias.
- `Docs/INDEX.md`: índice actualizado con la documentación web.

### Archivos retirados de la maqueta estática

Se eliminaron componentes y pantallas sin uso (`ConversationsScreen`,
`ChatScreen`, `data.js`, `Avatar`, `ConversationRow`, etc.) para evitar código
muerto. La maqueta anterior queda en el historial de Git. Se conservaron y
reutilizaron `BrandMark`, `ChatPattern`, `Waveform` y el tema visual.

No se modificó:

- `src/` (pipeline de IA).
- Métricas, evidencias históricas ni checkpoints.
- Configuraciones de modelos.
- Pruebas existentes.

## 6. Tecnologías utilizadas

- FastAPI 0.143.0, Uvicorn 0.54.0, python-multipart.
- Pydantic 2, Starlette.
- ffmpeg/ffprobe.
- PyTorch 2.8.0+cu128, Transformers 4.57.3, Coqui TTS 0.27.5, SpeechBrain 1.1.1.
- Expo SDK 58, React Native 0.88.1, React 19.3.0, React Native Web 0.21.4.
- Expo DocumentPicker y expo-audio.
- Playwright 1.64.1.
- Docker/Compose, Nginx.

## 7. Endpoints implementados

| Método | Ruta | Función |
|---|---|---|
| GET | `/health` | Liveness |
| GET | `/api/v1/status` | Estado sin cargar modelos |
| POST | `/api/v1/translate` | Recibe audio y ejecuta el pipeline |
| GET | `/api/v1/results/{id}/audio` | Reproduce/descarga el WAV |
| GET | `/docs` | Swagger UI |
| GET | `/openapi.json` | Esquema OpenAPI |

Características del backend:

- Validación de extensión y MIME.
- Límite de tamaño aplicado durante la escritura.
- Límite de duración vía ffprobe y validación posterior.
- Normalización y eliminación de metadatos con ffmpeg.
- Nombres de archivo UUID; nunca se usa el nombre original en disco.
- Lock de inferencia secuencial.
- Respuestas de error uniformes con `request_id`.
- CORS explícito configurable.
- Resultados con expiración y limpieza periódica.
- Logs sin contenido de audio ni transcripciones.

## 8. Funcionalidades del frontend

- Pantalla principal tipo mensajería con identidad "Hilo".
- Selector real de archivo (Expo DocumentPicker).
- Validación previa de extensión, MIME, tamaño y duración cuando el navegador lo
  permite.
- Estado del motor consultado al backend.
- Indicador de procesamiento con tiempo transcurrido y etapas del pipeline.
- Prevención de envíos duplicados.
- Audio original reproducible.
- Transcripción en español.
- Traducción al inglés.
- Reproductor real del audio generado con `expo-audio`.
- Descarga del WAV generado.
- Métricas: similitud ECAPA, tiempo total, modelo NMT.
- Estados vacío, carga, error, éxito y reintento.
- Adaptación a móvil y escritorio.
- Sin botones decorativos: todos los controles tienen una acción.

## 9. Integración con los modelos

- Se importa `src.pipeline.runner.process_audio`; no se duplica el pipeline.
- `process_audio` mantiene los componentes en caché (`_COMPONENTS`).
- El backend no recarga los modelos por solicitud.
- El lock `asyncio.Lock` serializa las inferencias.
- Se usa **MarianMT base** (`translation_checkpoint: base`).
- No se activa el checkpoint controlado de 10 000 pares.
- No se afirma entrenamiento con 100 000 pares.
- XTTS-v2 exige `COQUI_TOS_AGREED=1`.
- ECAPA se reporta como similitud coseno, no como identidad ni porcentaje.
- No se declara tiempo real.

## 10. Pruebas ejecutadas y resultados

| Suite | Resultado |
|---|---|
| Pytest: unitarias, integración y API | **33 passed** |
| Playwright UI (API interceptada) | **8 passed** |
| Incluye reproducción, descarga, error 500 y conexión perdida | Verificado |
| Playwright E2E real (FLEURS) | **1 passed** (31.0 s en frío; 3.7 s en caliente) |
| Build web de producción | **OK** |
| Imagen Docker frontend | **OK** |
| Configuración Compose | **OK** |
| Imagen Docker backend | **OK** (CUDA 12.8, health/status en CPU) |
| Frontend Docker + Nginx + API | **OK** (UI en `:8088` vía proxy) |

La prueba E2E real verificó:

- subida de un audio FLEURS real;
- transcripción en español;
- traducción al inglés;
- generación de WAV de 24 kHz;
- similitud ECAPA;
- reproducción por Range;
- descarga con nombre seguro.

Resultado real en caliente (API): 2.20 s de pipeline; XTTS 1.62 s; ECAPA 0.0294.
La primera ejecución tras reiniciar el backend tardó ~31.0 s en el E2E del navegador
(carga fría). No es tiempo real.

## 11. Prueba de extremo a extremo

- **Entrada:** `fleurs_es_419_test_0000.wav` (FLEURS `es_419`, test, CC BY 4.0).
- **Transcripción:** «Se recomienda enfáticamente a los viajeros que se informen
  sobre cualquier riesgo del clima extremo en el área que visitan, dado que ello
  puede afectar sus planes de viaje.»
- **Traducción:** «Travelers are strongly advised to report any extreme weather
  risks in the area they visit, as this may affect their travel plans.»
- **Similitud ECAPA:** 0.5336 en la última llamada HTTP registrada.
- **Salida:** WAV PCM 16-bit mono 24 kHz, 7.883 s.
- **Evidencias:** `Docs/deploy_evidence/`.

## 12. Requisitos para ejecutar

- Python 3.11 y dependencias de `requirements/web.txt`.
- GPU NVIDIA con al menos 8 GB de VRAM recomendada.
- ffmpeg y ffprobe.
- `COQUI_TOS_AGREED=1` si se acepta CPML.
- Node.js 20+ para el frontend.
- Modelos descargados o cacheados (no incluidos).

Comandos principales:

```bash
# Backend
cd deploy/backend
cp .env.example .env
./run.sh

# Frontend
cd deploy/frontend
npm install
npm run web
```

## 13. Limitaciones

- Sin despliegue público ni URL.
- Sin autenticación, cuentas ni cuotas.
- UUID + TTL no equivalen a autorización multiusuario.
- Inferencia secuencial; no hay cola persistente.
- Sin grabación de micrófono en la web.
- Expo Go nativo no revalidado en dispositivo físico.
- La inferencia GPU dentro de Docker no se ejecutó; el contenedor se validó en
  CPU para health/status y la UI vía Nginx.
- Sin CI/CD, monitoreo ni rate limiting.
- La calidad de clonación es aproximada; no hay evaluación perceptual (MOS).
- El servicio no es de tiempo real.
- FLEURS no expone `speaker_id`; no se mide leakage de hablante.
- La imagen backend fue construida y validada en CPU (health/status); la inferencia GPU dentro del contenedor queda pendiente de validación en el host final.

## 14. Consideraciones de licencias

- Código propio: MIT.
- XTTS-v2/Coqui: CPML, con restricciones de uso comercial y redistribución.
- Whisper: MIT.
- MarianMT: revisar model card (CC BY 4.0).
- ECAPA: revisar model card (Apache 2.0).
- FLEURS: CC BY 4.0.
- La licencia MIT del repositorio no cubre pesos ni datasets de terceros.
- No se redistribuyeron pesos de XTTS-v2.
- La muestra FLEURS incluida como fixture conserva atribución y licencia.

## 15. Estado de preparación para despliegue

- Backend local: funcional.
- Frontend local: funcional.
- Integración: funcional y probada.
- Docker frontend: construido.
- Compose: validado.
- Docker backend: imagen construida y health/status validados en CPU.
- Documentación: completa.
- Despliegue público: **pendiente y no autorizado**.

## 16. Evidencias que debe aportar el usuario

Ya se incluyen capturas reales de pantalla, logs y artefactos. Pendientes
opcionales para el informe académico:

1. Captura de la bandeja de descargas del navegador.
2. Captura de terminal del backend en ejecución.
3. Captura de terminal del frontend en ejecución.
4. Si se publica: captura de la URL pública y del panel del proveedor.

No se incluyeron capturas simuladas.

## 17. Pendientes para GitHub y despliegue público

- Revisar el diff y hacer commit en `feature/web-deployment`.
- Abrir pull request (sin `push --force`).
- Elegir proveedor GPU y presupuesto.
- Construir/verificar la imagen backend en un host con NVIDIA Container Toolkit.
- Configurar dominio, HTTPS, CORS exacto y almacenamiento de cachés.
- Añadir autenticación/rate limiting antes de exposición pública.
- Configurar monitoreo, logs y política de retención.
- Ejecutar el E2E real contra el entorno desplegado.
- Actualizar `DEPLOYMENT_STATUS.md` solo cuando exista evidencia.

## 18. Estado de Git

- Rama: `feature/web-deployment`.
- Cambios de implementación **sin commit** al cierre de este informe.
- No se reescribió el historial.
- No se hizo `push --force`.
- No se realizó despliegue público.
