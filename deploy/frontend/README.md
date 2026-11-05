# Hilo — frontend web de traducción de voz

Aplicación **Expo Web / React Native Web** que consume la API FastAPI del
proyecto. Conserva la identidad visual de mensajería "Hilo", pero ahora ejecuta
el pipeline real ES→EN.

## Funcionalidades

- Selección real de audio (WAV, MP3, M4A, OGG, FLAC, WEBM).
- Validación de extensión, MIME, tamaño y duración.
- Estado del motor mediante `GET /api/v1/status`.
- Procesamiento real con aviso de primera carga y bloqueo de envíos duplicados.
- Visualización de transcripción en español y traducción al inglés.
- Reproductor real del WAV generado y descarga.
- Métricas de similitud ECAPA y tiempos del pipeline.
- Estados vacío, carga, error, reintento y éxito.
- Diseño responsive para móvil y escritorio.

## Requisitos

- Node.js 20+.
- Backend FastAPI en ejecución (ver `../backend/README` o
  `../../Docs/DEPLOYMENT_GUIDE.md`).
- Backend con GPU/licencia CPML para procesar audios reales.

## Ejecutar

```bash
cd deploy/frontend
npm install
npm run web
```

Abre `http://localhost:8081`. En desarrollo, la app deriva el backend en
`http://<host>:8000` cuando se sirve en el puerto 8081.

Si el backend está en otra máquina o usas Expo Go:

```bash
EXPO_PUBLIC_API_URL=http://<IP-LAN>:8000 npx expo start
```

También puedes copiar `.env.example` a `.env`.

## Build estático

```bash
npm run build:web
```

Genera `dist/`. En producción debe servirse con un proxy para `/api` y
`/health`; se incluye `nginx.conf` y un `Dockerfile` para ello.

## Pruebas

```bash
# UI con API interceptada (no requiere modelos)
npx playwright test e2e/translator.spec.js

# E2E real; requiere backend y pipeline disponibles
E2E_LIVE=1 npx playwright test e2e/live.spec.js
```

La muestra `e2e/fixtures/fleurs_es_419_test_0000.wav` es de FLEURS `es_419`,
split `test`, licencia CC BY 4.0. Ver `e2e/fixtures/README.md`.

## Configuración

| Variable | Uso |
|---|---|
| `EXPO_PUBLIC_API_URL` | URL del backend. Si se omite, se deriva del host |

## Limitaciones

- No hay grabación de micrófono; se selecciona un archivo.
- No hay autenticación ni cuentas.
- La reproducción nativa de Expo Go no se revalidó en dispositivo físico en esta
  entrega; el navegador sí fue validado.
- El pipeline es secuencial y no es de tiempo real.
