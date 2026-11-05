# Documentación de la API

- **Servicio:** Hilo — API de traducción de voz ES→EN
- **Versión:** 1.0.0
- **Framework:** FastAPI + Uvicorn
- **OpenAPI interactivo:** `http://localhost:8000/docs`
- **OpenAPI JSON:** `http://localhost:8000/openapi.json`
- **Prefijo de datos:** `/api/v1`

## Autenticación y alcance

Esta primera versión **no tiene autenticación ni cuentas**. Es un prototipo
académico para ejecución local o en una red controlada. Los resultados se
protegen mediante UUID4 no listados y expiración temporal, no mediante
autorización de usuario. No debe exponerse a Internet sin añadir autenticación,
rate limiting y aislamiento de sesiones.

## Límites por defecto

| Límite | Valor | Variable |
|---|---:|---|
| Tamaño máximo | 20 MB | `MAX_UPLOAD_MB` |
| Duración máxima | 120 s | `MAX_AUDIO_SECONDS` |
| Duración mínima | 0.5 s | `MIN_AUDIO_SECONDS` |
| Retención de resultados | 3600 s | `RESULT_TTL_SECONDS` |
| Formatos | WAV, MP3, M4A, OGG, FLAC, WEBM | — |
| Concurrencia | 1 inferencia secuencial | — |

---

## GET `/health`

Comprobación de liveness. No carga modelos.

### Respuesta 200

```json
{
  "status": "ok",
  "service": "hilo-translation-api",
  "version": "1.0.0"
}
```

---

## GET `/api/v1/status`

Estado de los componentes **sin cargar los modelos**. Es seguro para consultar
periódicamente.

### Respuesta 200

```json
{
  "status": "ok",
  "service": "hilo-translation-api",
  "version": "1.0.0",
  "timestamp": "2026-11-05T03:49:06Z",
  "pipeline": {
    "ready": true,
    "busy": false,
    "warm": true,
    "mode": "sequential",
    "device": "cuda",
    "gpu": {
      "available": true,
      "name": "NVIDIA GeForce RTX 5060 Laptop GPU",
      "total_memory_gb": 7.6
    },
    "xtts_license_accepted": true,
    "requests_total": 2,
    "completed_total": 2,
    "last_error_code": null,
    "last_completed_at": "2026-11-05T03:50:12Z",
    "models": {
      "asr": "openai/whisper-small",
      "translation": "Helsinki-NLP/opus-mt-es-en",
      "translation_checkpoint": "base",
      "tts": "coqui/XTTS-v2",
      "speaker_encoder": "speechbrain/spkrec-ecapa-voxceleb"
    }
  },
  "limits": {
    "max_upload_mb": 20,
    "max_audio_seconds": 120.0,
    "result_ttl_seconds": 3600
  },
  "capabilities": {
    "translation_direction": "es-en",
    "speaker_similarity": true,
    "background_jobs": false
  }
}
```

`status` vale `"degraded"` si `COQUI_TOS_AGREED` no es `1` o si XTTS no está
disponible. `pipeline.warm` indica que ya se completó al menos una inferencia en
esta instancia; no implica que los modelos estén cargados antes de la primera
petición.

---

## POST `/api/v1/translate`

Ejecuta el pipeline completo de forma **síncrona y secuencial**. La respuesta se
devuelve cuando terminan Whisper, MarianMT, XTTS-v2 y ECAPA.

### Request

- `Content-Type: multipart/form-data`
- Campo obligatorio: `file`
- Formatos: WAV, MP3, M4A, OGG, FLAC, WEBM.
- El nombre del archivo se descarta; el servidor usa un UUID y un nombre seguro.

```bash
curl -X POST http://localhost:8000/api/v1/translate \
  -F "file=@entrada_es.wav;type=audio/wav"
```

### Respuesta 200

