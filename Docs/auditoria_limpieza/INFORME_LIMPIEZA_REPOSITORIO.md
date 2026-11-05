# Informe de limpieza profunda del repositorio

**Proyecto:** Traducción de Mensajes de Audio con Clonación de Voz mediante Inteligencia Artificial
**Repositorio:** `Setrox1250/Proyecto-IA-Traductor`
**Rama:** `main`
**Fecha:** 2026-11-04
**Tipo de operación:** limpieza profunda con reescritura del historial Git y `push --force` autorizado.

---

## 1. Estado de partida

| Elemento | Valor |
|---|---|
| HEAD previo | `9b75599beaa89a3d1a46ef9ea368a87c7e73ae25` |
| `origin/main` previo | `9b75599beaa89a3d1a46ef9ea368a87c7e73ae25` |
| Árbol de trabajo | Limpio |
| `.git/` | ~1.4 GB |
| `outputs/` | ~1.7 GB |
| Documentos en `Docs/` | 16 archivos `.md` + 4 binarios (`.pdf`, `.docx`) + anexos de auditoría |

El repositorio conservaba informes de auditoría, evidencias de capítulos anteriores, documentos académicos históricos y ejecuciones antiguas de `outputs/` que ya no son necesarios para ejecutar el notebook maestro en Colab.

---

## 2. Respaldo previo

Antes de cualquier borrado se creó un respaldo externo verificado:

**Ruta:** `/home/setrox/ia-proyecto-backups/deep_cleanup_20261104_221050/`

| Archivo | Contenido | SHA-256 |
|---|---|---|
| `repo_history_full.bundle` | Historial Git completo (`git bundle --all`) | `cb74487eb70b1ea0ad33a28f3c55ed1dbcef034eeff6c1ae4ced36b770ac562a` |
| `repo_tracked_HEAD.tar.gz` | Árbol rastreado previo | `0367a516a80adb5a6444400d7eb5824933a6654efda9bf9ae17e995fdb78439f` |
| `docs_current.tar.gz` | Documentación y configuración previas | `cbc45960d5e2fe153e124c18776d04af70d5f4f82b7c5c4c09ddfe473d4810fd` |
| `outputs_small_evidence.tar.gz` | Evidencia no-audio de `outputs/` | `ff69c670151a2f221d4d89c33adb7cd942f6f509832ede8f12fca36a70b8c523` |

Verificaciones realizadas:

- `sha256sum -c SHA256SUMS.txt`: los 4 archivos coinciden.
- `gzip -t`: correcto en los 3 `.tar.gz`.
- `git bundle verify`: el bundle contiene el historial completo.

Este respaldo es la única copia del historial anterior a la reescritura.

---

## 3. Documentación eliminada

Se retiraron los informes de auditoría y evidencias de capítulos anteriores que ya no describen el estado vigente:

| Archivo | Motivo |
|---|---|
| `Docs/AUDITORIA_FINAL_POST_EJECUCION.md` | Auditoría extensa de una fase anterior, con conclusiones y rutas ya superadas |
| `Docs/auditoria_final_evidencias/` | Anexos crudos de esa auditoría (inventarios, logs, textos extraídos) |
| `Docs/CHAPTER_4_EVIDENCE.md` | Evidencia histórica de la primera iteración (256/64/1 y smoke N=3) |
| `Docs/CHAPTER_4_2_EVIDENCE.md` | Evidencia de capítulo 4.2 duplicada por `TECHNICAL_AUDIT.md` |
| `Docs/REPORTE_COMPROBACION_5_1.md` | Comprobación del Capítulo V basada en la reserva v1 |
| `Docs/REPORTE_CONCLUYENTE_EJECUCION_IA.md` | Dossier consolidado con métricas antiguas |
| `Docs/SMOKE_TEST_RESULTS.md` | Resultados de smoke tests históricos |
| `Docs/MASTER_COLAB_EXECUTION_REPORT.md` | Reporte de una ejecución anterior del notebook |
| `Docs/Plan_Semanal_Traductor_IA.pdf` | Planificación, no informe técnico |
| `Docs/Segunda_Entrega_Traductor_IA.docx` | Documento académico anterior (solo capítulos I–II) |
| `Docs/Segunda_Entrega_Traductor_IA.pdf` | Versión PDF del documento anterior |
| `Docs/auditoria_limpieza/*` (anexos crudos) | Inventarios, logs, hashes y salidas de la fase de limpieza anterior |

