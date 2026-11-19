# Estado de despliegue y verificación actual

- **Fecha de actualización:** 2026-11-18
- **Rama:** `feature/web-deployment`
- **Entrenamiento del experimento NMT:** realizado en Google Colab con GPU.
- **Entorno revisado:** local, GPU NVIDIA RTX 5060 Laptop (8 151 MiB)
- **Despliegue público:** **no realizado**
- **Veredicto:** apto para demostración local controlada; **no apto todavía para exposición pública o producción**.

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
| Imagen Docker del frontend | **Completada históricamente** | `hilo-frontend:test` construida según la evidencia; no está presente en el host revisado |
| Configuración Docker Compose | **Validada** | `docker compose config` |
| Proxy Nginx + frontend Docker | **Validada** | UI en `:8088` consultó la API vía `/api` |
| Imagen Docker del backend | **Completada históricamente** | `hilo-backend:test` (~14.6 GB) construida y health/status validados; no está presente en el host revisado |
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

La imagen del frontend fue construida correctamente en la evidencia histórica.
La configuración de Compose fue validada nuevamente el 2026-11-18. El backend
puede ejecutarse localmente con `run.sh` y tiene definición de imagen GPU, pero
el host final debe contar con NVIDIA Container Toolkit y validar una inferencia
real dentro del contenedor.

### 4.1 Verificación vigente (2026-11-18)

| Validación | Resultado actual |
|---|---|
| Árbol Git | Limpio al iniciar la verificación; HEAD `95337f6` en `feature/web-deployment` |
| Backend, integración y API | **33 pruebas aprobadas** (`pytest`) |
| Calidad estática Python | **Ruff sin errores** |
| Interfaz web | **8 pruebas Playwright aprobadas** con API interceptada |
| Build web | `npm run build:web` generado correctamente |
| Compose | `docker compose config` válido |
| GPU del host | RTX 5060 Laptop detectada con 8 151 MiB |
| Imágenes locales | `hilo-backend:local` y `hilo-frontend:local` no están presentes |
| GPU en Docker | NVIDIA Container Toolkit/runtime no detectado; no se puede afirmar que Compose use GPU en este host |

Estas comprobaciones no sustituyen una prueba E2E real en el contenedor. La
evidencia anterior de E2E con modelos reales sigue descrita en
`Docs/END_TO_END_TEST_REPORT.md`; se ejecutó en el host, no como inferencia GPU
dentro de Docker.

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

### 5.1 Bloqueadores antes de exponer el sistema a Internet

1. Instalar y comprobar NVIDIA Container Toolkit en el host de destino; construir
   las imágenes y ejecutar una traducción real con GPU desde Docker Compose.
2. Implementar autenticación y rate limiting, o restringir el acceso mediante una
   red privada o un proxy autenticado. UUID y TTL no son autorización.
3. Configurar dominio, TLS/HTTPS, firewall y `CORS_ORIGINS` con el origen público
   exacto. El puerto del backend no debe quedar expuesto innecesariamente.
4. Confirmar la aceptación y compatibilidad de la licencia CPML de XTTS-v2 para
   el uso planificado.
5. Definir monitoreo, registros operativos, límites/cupos y una política de
   retención de audios antes de operar con usuarios externos.
6. Integrar y revisar la rama `feature/web-deployment` en una rama de release
   antes de publicar.

## 6. Evidencias

- `Docs/deploy_evidence/README.md`
- `Docs/deploy_evidence/screenshots/` (incluye `09_docker_nginx.png`)
- `Docs/deploy_evidence/artifacts/`
- `Docs/deploy_evidence/logs/`
- `Docs/END_TO_END_TEST_REPORT.md`
- `Docs/deploy_evidence/ARCHITECTURE.md`