```json
{
  "id": "b85cf9153bd14d408a3b1ada298a42d0",
  "status": "completed",
  "transcription_es": "Se recomienda enfáticamente a los viajeros que se informen sobre cualquier riesgo del clima extremo en el área que visitan, dado que ello puede afectar sus planes de viaje.",
  "translation_en": "Travelers are strongly advised to report any extreme weather risks in the area they visit, as this may affect their travel plans.",
  "speaker_similarity": 0.5345,
  "audio": {
    "url": "/api/v1/results/b85cf9153bd14d408a3b1ada298a42d0/audio",
    "download_url": "/api/v1/results/b85cf9153bd14d408a3b1ada298a42d0/audio?download=1",
    "mime_type": "audio/wav",
    "sample_rate": 24000,
    "duration_sec": 8.491,
    "filename": "hilo_b85cf915_en.wav"
  },
  "input": {
    "duration_sec": 12.84
  },
  "timings": {
    "preprocessing_sec": 0.0189,
    "asr_sec": 0.4713,
    "translation_sec": 0.1011,
    "xtts_sec": 1.5399,
    "speaker_evaluation_sec": 0.0235,
    "total_sec": 2.1562,
    "api_sec": 2.2347
  },
  "models": {
    "asr": "openai/whisper-small",
    "translation": "Helsinki-NLP/opus-mt-es-en",
    "translation_checkpoint": "base",
    "tts": "coqui/XTTS-v2",
    "speaker_encoder": "speechbrain/spkrec-ecapa-voxceleb"
  },
  "created_at": "2026-11-05T03:50:10Z",
  "expires_at": "2026-11-05T04:50:10Z"
}
```

### Notas de interpretación

- `speaker_similarity` es el coseno entre embeddings ECAPA. **No es un porcentaje
  de identidad** ni una garantía de clonación perfecta.
- `translation_checkpoint` debe ser `base`; el checkpoint controlado de 10 000
  pares no se usa por defecto.
- La operación no es en tiempo real. La primera petición carga los modelos y
  puede tardar bastante más que las siguientes.

### Errores

| HTTP | Código | Causa |
|---:|---|---|
| 413 | `file_too_large` | Supera `MAX_UPLOAD_MB` |
| 415 | `unsupported_media_type` | Extensión o MIME no permitido |
| 422 | `invalid_audio` | Audio vacío, corrupto, silencioso o sin voz |
| 422 | `audio_too_long` | Supera `MAX_AUDIO_SECONDS` |
| 422 | `validation_error` | Falta el campo `file` o el multipart es inválido |
| 500 | `pipeline_error` | Fallo interno del pipeline |
| 503 | `model_unavailable` | Licencia XTTS no aceptada, GPU sin memoria o modelo no disponible |
| 503 | `media_tool_unavailable` | ffmpeg/ffprobe no instalados |
| 500 | `internal_error` | Error no controlado |

Formato uniforme:

```json
{
  "error": {
    "code": "invalid_audio",
    "message": "El audio no contiene voz suficiente o su formato es inválido.",
    "request_id": "d4f6e59df1d54d1dbfabc17e20c7f1a2"
  }
}
```

No se devuelven rutas internas ni trazas. Las trazas completas quedan solo en el
log del servidor.

---

## GET `/api/v1/results/{result_id}/audio`

Recupera el WAV traducido mientras el resultado siga vigente. Admite peticiones
Range para reproducción en navegador.

### Parámetros

| Nombre | Ubicación | Descripción |
|---|---|---|
| `result_id` | path | UUID hexadecimal de 32 caracteres |
| `download` | query | `1`/`true` fuerza `Content-Disposition: attachment` |

### Respuesta 200

- `Content-Type: audio/wav`
- `Content-Disposition: inline` o `attachment`
- `Accept-Ranges: bytes`
- Cuerpo binario WAV PCM 16-bit mono 24 kHz.

```bash
# Reproducir / descargar
curl -OJ "http://localhost:8000/api/v1/results/<id>/audio?download=1"
```

### Errores

| HTTP | Código | Causa |
|---:|---|---|
| 404 | `result_not_found` | UUID inexistente, archivo eliminado o TTL vencido |

La URL es impredecible (UUID4) y no existe un endpoint para listar resultados.
Los resultados se eliminan al expirar y al iniciar/limpiar el servidor.

---

## CORS

Solo se permiten los orígenes configurados en `CORS_ORIGINS`, separados por
comas. En desarrollo se incluyen `localhost`/`127.0.0.1` en los puertos 8081 y
19006. Para un teléfono en la misma red, agrega el origen LAN exacto. No se
habilita `*` por defecto.

## Privacidad y retención

- El archivo subido se normaliza y el original se elimina tras el procesamiento.
- El servidor conserva únicamente `output.wav` y `result.json` mientras el
  resultado está vigente.
- No se registra el contenido de audio ni las transcripciones en los logs.
- No hay base de datos ni almacenamiento permanente.