Se conservó `Docs/auditoria_limpieza/INFORME_LIMPIEZA_REPOSITORIO.md` como único informe de la limpieza.

### Documentación vigente conservada

- `README.md`
- `Docs/INDEX.md`
- `Docs/TECHNICAL_AUDIT.md`
- `Docs/REPORTE_DATASET_B_FINAL.md`
- `Docs/NMT_CONTROLLED_EXPERIMENT_10K.md` y `.json`
- `Docs/REVISION_INFORME_ACADEMICO_FINAL.md`
- `Docs/contexto_alcance.md`
- `Docs/responsabilidades_modelos.md`
- `Docs/auditoria_limpieza/INFORME_LIMPIEZA_REPOSITORIO.md`
- `LICENSE` y `THIRD_PARTY_LICENSES.md`

Se actualizaron las referencias de `README.md`, `Docs/INDEX.md`, `Docs/TECHNICAL_AUDIT.md`, `Docs/NMT_CONTROLLED_EXPERIMENT_10K.md/.json` y `Docs/REVISION_INFORME_ACADEMICO_FINAL.md` para no apuntar a archivos eliminados.

---

## 4. Limpieza de `outputs/`

Se eliminaron las ejecuciones históricas y los artefactos duplicados:

- `outputs/master_colab/` (~1.1 GB, tres runs antiguos con checkpoints duplicados).
- `outputs/comprobacion/` (~330 MB, reserva v1).
- `outputs/final_eval/` excepto el run final `master_20261104_082658`.
- WAVs del run final.
- `outputs/smoke_tests/` (audio y resultados históricos; se conservó `.gitkeep`).
- Contenido histórico de `outputs/audio/`, `outputs/dataset/`, `outputs/logs/`, `outputs/metrics/` y `outputs/plots/` (se conservaron los `.gitkeep`).

### Evidencia final conservada

Se mantienen 73 archivos no-audio (~0.3 MB) del run final:

- `outputs/final_eval/master_20261104_082658/datasetB/aggregate_metrics.json`
- `outputs/final_eval/master_20261104_082658/datasetB/results_per_sample.csv`
- `outputs/final_eval/master_20261104_082658/datasetB/dataset_summary.json`
- `outputs/final_eval/master_20261104_082658/datasetB/exclusions.csv`
- `outputs/final_eval/master_20261104_082658/datasetB/environment.json`
- `outputs/final_eval/master_20261104_082658/datasetB/error_propagation_examples.csv`
- `outputs/final_eval/master_20261104_082658/datasetB/REPORTE_DATASET_B.md`
- Transcripciones, traducciones y metadatos por muestra (`metadata.json`, `transcription.txt`, `translation.txt`).
- `gradio_smoke.json`, `invalid_input_checks.json`, `environment.json`, `execution_summary.json`, `config.json`, `MASTER_REPORT.md`.

El notebook maestro no lee `outputs/` existentes: escribe un run nuevo en cada ejecución. Por tanto, esta limpieza no afecta a Colab.

---

## 5. Archivos rastreados eliminados de Git

Además de los documentos anteriores, se retiraron del tracking los WAV y JSON históricos de `outputs/smoke_tests/` (~19 MB). Permanecen los `.gitkeep` de la estructura de `outputs/`.

Con esto, el árbol rastreado deja de incluir audio histórico y se limita a código, configuración, documentación vigente, notebook maestro, manifiesto oficial y plantillas.

