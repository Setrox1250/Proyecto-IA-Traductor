# IA-Proyecto

Proyecto de IA: traductor con síntesis de voz y clonación de voz.

## Estructura

- `configs/` — configuraciones YAML
- `data/` — datos crudos, procesados y externos
- `models/` — checkpoints y modelos fine-tuned
- `notebooks/` — notebooks por módulo
- `src/` — código fuente por módulo
- `evaluation/` — scripts y resultados de evaluación
- `outputs/` — audio, métricas, plots y logs generados
- `tests/` — pruebas unitarias e integración
- `scripts/` — scripts auxiliares
- `requirements/` — dependencias por módulo

## Preparación del dataset

Fase exclusivamente de datos: CoVoST 2 como corpus de traducción e inspección,
y una pequeña muestra de audio de FLEURS como dataset de evaluación
Speech-to-Speech (audio + transcripción es + traducción en + split).

Ejecutar en orden en Google Colab. Cada notebook configura su propio entorno e
instala sus dependencias; los archivos de datos, sin embargo, son la salida del
notebook anterior:

1. `notebooks/dataset/00_inspect_covost2.ipynb` — descarga y explora el metadata de
   CoVoST 2 es→en (TSV oficial, ~3 MB) sin Common Voice.
2. `notebooks/dataset/01_sample_fleurs.ipynb` — carga FLEURS `es_419` en streaming,
   guarda 20 audios WAV en `data/raw/audio/` y genera
   `data/processed/manifests/fleurs_sample.csv`.
3. `notebooks/dataset/02_build_evaluation_dataset.ipynb` — añade traducciones de
   referencia manuales y asigna split dev/test (70/30) → `evaluation_v1.csv`.
4. `notebooks/dataset/03_validate_dataset.ipynb` — valida audios, textos, duraciones
   y posibles leakages; genera el reporte en `outputs/dataset/`.

Detalles de implementación en `src/dataset/` (`covost.py`, `fleurs.py`,
`manifest.py`, `validation.py`). Los datos generados no se suben al repositorio
(ver `.gitignore`).

### Google Colab

La primera celda de cada notebook monta Drive y localiza automáticamente una
carpeta que contenga `src/` y `requirements/dataset.txt`, incluso si está dentro
de otra carpeta o una unidad compartida. Comprueba la ruta que imprime como
`PROJECT_ROOT` antes de continuar.

Si existen varias copias o no se localiza el proyecto, asigna la ruta correcta
en la primera celda, por ejemplo:

```python
PROJECT_ROOT_OVERRIDE = Path("/content/drive/MyDrive/Curso/IA-Proyecto")
```

El notebook 02 requiere completar manualmente `manual_translations.csv` antes
de crear `evaluation_v1.csv`; el 03 requiere que ese archivo ya exista.
