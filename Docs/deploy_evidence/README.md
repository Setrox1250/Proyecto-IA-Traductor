# Evidencias de implementación y despliegue

Esta carpeta conserva evidencias **reales** de la implementación local. No
contiene capturas simuladas ni resultados inventados.

## Capturas incluidas

| # | Evidencia | Archivo | Estado |
|---|---|---|---|
| 1 | Arquitectura general | `ARCHITECTURE.md` (diagrama Mermaid) | Incluida |
| 2 | Pantalla principal | `screenshots/01_pantalla_principal.png` | Incluida |
| 3 | Selección de audio | `screenshots/02_seleccion_audio.png` | Incluida |
| 4 | Procesamiento en curso | `screenshots/03_procesamiento.png` | Incluida |
| 5 | Transcripción generada | `screenshots/04_resultado_escritorio.png` | Incluida |
| 6 | Traducción generada | `screenshots/04_resultado_escritorio.png` | Incluida |
| 7 | Reproducción del audio traducido | `screenshots/05_reproduccion_audio.png` | Incluida |
| 8 | Descarga del audio | `artifacts/final_api_output.wav` + `logs/playwright-live.log` | Descarga verificada; captura de bandeja pendiente |
| 9 | Documentación OpenAPI | `screenshots/07_openapi.png` | Incluida |
| 10 | Ejecución del backend | `logs/backend_runtime.log` | Log real incluido; captura de terminal pendiente |
| 11 | Ejecución del frontend | `screenshots/08_inicio_movil.png` + `screenshots/09_docker_nginx.png` | Incluida |
| 12 | Prueba completa E2E | `logs/playwright-live.log` + `artifacts/final_api_result.json` + `artifacts/final_api_output.wav` | Incluida |

## Artefactos

- `artifacts/fleurs_es_419_test_0000.wav`: audio FLEURS real usado en la prueba.
- `artifacts/final_api_result.json`: respuesta real de `POST /api/v1/translate`.
- `artifacts/final_api_output.wav`: WAV generado por XTTS-v2 y descargado desde la API.
- `logs/pytest.log`: 33 pruebas Python aprobadas.
- `logs/playwright-ui.log`: 8 pruebas de interfaz aprobadas con API interceptada.
- `logs/playwright-live.log`: prueba E2E real con backend, pipeline y descarga.
- `logs/backend_runtime.log`: salida real del servidor Uvicorn durante las pruebas.
- `screenshots/09_docker_nginx.png`: UI servida por Nginx en Docker, consultando la API por proxy.

## Capturas que deben completarse para el informe

1. **Descarga del audio:** capturar la bandeja de descargas del navegador con el
   archivo `hilo_<id>_en.wav`, o una captura de la confirmación nativa. La
   descarga ya fue verificada por Playwright y el WAV está en `artifacts/`.
2. **Ejecución del backend:** captura de terminal con
   `deploy/backend/run.sh` y las líneas de inicio de Uvicorn. El log real ya está
   incluido.
3. **Ejecución del frontend:** captura de terminal con `npm run web` y el QR/URL
   de Expo. La captura actual muestra la app en ejecución.

## Cómo reproducir las capturas

```bash
# Terminal 1: backend
cd deploy/backend
cp .env.example .env
./run.sh

# Terminal 2: frontend
cd deploy/frontend
npm install
npx expo start --web

# Pruebas
cd deploy/frontend
npx playwright test e2e/translator.spec.js
E2E_LIVE=1 npx playwright test e2e/live.spec.js
```

Las capturas de resultado se obtuvieron con
`deploy/frontend/e2e/fixtures/fleurs_es_419_test_0000.wav`, un audio FLEURS
`es_419` del split oficial `test` (CC BY 4.0). No se usaron audios personales.
