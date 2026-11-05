# Reporte de pruebas de extremo a extremo

- **Fecha:** 2026-11-04 / 2026-11-05
- **Rama:** `feature/web-deployment`
- **Estado:** pruebas locales completadas con pipeline real
- **Despliegue público:** no realizado

## 1. Entorno de ejecución

| Componente | Versión / valor |
|---|---|
| Sistema | Linux |
| Python | 3.11.15 |
| PyTorch | 2.8.0+cu128 |
| CUDA | 12.8 |
| GPU | NVIDIA GeForce RTX 5060 Laptop GPU, 7.6 GiB |
| Transformers | 4.57.3 |
| Coqui TTS | 0.27.5 |
| SpeechBrain | 1.1.1 |
| FastAPI | 0.143.0 |
| Uvicorn | 0.54.0 |
| Node.js | 26.13.0 |
| Expo SDK | 58.0.23 |
| React Native | 0.88.1 |
| React | 19.3.0 |
| Playwright | 1.64.1 |
| Navegador | Chromium 156 headless (Chrome for Testing) |

## 2. Muestra de audio

- **Archivo:** `deploy/frontend/e2e/fixtures/fleurs_es_419_test_0000.wav`
- **Origen:** `google/fleurs`, configuración `es_419`, split oficial `test`.
- **Sentence ID:** 2001.
- **Duración:** 12.84 s, mono, 16 kHz.
- **Licencia:** CC BY 4.0.
- **Transcripción de referencia:** «Se recomienda enfáticamente a los viajeros
  que se informen sobre cualquier riesgo del clima extremo en el área que
  visitan, dado que ello puede afectar sus planes de viaje.»
- **Procedencia:** descargada del dataset público FLEURS y conservada también en
  `Docs/deploy_evidence/artifacts/`.

No se usaron audios personales ni de terceros sin autorización.

## 3. Pruebas ejecutadas

### 3.1 Backend y pipeline existente

Comando:

```bash
.venv-xtts/bin/python -m pytest tests/unit tests/integration tests/api -q
```

Resultado: **33 passed** (17 pruebas existentes + 16 nuevas de API).

Cobertura de las pruebas nuevas:

- `/health` y `/api/v1/status`.
- Estado degradado sin licencia CPML.
- Traducción correcta con pipeline simulado.
- Audio vacío, extensión inválida, MIME inválido, tamaño excedido, audio
  corrupto, audio demasiado largo y audio silencioso.
- Error del pipeline saneado sin rutas internas.
- Error de licencia XTTS → 503.
- Resultado inexistente → 404.
- CORS permitido/denegado.
- OpenAPI con los cuatro endpoints.
- Expiración y eliminación del almacén de resultados.

Evidencia: `Docs/deploy_evidence/logs/pytest.log`.

### 3.2 Frontend (API interceptada)

Comando:

```bash
cd deploy/frontend
npx playwright test e2e/translator.spec.js
```

Resultado: **8 passed**.

Casos:

1. Pantalla principal y estado del motor.
2. Selección de audio y habilitación de traducción.
3. Estado de procesamiento y visualización de resultados.
4. Descarga del audio generado.
5. Validación de extensión no permitida.
6. Error del backend y botón de reintento.
7. Conexión perdida durante el procesamiento.
8. Adaptación móvil sin sidebar.

Evidencia: `Docs/deploy_evidence/logs/playwright-ui.log`.

### 3.3 E2E real con pipeline

Comando:

```bash
cd deploy/frontend
E2E_LIVE=1 npx playwright test e2e/live.spec.js
```

Resultado: **1 passed** en 3.7 s con modelos calientes. Tras reiniciar el backend, la misma prueba tardó 31.0 s por la carga inicial de modelos.

Flujo verificado:

1. La página carga y consulta `/api/v1/status`.
2. Se selecciona el WAV FLEURS desde el navegador.
3. Se envía por multipart a `POST /api/v1/translate`.
4. Whisper transcribe el audio.
5. MarianMT base traduce al inglés.
6. XTTS-v2 genera el WAV con referencia vocal.
7. ECAPA calcula la similitud.
8. El navegador muestra transcripción y traducción.
9. El reproductor solicita el audio por Range (`206 Partial Content`).
10. El botón de descarga produce un WAV con nombre
    `hilo_<id>_en.wav`.

Evidencia: `Docs/deploy_evidence/logs/playwright-live.log`.

