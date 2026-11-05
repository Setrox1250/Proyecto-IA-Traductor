# Plan de implementación del sistema web y despliegue

- **Proyecto:** Traducción de mensajes de audio ES→EN con clonación de voz
- **Rama:** `feature/web-deployment`
- **Fecha de auditoría:** 2026-11-04
- **Estado:** plan aprobado para implementación

## 1. Diagnóstico del estado inicial

### 1.1 Repositorio

El repositorio contiene un pipeline de IA funcional, modular y ya evaluado. No
existía un backend web ni una API. La carpeta `deploy/frontend/` contenía
únicamente una maqueta Expo/React Native con dos pantallas estáticas
(conversaciones y chat), sin ninguna conexión con el pipeline.

El estado de Git al iniciar la intervención estaba limpio sobre `main`. Todo el
trabajo se realiza en la rama `feature/web-deployment`, sin reescribir historia.

### 1.2 Pipeline existente reutilizable

| Componente | Archivo | Decisión |
|---|---|---|
| Orquestación | `src/pipeline/runner.py` | Reutilizar sin duplicar |
| ASR Whisper Small | `src/asr/transcribe.py` | Reutilizar |
| Traducción MarianMT base | `src/translation/model.py` | Reutilizar; no activar checkpoint controlado |
| XTTS-v2 | `src/voice_cloning/synthesize.py` | Reutilizar con licencia CPML aceptada |
| Preparación de audio | `src/voice_cloning/audio.py` | Reutilizar |
| Similitud ECAPA | `src/evaluation/speaker_similarity.py` | Reutilizar como evaluación, no como garantía de identidad |
| Interfaz Gradio | `src/pipeline/demo.py` | Conservar como demo alternativa, no duplicar en API |

`process_audio()` ya:

- valida duración, silencio y amplitud antes de cargar modelos;
- prepara copias ASR (16 kHz) y referencia XTTS (22.05 kHz);
- mantiene los modelos en caché entre solicitudes (`_COMPONENTS`);
- devuelve transcripción, traducción, similitud ECAPA, tiempos y metadatos;
- escribe `output.wav`, transcripciones y `metadata.json`.

### 1.3 Modelos y entorno local

- Python 3.11.15.
- PyTorch 2.8.0+cu128; CUDA disponible.
- NVIDIA GeForce RTX 5060 Laptop GPU, 8 GB VRAM.
- Pesos cacheados localmente: Whisper Small, MarianMT ES→EN, XTTS-v2 y ECAPA.
- `COQUI_TOS_AGREED=1` es obligatorio para cargar XTTS-v2.
- Pipeline caliente validado con FLEURS: ~29.8 s incluyendo carga inicial y
  ~2 s por etapa en régimen caliente.

### 1.4 Frontend existente

- Expo SDK 58, React Native 0.88, React 19.3.
- Identidad visual propia "Hilo": fondo crema, verde profundo, acentos durazno y
  lavanda; tipografía Manrope.
- Componentes reutilizables: marca, avatares, ondas de audio, tarjetas de
  traducción y tema visual.
- Limitación: no tiene selección real de archivos, llamadas HTTP, reproducción
  real ni descarga.

## 2. Arquitectura propuesta

```text
Navegador / Expo Web
        │  multipart/form-data + JSON
        ▼
FastAPI (Uvicorn, 1 worker)
  ├── validación de archivo y límites
  ├── normalización con ffmpeg → WAV
  ├── exclusión mutua (una inferencia a la vez)
  ├── ResultStore temporal con TTL
  └── importa process_audio()
        │
        ▼
Whisper Small → MarianMT base → XTTS-v2 → ECAPA
        │
        ▼
JSON con transcripción/traducción/tiempos
+ GET /api/v1/results/{id}/audio
```

### Decisiones

- **API REST FastAPI:** encaja con Python, expone OpenAPI y permite reutilizar el
  pipeline sin reimplementarlo.
