# Modelos

Los pesos no se versionan en este repositorio. Se descargan con `scripts/download_models.py`.

## Modelos usados

| Rol | Identificador | Versión / notas |
|---|---|---|
| ASR | `openai/whisper-small` | Pesos Hugging Face; inferencia en español |
| NMT base | `Helsinki-NLP/opus-mt-es-en` | Modelo usado por el pipeline |
| NMT ajustado | `models/checkpoints/controlled_10k` | Experimento de 10 000 pares; BLEU/chrF inferiores al base |
| TTS / clonación | `coqui/XTTS-v2` vía `tts_models/multilingual/multi-dataset/xtts_v2` | Requiere `COQUI_TOS_AGREED=1`; licencia CPML |
| Speaker encoder | `speechbrain/spkrec-ecapa-voxceleb` | Similitud coseno ECAPA-TDNN |

## Directorios

- `checkpoints/` — checkpoints de entrenamiento (ignorados por Git)
- `fine_tuned/` — modelos ajustados (ignorados por Git)

## Licencias

El código es MIT, pero los pesos de XTTS-v2/Coqui no lo son. Consulte `README.md` y los términos de cada modelo antes de redistribuirlos.
