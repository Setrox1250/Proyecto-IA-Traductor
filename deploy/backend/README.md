# Backend Hilo — API FastAPI

Capa de integración que expone el pipeline existente
`src.pipeline.runner.process_audio` (Whisper Small → MarianMT base → XTTS-v2 →
ECAPA).

## Inicio rápido

```bash
cd deploy/backend
cp .env.example .env          # COQUI_TOS_AGREED=1 si aceptas CPML
./run.sh
```

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Health: `GET /health`
- Estado: `GET /api/v1/status`
- Traducción: `POST /api/v1/translate` (multipart, campo `file`)
- Audio: `GET /api/v1/results/{id}/audio`

El backend usa un solo worker y serializa las inferencias con un lock. Los
resultados se guardan temporalmente y expiran según `RESULT_TTL_SECONDS`.
No hay base de datos ni autenticación en esta versión.

## Pruebas

Desde la raíz del repositorio:

```bash
.venv-xtts/bin/python -m pytest tests/api -q
```

Detalle completo en `Docs/API_DOCUMENTATION.md` y
`Docs/DEPLOYMENT_GUIDE.md`.
