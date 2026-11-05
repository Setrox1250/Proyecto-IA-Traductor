# Guía de despliegue

- **Sistema:** Hilo — traducción de audio ES→EN con clonación de voz
- **Frontend:** Expo SDK 58 / React Native Web
- **Backend:** FastAPI + Uvicorn
- **Pipeline:** Whisper Small → MarianMT base → XTTS-v2 → ECAPA-TDNN
- **Estado:** preparado y probado localmente; **sin despliegue público**

## 1. Arquitectura de despliegue

```text
Navegador
   │
   ├── HTTPS ──> Nginx / CDN
   │               ├── /            → build estático Expo Web
   │               ├── /api/*       → proxy a FastAPI
   │               └── /health      → proxy a FastAPI
   │
   └── API ────> FastAPI (1 worker, puerto 8000)
                    └── GPU NVIDIA
                         ├── Whisper Small
                         ├── MarianMT base
                         ├── XTTS-v2
                         └── ECAPA-TDNN
```

En desarrollo se ejecutan dos servidores: Expo Web en `:8081` y FastAPI en
`:8000`. En producción se recomienda servir el build estático con Nginx y
proxificar `/api` y `/health` al backend en la misma origen.

## 2. Requisitos

### Hardware

| Recurso | Mínimo | Recomendado |
|---|---|---|
| GPU NVIDIA | 8 GB VRAM | 8–12 GB VRAM |
| RAM | 8 GB | 16 GB |
| Disco | 20 GB libres | 35 GB+ (imagen CUDA, pesos y cachés) |
| CPU | 4 núcleos | 8 núcleos |

La ejecución validada usó una RTX 5060 Laptop GPU de 8 GB y 14 GB de RAM. XTTS
también puede ejecutarse en CPU, pero con latencias muy altas. No es un servicio
de tiempo real.

### Software

- Python 3.11.
- CUDA 12.8 y driver NVIDIA compatible (entorno validado).
- PyTorch 2.8.0.
- ffmpeg y ffprobe instalados (`ffmpeg -version`).
- Node.js 20+ (validado con Node 26 y Node 22 en Docker).
- npm.
- Opcional: Docker 29+ y Docker Compose.

### Licencia

XTTS-v2/Coqui usa **CPML**, no MIT. Debes aceptar la licencia antes de cargar el
modelo:

```bash
export COQUI_TOS_AGREED=1
```

Revisa `THIRD_PARTY_LICENSES.md` y la model card:
https://huggingface.co/coqui/XTTS-v2

## 3. Variables de entorno

Copia `deploy/backend/.env.example` a `deploy/backend/.env` y ajusta:

```bash
cd deploy/backend
cp .env.example .env
```

| Variable | Default | Descripción |
|---|---|---|
| `COQUI_TOS_AGREED` | `0` | `1` solo si aceptas la licencia CPML |
| `HOST` | `0.0.0.0` | Interfaz del backend |
| `PORT` | `8000` | Puerto del backend |
| `CORS_ORIGINS` | localhost:8081,… | Orígenes permitidos, separados por comas |
| `MAX_UPLOAD_MB` | `20` | Tamaño máximo de subida |
| `MAX_AUDIO_SECONDS` | `120` | Duración máxima |
| `MIN_AUDIO_SECONDS` | `0.5` | Duración mínima |
| `RESULT_DIR` | `.data/results` | Directorio de resultados temporales |
| `RESULT_TTL_SECONDS` | `3600` | Retención de resultados |
| `CLEANUP_INTERVAL_SECONDS` | `300` | Frecuencia de limpieza |
| `FFMPEG_BIN` / `FFPROBE_BIN` | `ffmpeg` / `ffprobe` | Binarios del sistema |
| `FFMPEG_TIMEOUT_SECONDS` | `60` | Tiempo máximo por operación de audio |
| `LOG_LEVEL` | `INFO` | Nivel de logging |

Frontend: copia `deploy/frontend/.env.example` a `.env` solo si necesitas fijar
la URL del backend:

```bash
cd deploy/frontend
cp .env.example .env
```

| Variable | Default | Descripción |
|---|---|---|
| `EXPO_PUBLIC_API_URL` | derivada | URL pública del backend |