### 3.4 Llamada HTTP real adicional

```bash
curl -X POST http://127.0.0.1:8000/api/v1/translate \
  -F "file=@fleurs_es_419_test_0000.wav;type=audio/wav"
```

Resultado real (modelos calientes):

- HTTP 200.
- Transcripción: «Se recomienda enfáticamente a los viajeros que se informen
  sobre cualquier riesgo del clima extremo en el área que visitan, dado que ello
  puede afectar sus planes de viaje.»
- Traducción: «Travelers are strongly advised to report any extreme weather risks
  in the area they visit, as this may affect their travel plans.»
- Similitud ECAPA: 0.5336 (última llamada de evidencia).
- Tiempo total: 2.2003 s (última llamada de evidencia; 2.0949 s en la anterior).
- ASR: 0.4024 s; NMT: 0.1173 s; XTTS: 1.6211 s; ECAPA: 0.0294 s.
- Salida: WAV PCM 16-bit mono 24 kHz, 7.883 s.
- Respuesta: `Docs/deploy_evidence/artifacts/final_api_result.json`.
- Audio: `Docs/deploy_evidence/artifacts/final_api_output.wav`.

Primera ejecución en frío de la sesión: ~22.6 s (incluye carga inicial de
modelos). No se declara tiempo real.

### 3.5 Build y Docker

| Prueba | Comando | Resultado |
|---|---|---|
| Build web estático | `npm run build:web` | OK, `dist/` generado |
| Imagen frontend | `docker build -t hilo-frontend:test -f Dockerfile .` | OK |
| Configuración Compose | `docker compose config` | OK |
| Imagen backend | `docker build -t hilo-backend:test -f Dockerfile .` | OK (CUDA 12.8) |
| Contenedor backend | `GET /health`, `GET /api/v1/status` | OK en CPU |
| Frontend + Nginx + API | UI en `:8088` → proxy `/api` | OK |

No se ejecutó un despliegue público ni se generaron costos.

## 4. Resultados observados

- La UI muestra el estado real del motor consultando el backend.
- La primera petición puede tardar decenas de segundos; la UI avisa y evita
  envíos duplicados.
- La sesión reutiliza los modelos cargados y baja el tiempo a ~2 s en caliente.
- La reproducción del WAV funciona con peticiones Range.
- La descarga entrega un nombre seguro generado por el servidor, no el nombre
  original.
- Los errores del backend se muestran con mensaje comprensible y `request_id`.
- Los archivos inválidos son rechazados antes del pipeline.
- Los resultados se eliminan al expirar y no hay listado público.

## 5. Incidencias encontradas y resueltas

| Incidencia | Resolución |
|---|---|
| Selectores Playwright duplicados por sidebar/header y textos repetidos | Se usaron roles y `exact: true` |
| `download` cross-origin no disparaba descarga en el mock | Se añadió `Content-Disposition: attachment` al mock del endpoint |
| Tipografía demasiado pequeña en escritorio | Se aumentaron tamaños y espaciados de la interfaz |
| La primera petición no tenía feedback del tiempo | Se añadió contador de segundos y aviso de carga inicial |
| El frontend usaba `localhost:8000` en LAN | Se derivó el host y se documentó `EXPO_PUBLIC_API_URL` |
| No se verificaba el flag de licencia antes de subir | La API responde 503 inmediatamente si falta CPML |
| Riesgo de nombres originales maliciosos | Se guarda con UUID y extensión validada |
| Archivos corruptos o formatos móviles | Normalización con ffmpeg + validación `soundfile` |

## 6. Limitaciones

- No hay despliegue público.
- No hay autenticación ni aislamiento de sesiones; el UUID y el TTL son la única
  protección de resultados.
- La inferencia es secuencial; las peticiones concurrentes esperan.
- No se implementó grabación de micrófono en la web.
- La reproducción selección nativa en Expo Go no se revalidó en dispositivo
  físico.
- La inferencia GPU dentro de Docker no se ejecutó; el contenedor se validó en
  CPU para health/status y la UI vía Nginx.
- Los modelos XTTS-v2 están sujetos a CPML; no se redistribuyen.
- El tiempo depende de la GPU y de si los modelos están calientes.

## 7. Evidencias

Ver `Docs/deploy_evidence/README.md` para el índice completo, capturas y
artefactos. Las capturas de pantalla incluidas corresponden a ejecuciones reales
del pipeline con FLEURS.
