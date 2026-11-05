# Licencias de terceros

El código de este repositorio se distribuye bajo licencia MIT (`LICENSE`). Esa
licencia **no cubre automáticamente** los modelos, pesos ni datasets de terceros.

| Componente | Uso | Licencia / condición | Enlace |
|---|---|---|---|
| OpenAI Whisper (`openai/whisper-small`) | ASR | MIT | https://huggingface.co/openai/whisper-small |
| Helsinki-NLP MarianMT (`Helsinki-NLP/opus-mt-es-en`) | Traducción | CC BY 4.0 (verificar model card) | https://huggingface.co/Helsinki-NLP/opus-mt-es-en |
| Coqui XTTS-v2 (`coqui/XTTS-v2`) | Clonación de voz | **CPML — Coqui Public Model License**; restricciones de uso comercial y redistribución | https://huggingface.co/coqui/XTTS-v2 |
| SpeechBrain ECAPA (`speechbrain/spkrec-ecapa-voxceleb`) | Similitud de hablante | Apache 2.0 (verificar model card) | https://huggingface.co/speechbrain/spkrec-ecapa-voxceleb |
| FLEURS (`google/fleurs`) | Evaluación ASR/S2S | CC BY 4.0 (verificar dataset card) | https://huggingface.co/datasets/google/fleurs |
| OPUS-100 (`Helsinki-NLP/opus-100`) | Entrenamiento NMT | Verificar dataset card de OPUS-100 | https://huggingface.co/datasets/Helsinki-NLP/opus-100 |

## Implicación para XTTS-v2

XTTS-v2 se usa únicamente con fines académicos y de investigación. Antes de
redistribuir pesos, voces sintetizadas o un servicio basado en XTTS-v2, revise la
CPML y obtenga la autorización que corresponda. La licencia MIT de este
repositorio no autoriza por sí sola ese uso.

## Variables de entorno

La carga de XTTS-v2 exige aceptar la licencia:

```bash
export COQUI_TOS_AGREED=1
```

El proyecto no incluye pesos de XTTS-v2 en el repositorio.