La app deriva automáticamente `http://<host>:8000` si se sirve en `:8081` y usa
mismo origen en un build estático servido por Nginx. Para Expo Go en un teléfono
físico debes definir la IP LAN:

```bash
EXPO_PUBLIC_API_URL=http://192.168.1.25:8000 npx expo start
```

## 4. Instalación local

### 4.1 Backend

Se recomienda reutilizar el entorno `.venv-xtts` del proyecto. Crear uno nuevo
implica descargar PyTorch, Coqui TTS y los demás pesos.

```bash
cd /ruta/al/repo
python3.11 -m venv .venv-xtts
source .venv-xtts/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements/web.txt
```

`requirements/web.txt` incluye ASR, traducción, clonación de voz, FastAPI,
Uvicorn y `python-multipart`.

### 4.2 Modelos

Los pesos se descargan automáticamente desde Hugging Face/Coqui en la primera
ejecución:

- `openai/whisper-small`
- `Helsinki-NLP/opus-mt-es-en`
- `coqui/XTTS-v2`
- `speechbrain/spkrec-ecapa-voxceleb`

No se versionan en el repositorio. Asegúrate de tener espacio y conexión. La
primera petición puede tardar decenas de segundos; las siguientes usan la caché
en memoria.

### 4.3 Arrancar backend

```bash
cd deploy/backend
cp .env.example .env          # ajusta COQUI_TOS_AGREED=1 si aceptas CPML
./run.sh
```

Equivalente manual:

```bash
cd deploy/backend
COQUI_TOS_AGREED=1 ../../.venv-xtts/bin/python -m uvicorn app.main:app \
  --host 0.0.0.0 --port 8000 --workers 1
```

Verifica:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/status
```

### 4.4 Arrancar frontend web

```bash
cd deploy/frontend
npm install
npm run web
```

Abre `http://localhost:8081`. El cliente derivará el backend en
`http://localhost:8000`. Para usar un dispositivo físico en la misma red:

```bash
EXPO_PUBLIC_API_URL=http://<IP-LAN>:8000 npm run web
```

Si usas Expo Go:

```bash
cd deploy/frontend
EXPO_PUBLIC_API_URL=http://<IP-LAN>:8000 npx expo start
```

La versión funcional fue validada en navegador (móvil y escritorio). La
selección/reproducción nativa en Expo Go no se revalidó en un dispositivo físico
en esta entrega; se documenta como limitación.

## 5. Pruebas

```bash
# Backend + unitarias existentes (sin cargar modelos)
.venv-xtts/bin/python -m pytest tests/unit tests/integration tests/api -q

# Frontend con API interceptada
cd deploy/frontend
npx playwright test e2e/translator.spec.js

# E2E real, requiere backend + GPU + licencia
cd deploy/frontend
E2E_LIVE=1 npx playwright test e2e/live.spec.js
```

El E2E real usa `deploy/frontend/e2e/fixtures/fleurs_es_419_test_0000.wav` y
verifica transcripción, traducción, similitud ECAPA y descarga del WAV.

## 6. Build estático

```bash
cd deploy/frontend
npm run build:web
# salida: deploy/frontend/dist/
```

El build se sirvió correctamente y se validó su construcción. Para producción,
sirve `dist/` con Nginx y configura el proxy de `/api` y `/health`. El archivo
`deploy/frontend/nginx.conf` ya contiene esa configuración.

## 7. Docker

### 7.1 Requisitos

- Docker con soporte NVIDIA Container Toolkit.
- `docker compose`.
- Suficiente disco para la imagen CUDA y los pesos. La imagen backend local de
  prueba ocupó ~14.6 GB; reserva 25–35 GB para imagen, pesos y cachés.
- Crear `deploy/backend/.env` antes de levantar Compose.

### 7.2 Construir y levantar

```bash
cd deploy
cp backend/.env.example backend/.env
# edita COQUI_TOS_AGREED=1 si aceptas CPML
docker compose up --build
```

Servicios:

- Frontend: `http://localhost:8088`
- Backend: `http://localhost:8000`
- Nota: Nginx proxifica `/api` y `/health`, por lo que el navegador usa el mismo
  origen del frontend.

### 7.3 Estado de verificación Docker

- `deploy/frontend/Dockerfile` fue **construido correctamente** con la etiqueta
  `hilo-frontend:test`.