- **Ejecución secuencial:** XTTS y los modelos comparten una GPU de 8 GB. Se usa
  un lock para evitar concurrencia insegura. Es suficiente para el prototipo.
- **Modelos precargados una vez:** `process_audio()` ya mantiene la caché; la API
  no debe instanciar modelos por solicitud.
- **Respuesta JSON + URL temporal:** evita incrustar audio binario en JSON.
- **Resultados con UUID y TTL:** no se usa base de datos. Cada resultado vive en
  un directorio aislado y expira (por defecto 1 hora).
- **Frontend Expo Web:** se conserva la tecnología y la identidad visual; se
  añade selección de archivo, estados reales y consumo de API.
- **Sin autenticación:** no hay cuentas en esta versión. La protección se basa en
  UUID no adivinables, TTL y ausencia de listado. Se documenta como limitación.

## 3. Componentes a reutilizar

- `src.pipeline.runner.process_audio`
- Configuraciones YAML de ASR, traducción y clonación.
- `src.voice_cloning.audio` para validación/preparación.
- Tema, marca, tipografía y patrones visuales de `deploy/frontend`.
- Pruebas unitarias y de contrato existentes (17 pruebas).

## 4. Componentes a implementar

### Backend (`deploy/backend/`)

- Aplicación FastAPI y configuración centralizada.
- Servicio de pipeline con lock y caché de modelos.
- Almacén temporal de resultados con expiración.
- Validación de MIME/extensión/tamaño/duración.
- Normalización de audio con ffmpeg.
- Endpoints `/health`, `/api/v1/status`, `/api/v1/translate`,
  `/api/v1/results/{id}/audio`.
- Manejo uniforme de errores y CORS restringido.
- Pruebas de API con modelos simulados.
- Dockerfile y Compose para despliegue.

### Frontend (`deploy/frontend/`)

- Pantalla funcional de traductor con estética de mensajería.
- Selector de audio real (Expo DocumentPicker).
- Reproductor real para audio original y generado.
- Validaciones de archivo, estados vacío/carga/error/éxito.
- Consumo real de la API, sin resultados simulados.
- Descarga del WAV generado.
- Estado del motor y aviso de primera carga.
- Configuración mediante `EXPO_PUBLIC_API_URL`.
- Pruebas de UI con Playwright y API simulada, más E2E real.

## 5. Comunicación frontend-backend

### Endpoints

| Método | Ruta | Uso |
|---|---|---|
| GET | `/health` | Liveness |
| GET | `/api/v1/status` | Estado sin cargar modelos |
| POST | `/api/v1/translate` | Subida y ejecución del pipeline |
| GET | `/api/v1/results/{id}/audio` | Descarga/reproducción del WAV |

### Contrato de `POST /api/v1/translate`

- `multipart/form-data` con campo `file`.
- Formatos: WAV, MP3, M4A, OGG, FLAC, WEBM.
- Tamaño máximo configurable (20 MB por defecto).
- Duración máxima configurable (120 s por defecto).
- Respuesta: `id`, `status`, `transcription_es`, `translation_en`,
  `speaker_similarity`, `audio` (URL, MIME, duración, sample rate), `timings`,
  `models`, `created_at`, `expires_at`.

### Errores

Códigos HTTP: 400, 413, 415, 422, 429, 500, 503. Formato uniforme:

```json
{
  "error": {
    "code": "invalid_audio",
    "message": "No se pudo leer el archivo de audio.",
    "request_id": "..."
  }
}
```

## 6. Flujo completo de procesamiento

1. El usuario selecciona un audio en el navegador.
2. El frontend valida extensión, MIME, tamaño y archivo no vacío.
3. Se envía `multipart/form-data` a `POST /api/v1/translate`.
4. El backend asigna un UUID, guarda el archivo con nombre seguro y comprueba
   límites mientras escribe.