---

## 6. Reescritura del historial Git

Para eliminar los blobs grandes y los commits de auditorías anteriores:

1. Se creó una rama huérfana a partir del árbol final limpio.
2. Se registró un único commit inicial con todo el estado vigente.
3. Se reemplazó `main` por esa rama.
4. Se publicó con `git push --force origin main`.
5. Se ejecutó `git reflog expire --expire=now --all` y `git gc --prune=now --aggressive`.

Resultado esperado: `.git/` pasa de ~1.4 GB a un tamaño acorde con el árbol rastreado (~22 MB de contenido, más metadatos).

> Limitación: GitHub puede conservar temporalmente objetos inalcanzables del historial anterior. El historial local y la rama remota ya no los referencian. La copia recuperable está en el bundle del respaldo.

---

## 7. Integridad de las evidencias

Los siguientes archivos no se modificaron y conservan sus hashes:

| Archivo | SHA-256 |
|---|---|
| `notebooks/Proyecto_IA_Traductor_MASTER_COLAB.ipynb` | `c6a3ecaf74e5bea801d055d107bf1afc8829dfcbd47b4f478789f91e901c0bfb` |
| `data/processed/manifests/fleurs_evaluation_v2_official_test.csv` | `831ac4db2170d79d3d71c01f8e3fa38eb43cce24825620459307745404b4630d` |
| `outputs/final_eval/master_20261104_082658/datasetB/aggregate_metrics.json` | `483d0a034f8e74f7c70985722acabbbc97a12b78a938506358043cbcb4a80475` |
| `outputs/final_eval/master_20261104_082658/datasetB/results_per_sample.csv` | `f5120a483df6f79ce4c0f22769590398b8a5cd1ad310980e5cd0d4e1ff434d6c` |
| `models/checkpoints/controlled_10k/model.safetensors` | `91324a018bbf0d49a5f58d3290612957b172721889a88eec32a402060af1b7a9` |

También se conservan:

- `models/checkpoints/controlled_10k/` (checkpoint del experimento 10k, ignorado por Git).
- `Docs/NMT_CONTROLLED_EXPERIMENT_10K.json` (leído por la celda 18 del notebook maestro).
- `data/processed/manifests/fleurs_evaluation_v2_official_test.csv` (reserva oficial `test`).

---

## 8. Validaciones

| Comprobación | Resultado |
|---|---|
| `pytest tests/ -q` | 17 passed |
| `ruff check src scripts tests` | All checks passed |
| Notebook maestro | 22 celdas, 10 de código, 10 ejecutadas, 0 errores |
| Enlaces locales en Markdown | 0 rotos |
| Métricas vs JSON oficial | Coinciden |
| Hashes de notebook, manifiesto, métricas y checkpoint | Sin cambios |
| `git diff --check` | Sin errores |
| Sincronización local/remoto | Ver `VERIFICACION_FINAL.txt` |

Los detalles exactos del estado posterior al `push --force` se registran en `Docs/auditoria_limpieza/VERIFICACION_FINAL.txt`.

---

## 9. Pendientes

- Decidir si el checkpoint 10k y el run final se publican como release/artefacto externo.
- Añadir capturas de Gradio y evidencia visual.
- Confirmar las licencias de MarianMT, ECAPA, FLEURS y OPUS-100.
- Aplicar las correcciones de `Docs/REVISION_INFORME_ACADEMICO_FINAL.md` al documento académico externo.
- Mantener fuera de Git los artefactos pesados (`outputs/`, checkpoints, ZIPs y entornos virtuales).

---

## 10. Recuperación

Para recuperar el estado anterior a esta limpieza:

```bash
cd /home/setrox/ia-proyecto-backups/deep_cleanup_20261104_221050
sha256sum -c SHA256SUMS.txt
git clone repo_history_full.bundle repositorio_recuperado
```

El bundle contiene el historial completo previo, incluidos los documentos y las evidencias eliminadas.
