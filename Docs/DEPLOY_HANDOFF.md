# Handoff de despliegue y dirección del producto

**Proyecto:** Traductor de mensajes de audio ES→EN con voz condicionada por la referencia.  
**Estado:** código y validaciones locales preparados; despliegue público pendiente.  
**Actualizado:** 2026-11-18.

## 1. Qué se debe desplegar

No es una aplicación de solo frontend. Es una aplicación web compuesta por:

```text
Navegador (Expo Web) → HTTPS / proxy → API FastAPI → GPU
                                              ↓
                 Whisper-small → MarianMT → XTTS-v2 → ECAPA
```

El frontend recibe un audio y muestra los resultados. El backend ejecuta la
inferencia; por eso necesita acceso a los pesos de los modelos y, para una
experiencia de usuario aceptable, a una GPU NVIDIA.

## 2. Dirección funcional recomendada

La dirección adecuada es una **aplicación web de tarea única**: un traductor de
mensajes de voz ES→EN. No debe presentarse como chat en tiempo real, red social,
servicio de mensajería ni clonador de identidad vocal.

### MVP que debe conservarse

1. Cargar un audio en español.
2. Validar formato, tamaño, duración y contenido audible.
3. Procesar una solicitud a la vez.
4. Mostrar estado y aviso de primera carga.
5. Mostrar transcripción ES y traducción EN.
6. Reproducir y descargar el WAV generado en inglés.
7. Mostrar tiempo y similitud ECAPA como métrica técnica, no como porcentaje de
   identidad.
8. Eliminar los resultados automáticamente según el TTL.

La interfaz actual ya cubre este MVP. Se recomienda que su comunicación visual
sea la de un **traductor de audio**: carga → procesamiento → resultado. Una UI
tipo chat puede sugerir conversación instantánea, concurrencia o streaming, que
no forman parte de la capacidad actual del pipeline.

### Fuera de alcance para el primer deploy

- Conversación en tiempo real y streaming.
- Grabación desde micrófono.
- Cuentas, historial permanente y mensajería entre usuarios.
- Procesamiento concurrente en una GPU de 8 GB.
- Afirmaciones de identidad, emoción o naturalidad vocal garantizada.

## 3. Entornos: no confundir entrenamiento e inferencia

| Actividad | Entorno |
|---|---|
| Entrenamiento del experimento NMT | Google Colab con GPU |
| Desarrollo, pruebas e integración web | Equipo local con RTX NVIDIA |
| Evaluación end-to-end | Equipo local con RTX NVIDIA |
| Deploy | Host con GPU NVIDIA persistente o GPU local expuesta de forma controlada |

El hecho de que el entrenamiento esté terminado no elimina el cómputo de
inferencia: Whisper, MarianMT, XTTS-v2 y ECAPA se ejecutan para cada audio que
suba un usuario.

## 4. Despliegue recomendado

### Opción prioritaria: una instancia GPU persistente

Usar una VM o Pod con GPU NVIDIA y Docker Compose. La arquitectura mínima es:

```text
Internet
  ↓ HTTPS
Caddy o Nginx
  ├─ frontend Expo Web estático
  └─ /api → backend FastAPI interno con GPU
```

- GPU: 8 GB de VRAM es el mínimo validado; 16 GB ofrece margen operativo.
- RAM: 16 GB recomendados.
- Disco: reservar al menos 35 GB para la imagen CUDA, dependencias y cachés.
- Mantener una instancia persistente para evitar descargas y cargas frías de
  modelos en cada solicitud.
- Exponer públicamente solo el proxy HTTPS. El backend debe permanecer en la red
  interna de Docker.

Esta alternativa se ajusta al diseño actual: FastAPI mantiene modelos en memoria
y serializa inferencias para proteger la GPU.

### Alternativa para demo académica

Usar la RTX local como host de inferencia y publicar temporalmente mediante un
túnel protegido (por ejemplo, con control de acceso). El equipo debe permanecer
encendido y no debe considerarse producción.

### Render y servicios CPU

Render, Cloudflare Pages, Vercel o Netlify son adecuados para **el frontend
estático**. No se recomienda alojar el backend completo en un servicio CPU: XTTS
es costoso, la imagen es pesada y la latencia/carga de modelos no es apropiada
para una interacción web. Si el frontend se publica separado del backend GPU,
definir en el build:

```bash
EXPO_PUBLIC_API_URL=https://api.ejemplo.com
```

y configurar `CORS_ORIGINS` con el dominio exacto del frontend.

## 5. Requisitos técnicos previos

1. GPU NVIDIA con driver compatible.
2. Docker y Docker Compose.
3. NVIDIA Container Toolkit operativo. Verificar que un contenedor vea la GPU
   antes de construir la aplicación.
4. Dominio, DNS y HTTPS si se publica fuera de una red privada.
5. Volúmenes persistentes para cachés de Hugging Face, Coqui TTS y resultados.
6. Aceptación explícita de la licencia CPML de XTTS-v2.

Variables mínimas del backend:

```env
COQUI_TOS_AGREED=1
CORS_ORIGINS=https://app.ejemplo.com
RESULT_TTL_SECONDS=3600
MAX_UPLOAD_MB=20
MAX_AUDIO_SECONDS=120
```

No subir `.env`, pesos, audios de usuarios ni resultados a Git.

## 6. Ajustes obligatorios antes de hacerlo público

- No exponer directamente el puerto `8000` del backend; usar el proxy como única
  entrada pública.
- Configurar TLS/HTTPS y firewall.
- Implementar autenticación y rate limiting, o restringir la aplicación a una
  red privada/proxy autenticado.
- Revisar la política de retención de los audios antes de operar con usuarios.
- Configurar logs, monitoreo básico y límites de gasto de GPU.
- Validar una traducción real dentro del contenedor con GPU. Un `/health` exitoso
  no prueba que CUDA, XTTS y el pipeline completo funcionen.

## 7. Secuencia de despliegue

1. Integrar el código aprobado en una rama de release y etiquetar la versión.
2. Instalar NVIDIA Container Toolkit en el host y comprobar CUDA desde Docker.
3. Crear `deploy/backend/.env` desde `.env.example`; aceptar CPML solo si
   corresponde al uso autorizado.
4. Construir las imágenes y levantar los servicios.
5. Esperar la descarga inicial de pesos en los volúmenes persistentes.
6. Comprobar `/health` y `/api/v1/status`.
7. Ejecutar una traducción real con el WAV de prueba FLEURS.
8. Verificar transcripción, traducción, audio, descarga, expiración TTL y uso de
   GPU.
9. Habilitar el dominio y HTTPS solo tras esas verificaciones.

## 8. Criterios de aceptación

El deploy se considera listo cuando:

- La GPU es visible desde el contenedor.
- `/api/v1/status` indica GPU disponible y la licencia XTTS aceptada.
- Una solicitud real genera el WAV de salida correctamente.
- El frontend consume la API mediante HTTPS y el proxy, no por el puerto interno.
- Los resultados expiran y se eliminan de acuerdo con el TTL.
- El servicio no queda abierto sin control de acceso o limitación de tráfico.

## 9. Fuentes del repositorio

- `Docs/DEPLOYMENT_STATUS.md`
- `Docs/DEPLOYMENT_GUIDE.md`
- `Docs/END_TO_END_TEST_REPORT.md`
- `deploy/docker-compose.yml`
- `deploy/backend/.env.example`
- `deploy/frontend/nginx.conf`
