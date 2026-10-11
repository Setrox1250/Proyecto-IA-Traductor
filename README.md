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

El flujo canónico se ejecuta completo en una sola instancia de Google Colab:

1. Abrir `notebooks/dataset/00_prepare_all_datasets_colab.ipynb`.
2. Seleccionar **Entorno de ejecución → Ejecutar todas**.
3. Descargar el ZIP de resultados desde la última celda.

El notebook contiene directamente el código de procesamiento y clona este
repositorio público para usarlo como directorio del proyecto en Colab. No monta
Google Drive ni depende de los módulos locales de `src/`.

El notebook construye dos conjuntos independientes:

- **Dataset A — aprendizaje NMT:** OPUS-100 `en-es`, con 100 000 pares de
  entrenamiento seleccionados de forma reproducible y los splits oficiales de
  validación y prueba.
- **Dataset B — evaluación Speech-to-Speech:** 20 audios de FLEURS `es_419`, con
  transcripción española y referencia inglesa oficial enlazada mediante el
  identificador multilingüe de la oración.

Los notebooks numerados `00_inspect_covost2.ipynb` a
`03_validate_dataset.ipynb` se conservan como exploraciones modulares y registro
de ejecuciones anteriores. No son necesarios para el flujo canónico.

Detalles de implementación en `src/dataset/` (`covost.py`, `fleurs.py`,
`manifest.py`, `validation.py`). Los datos generados no se suben al repositorio
(ver `.gitignore`).

Los artefactos se comprimen como `IA-Proyecto_dataset_artifacts.zip` y se
descargan directamente desde Colab al finalizar. La implementación está en
`src/dataset/` (`parallel.py`, `fleurs.py`, `manifest.py`, `validation.py`).
El resumen numérico de Dataset A se guarda en
`outputs/dataset/parallel_dataset_summary.csv`.
