# Arquitectura general del sistema web

```mermaid
flowchart LR
    U[Usuario<br/>navegador móvil o escritorio] -->|selecciona audio| F[Frontend Expo Web<br/>deploy/frontend]
    F -->|multipart/form-data| A[FastAPI<br/>deploy/backend]
    A --> V[Validación de extensión, MIME,<br/>tamaño y duración]
    V --> N[Normalización ffmpeg<br/>WAV mono]
    N --> L{Lock de inferencia<br/>secuencial}
    L --> W[Whisper Small<br/>ASR ES]
    W --> M[MarianMT base<br/>ES → EN]
    M --> X[XTTS-v2<br/>voz EN con referencia]
    X --> E[ECAPA-TDNN<br/>similitud vocal]
    E --> R[ResultStore temporal<br/>UUID + TTL]
    R -->|JSON con transcripción,<br/>traducción y URL| F
    F -->|GET /api/v1/results/{id}/audio| R
    R -->|WAV| U

    subgraph GPU local
        W
        M
        X
        E
    end
```

## Decisiones representadas

- El frontend y la API están desacoplados por HTTP.
- El backend no reimplementa el pipeline: importa `src.pipeline.runner.process_audio`.
- Los modelos se cargan una vez y se comparten entre peticiones; el lock impide
  inferencias simultáneas sobre la GPU.
- El audio generado se sirve por una URL temporal con UUID y expiración.
- No hay base de datos ni autenticación en esta primera versión.
- Nginx puede servir el build estático y actuar como proxy de `/api` y `/health`.