5. ffmpeg normaliza el audio a WAV mono; `soundfile` valida duración y contenido.
6. El lock de inferencia se adquiere para ejecutar una sola petición a la vez.
7. `process_audio()` ejecuta Whisper → MarianMT → XTTS-v2 → ECAPA.
8. Se construye el resultado con URLs temporales, tiempos y metadatos.
9. El archivo original de subida se elimina; se conserva solo `output.wav`
   mientras el resultado esté vigente.
10. El frontend muestra transcripción, traducción, reproductor y descarga.
11. Un job de limpieza elimina resultados vencidos y sus audios.

## 7. Requisitos computacionales

- GPU NVIDIA recomendada con ≥ 8 GB VRAM (configuración validada).
- CPU alternativa posible pero muy lenta; XTTS puede tardar minutos.
- ~8 GB de RAM como mínimo; 16 GB recomendado.
- ~4 GB de pesos en caché (Whisper, MarianMT, XTTS, ECAPA).
- ffmpeg instalado en el host.
- Una sola instancia/worker recomendada por GPU.

## 8. Riesgos técnicos

| Riesgo | Mitigación |
|---|---|
| OOM de GPU | Una inferencia a la vez; límites de audio; errores 503 claros |
| Primera petición lenta | Aviso en UI; sin timeout agresivo; estado del motor |
| Archivos corruptos | ffprobe/ffmpeg + soundfile + validación de duración |
| Formatos de móvil (M4A/WEBM) | Normalización con ffmpeg |
| Licencia CPML de XTTS | `COQUI_TOS_AGREED=1` explícito; no redistribuir pesos |
| Exposición de resultados | UUID4, sin listado, TTL y limpieza |
| Concurrencia | Lock secuencial y estado `busy` |
| CORS excesivo | Lista explícita configurable por entorno |
| Despliegue gratuito insuficiente | Documentar GPU y alternativas de pago |

## 9. Estrategia de pruebas

### Rápidas (sin modelos)

- Salud y estado.
- Validación de archivo vacío, extensión/MIME inválido, tamaño excedido,
  audio corrupto y duración excedida.
- Errores del pipeline mapeados a códigos correctos.
- Respuesta correcta y acceso/expiración de audio.
- Pruebas unitarias y de contrato existentes.

### Integración real

- Descargar una muestra FLEURS `es_419` del split oficial `test`.
- Levantar FastAPI real.
- Enviar el audio por HTTP.
- Verificar transcripción, traducción, WAV generado, similitud ECAPA, descarga y
  reproducción.
- Documentar tiempos y limitaciones.

### Frontend

- Playwright con API interceptada: selector, validaciones, carga, resultados,
  error, descarga y estados.
- E2E real con backend y pipeline para confirmar que no hay respuestas ficticias.

## 10. Estrategia de despliegue

- **Desarrollo:** backend Uvicorn en `:8000`; Expo Web en `:8081`.
- **Producción:** build estático de Expo Web servido por Nginx; API FastAPI con
  Uvicorn/Gunicorn detrás de proxy. Alternativa: servir el build desde FastAPI.
- **Docker:** imagen backend basada en CUDA runtime + Python 3.11, con ffmpeg y
  `libsndfile`; frontend en Nginx. Compose con volúmenes de caché de modelos y
  `deploy/backend/.data`.
- **Modelos:** se descargan en el primer uso o se montan; no se incluyen en la
  imagen por licencia y tamaño.
- **Hosting:** no se hará despliegue público ni se generarán costos sin
  autorización. Se documentan proveedores GPU y la insuficiencia de capas
  gratuitas.

## 11. Criterios de aceptación y evidencia

Se considerará completado cuando exista:

- API real con validaciones y errores.
- Frontend conectado a la API real.
- Prueba HTTP real con FLEURS y audio WAV generado.
- Pruebas automatizadas verdes.
- Documentación de ejecución, API, despliegue y estado.
- Estructura de evidencias sin capturas inventadas.