- `deploy/backend/Dockerfile` fue **construido correctamente** con la etiqueta
  `hilo-backend:test` (base PyTorch CUDA 12.8, ~14.6 GB). El contenedor respondió
  `/health` y `/api/v1/status` en CPU.
- `deploy/docker-compose.yml` fue validado con `docker compose config`.
- Se levantó una red Docker de prueba con backend + frontend Nginx. La UI en
  `:8088` consultó la API a través del proxy `/api` y `/health`.
- **No se ejecutó la inferencia GPU dentro del contenedor** en esta validación;
  el pipeline real se probó en el host con GPU. La imagen está construida, pero
  el host final debe validar CUDA y montar las cachés de modelos.
- No se levantó un despliegue público ni se generaron costos.

### 7.4 Volúmenes de modelos

Compose usa volúmenes nombrados:

- `hilo_hf_cache` → `/root/.cache/huggingface`
- `hilo_tts_cache` → `/root/.local/share/tts`
- `hilo_results` → `/app/deploy/backend/.data`

La primera ejecución descargará los pesos. Para reutilizar cachés existentes,
monta tus directorios locales en lugar de los volúmenes nombrados.

## 8. Consideraciones de GPU y hosting

### Por qué no sirve un hosting gratuito típico

XTTS-v2 y Whisper Small requieren GPU y varios GB de VRAM. Plataformas gratuitas
como Vercel, Netlify, Render Free o Railway Free no ofrecen GPU persistente ni
8 GB de VRAM, y los límites de ejecución son incompatibles con una inferencia de
2–30 segundos y cargas de modelos de varios GB. No se debe presentar este
proyecto como desplegado en esas plataformas.

### Alternativas viables

| Opción | Uso | Nota |
|---|---|---|
| Servidor propio con RTX 8 GB+ | Demo académica / interno | Opción validada localmente |
| RunPod / Vast.ai GPU | Alquiler por hora | Revisar costos y CPML |
| AWS g5 / GCP L4 / Azure NC | Producción con GPU | Requiere presupuesto |
| Hugging Face Inference Endpoints | Solo si el modelo y licencia lo permiten | XTTS/CPML requiere revisión |
| CPU | Pruebas funcionales | Muy lento; no apto para demo interactiva |

No se realizó ningún despliegue público ni se asumieron costos.

## 9. Consideraciones de seguridad

- No publiques el backend sin autenticación y rate limiting.
- Restringe CORS al dominio exacto del frontend.
- Usa HTTPS en producción.
- No montes el repositorio completo en el contenedor de producción.
- No incluyas `.env`, claves, pesos ni audios de usuarios en la imagen.
- Limpia `RESULT_DIR` con la política TTL.
- Revisa la licencia CPML antes de redistribuir pesos o un servicio basado en
  XTTS-v2.
- Los UUID de resultado no sustituyen un sistema de autorización.

## 10. Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| `503 model_unavailable` | `COQUI_TOS_AGREED` distinto de `1` | Expórtalo y reinicia |
| Primer request muy lento | Carga inicial de modelos | Espera; el estado pasa a `warm` |
| `503 media_tool_unavailable` | ffmpeg/ffprobe ausentes | `sudo apt install ffmpeg` |
| Error CORS en navegador | Origen no incluido | Ajusta `CORS_ORIGINS` |
| No conecta desde el teléfono | `localhost` apunta al teléfono | Usa la IP LAN del backend |
| `invalid_audio` | Formato corrupto/silencioso | Prueba con WAV PCM válido |
| OOM de GPU | Audio largo u otra inferencia | Usa un audio más corto; una sola instancia |
| El frontend no encuentra la API | Build estático sin proxy | Configura Nginx o `EXPO_PUBLIC_API_URL` |
| `result_not_found` | TTL vencido | Repite la traducción |

## 11. Limitaciones de esta entrega

- No hay despliegue público.
- No hay autenticación, cuentas ni cuotas por usuario.
- No hay procesamiento asíncrono ni cola persistente; las peticiones esperan al
  lock secuencial.
- No hay grabación desde micrófono en la interfaz web; se usa selección de
  archivo.
- La descarga en navegador fue validada; en Expo Go nativo se comparte la URL.
- La inferencia GPU dentro de Docker no se declara verificada; el contenedor se
  validó en CPU para health/status y la UI vía Nginx.
