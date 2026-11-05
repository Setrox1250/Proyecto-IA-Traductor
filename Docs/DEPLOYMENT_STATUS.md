# Estado de despliegue

- **Fecha:** 2026-11-05
- **Rama:** `feature/web-deployment`
- **Entorno:** local, GPU NVIDIA RTX 5060 Laptop (7.6 GiB)
- **Despliegue público:** **no realizado**

## 1. Resumen por etapa

| Etapa | Estado | Evidencia |
|---|---|---|
| Implementación local del backend | **Completada** | API FastAPI + pruebas |
| Implementación local del frontend | **Completada** | Pantalla funcional + Playwright |
| Integración frontend ↔ backend | **Completada** | E2E real con FLEURS |
| Ejecución real del pipeline | **Completada** | Transcripción, traducción y WAV |
| Pruebas de archivos inválidos | **Completada** | 33 pruebas Python |
| Pruebas de interfaz | **Completada** | 8 pruebas Playwright |
| Build estático web | **Completada** | `npm run build:web` |
| Imagen Docker del frontend | **Completada** | `hilo-frontend:test` construida |
| Configuración Docker Compose | **Validada** | `docker compose config` |
| Proxy Nginx + frontend Docker | **Validada** | UI en `:8088` consultó la API vía `/api` |
| Imagen Docker del backend | **Completada** | `hilo-backend:test` (~14.6 GB) construida; health/status validados |
| Despliegue público | **Pendiente** | Requiere autorización, GPU y presupuesto |
| Autenticación / cuentas | **Fuera de alcance** | No implementado |
| Grabación de micrófono | **Fuera de alcance v1** | Selección de archivo disponible |

## 2. Lo que está demostrado

- El backend arranca y responde `/health` y `/api/v1/status`.
- El estado se obtiene sin cargar los modelos.
- El endpoint `/api/v1/translate` valida y ejecuta el pipeline existente.
- Se reutiliza `src.pipeline.runner.process_audio`, sin duplicar modelos.
- Whisper Small transcribe; MarianMT base traduce; XTTS-v2 genera el WAV;
  ECAPA calcula similitud.
- El frontend web se comunica con la API real y muestra estados de carga, error,
  transcripción, traducción, reproducción y descarga.
- El audio original y los resultados se eliminan según la política TTL.
- La prueba E2E real se ejecutó y pasó.

## 3. Lo que no está demostrado

- **No hay URL pública.** No se desplegó en Vercel, Render, Railway, AWS, GCP,
  Azure, RunPod ni ningún otro proveedor.
- **No hay autenticación.** Un UUID no adivinable y el TTL no equivalen a un
  sistema de autorización.
- **No se validó Expo Go nativo** en un dispositivo físico en esta entrega; el
  objetivo funcional y las pruebas se realizaron en navegador (móvil y escritorio).
- **No se implementó grabación desde micrófono**; se selecciona un archivo.
- **No se ejecutó inferencia GPU dentro de Docker.** La imagen backend se construyó
  y el contenedor respondió health/status/UI a través de Nginx en CPU; la
  inferencia real se validó en el host con GPU.
- **No hay CI/CD, monitoreo, rate limiting ni cuotas.**
- No se modificaron las métricas históricas ni las evidencias oficiales.

## 4. Preparación para despliegue

Existe:

- `deploy/backend/Dockerfile`
- `deploy/frontend/Dockerfile`
- `deploy/frontend/nginx.conf`
- `deploy/docker-compose.yml`
- `deploy/backend/.env.example`
- `deploy/frontend/.env.example`
- `requirements/web.txt`
- Script `deploy/backend/run.sh`

La imagen del frontend fue construida correctamente. Compose fue validado. El
backend puede ejecutarse localmente con `run.sh` y está listo para una imagen GPU
en un host que cumpla los requisitos.

## 5. Requisitos para publicación

1. Host con GPU NVIDIA de ≥ 8 GB VRAM (o aceptar latencia CPU).
2. Aceptación explícita de CPML y configuración `COQUI_TOS_AGREED=1`.
3. Volumen persistente para cachés de modelos (Whisper, MarianMT, XTTS, ECAPA).
4. HTTPS y dominio.
5. Autenticación o, como mínimo, protección de acceso y rate limiting antes de
   exponer a Internet.
6. Configurar `CORS_ORIGINS` con el dominio exacto.
7. Definir retención y limpieza; el valor por defecto es 1 hora.
8. Revisar costos del proveedor GPU y la licencia CPML.
9. Autorización explícita para generar costos y publicar.

## 6. Evidencias

- `Docs/deploy_evidence/README.md`
- `Docs/deploy_evidence/screenshots/` (incluye `09_docker_nginx.png`)
- `Docs/deploy_evidence/artifacts/`
- `Docs/deploy_evidence/logs/`
- `Docs/END_TO_END_TEST_REPORT.md`
- `Docs/deploy_evidence/ARCHITECTURE.md`
