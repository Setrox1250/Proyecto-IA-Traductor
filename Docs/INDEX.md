# Índice documental

**Proyecto:** Traducción de Mensajes de Audio con Clonación de Voz mediante Inteligencia Artificial
**Última actualización:** 2026-11-05
**Run final de referencia:** `outputs/final_eval/master_20261104_082658/`
**Commit de ejecución registrado:** `e2df5999daf5a0635c8986794742fef35f179b1d` (historial anterior a la limpieza)

---

## 1. Documentación vigente

Documentos que describen el estado final y deben usarse para el informe y la publicación:

| Documento | Uso |
|---|---|
| `README.md` | Descripción, instalación, uso, datasets, métricas y licencias |
| `Docs/INDEX.md` | Este índice |
| `Docs/TECHNICAL_AUDIT.md` | Estado técnico consolidado |
| `Docs/REPORTE_DATASET_B_FINAL.md` | Evaluación final FLEURS |
| `Docs/NMT_CONTROLLED_EXPERIMENT_10K.md` | Experimento NMT de 10 000 pares |
| `Docs/NMT_CONTROLLED_EXPERIMENT_10K.json` | Resumen machine-readable del experimento 10k |
| `Docs/REVISION_INFORME_ACADEMICO_FINAL.md` | Revisión orientativa del documento académico I–VI |
| `Docs/contexto_alcance.md` | Contexto y alcance funcional |
| `Docs/responsabilidades_modelos.md` | Responsabilidades y estrategia de aprendizaje |
| `Docs/DEPLOYMENT_IMPLEMENTATION_PLAN.md` | Auditoría y plan de implementación web |
| `Docs/DEPLOYMENT_GUIDE.md` | Instalación, ejecución, Docker, GPU y troubleshooting |
| `Docs/API_DOCUMENTATION.md` | Endpoints, contratos, códigos de error y ejemplos |
| `Docs/END_TO_END_TEST_REPORT.md` | Pruebas de backend, frontend y E2E real |
| `Docs/DEPLOYMENT_STATUS.md` | Estado local vs. despliegue público |
| `Docs/DEPLOYMENT_IMPLEMENTATION_REPORT.md` | Informe integral de la implementación |
| `Docs/deploy_evidence/README.md` | Índice de capturas, logs y artefactos reales |
| `Docs/auditoria_limpieza/INFORME_LIMPIEZA_REPOSITORIO.md` | Limpieza, consolidación y estado final del repositorio |
| `THIRD_PARTY_LICENSES.md` | Licencias de terceros (ubicación real en la raíz) |

> No hay una copia de licencias dentro de `Docs/`; el archivo correcto es `THIRD_PARTY_LICENSES.md` en la raíz.

---

## 2. Evidencias finales

| Ruta | Contenido |
|---|---|
| `notebooks/Proyecto_IA_Traductor_MASTER_COLAB.ipynb` | Notebook maestro ejecutado: 22 celdas, 10 de código, 0 errores |
| `outputs/final_eval/master_20261104_082658/` | Run final: métricas, CSV, JSON y reportes en texto |
| `outputs/final_eval/master_20261104_082658/datasetB/aggregate_metrics.json` | Métricas finales FLEURS |
| `outputs/final_eval/master_20261104_082658/datasetB/results_per_sample.csv` | Resultados por muestra |
| `outputs/final_eval/master_20261104_082658/datasetB/dataset_summary.json` | Cobertura 20/20, 0 exclusiones |
| `outputs/final_eval/master_20261104_082658/gradio_smoke.json` | Evidencia de Gradio |
| `outputs/final_eval/master_20261104_082658/invalid_input_checks.json` | Pruebas de entradas inválidas |
| `data/processed/manifests/fleurs_evaluation_v2_official_test.csv` | Reserva FLEURS oficial `test` |
| `models/checkpoints/controlled_10k/` | Checkpoint del experimento 10k (ignorado por Git) |
| `Docs/auditoria_limpieza/INFORME_LIMPIEZA_REPOSITORIO.md` | Informe de limpieza y estado final |
| `Docs/deploy_evidence/` | Capturas reales, logs de pruebas, respuesta API y WAV generado |
| `deploy/frontend/e2e/fixtures/fleurs_es_419_test_0000.wav` | Muestra FLEURS usada en la prueba E2E |

> Los WAV de ejecuciones históricas se retiraron del repositorio. El notebook maestro regenera los artefactos de audio al ejecutarse. La evidencia web conserva únicamente la muestra FLEURS y el WAV de la prueba E2E.

---

## 3. Documentación retirada

Los informes de auditoría y evidencia de capítulos anteriores se retiraron del árbol de trabajo para evitar duplicidad y conclusiones obsoletas. Se conserva una copia completa en el respaldo externo documentado en `Docs/auditoria_limpieza/INFORME_LIMPIEZA_REPOSITORIO.md`.

El estado vigente debe consultarse únicamente en los documentos de la sección 1 y en las evidencias finales de la sección 2.

---

## 4. Pendientes

| Elemento | Pendiente |
|---|---|
| Documento académico externo I–VI | Aplicar las correcciones de `Docs/REVISION_INFORME_ACADEMICO_FINAL.md` |
| `data/processed/translation/` | Regenerar CSV de OPUS-100 si se quiere repetir el experimento 10k |
| `models/checkpoints/controlled_10k/` | Definir estrategia de distribución (no versionado) |
| `outputs/final_eval/master_20261104_082658/` | Decidir si se publica como release/artefacto externo |
| Gradio | Añadir capturas de pantalla y evidencia visual |
| Web | Capturas de bandeja de descarga y terminales; ver `Docs/deploy_evidence/README.md` |
| Docker backend | Construir y verificar la imagen en un host con GPU/NVIDIA Container Toolkit |
| Despliegue público | Pendiente de autorización, proveedor GPU y presupuesto |
| Licencias | Confirmar model/dataset cards de MarianMT, ECAPA, FLEURS y OPUS-100 |
| GitHub | Historial reescrito; mantener los artefactos pesados fuera de Git |

---

## 5. Fuentes de verdad por tema

| Tema | Fuente principal |
|---|---|
| Métricas finales FLEURS | `outputs/final_eval/master_20261104_082658/datasetB/aggregate_metrics.json` |
| Cobertura y exclusiones | `outputs/final_eval/master_20261104_082658/datasetB/dataset_summary.json` |
| Resultados por muestra | `outputs/final_eval/master_20261104_082658/datasetB/results_per_sample.csv` |
| Entorno de ejecución | `outputs/final_eval/master_20261104_082658/environment.json` |
| Gradio | `outputs/final_eval/master_20261104_082658/gradio_smoke.json` |
| Entradas inválidas | `outputs/final_eval/master_20261104_082658/invalid_input_checks.json` |
| Notebook maestro | `notebooks/Proyecto_IA_Traductor_MASTER_COLAB.ipynb` |
| Experimento NMT 10k | `Docs/NMT_CONTROLLED_EXPERIMENT_10K.json` |
| Licencias | `THIRD_PARTY_LICENSES.md` y `LICENSE` |
| Revisión académica | `Docs/REVISION_INFORME_ACADEMICO_FINAL.md` |

---

## 6. Regla de precedencia documental

Si dos documentos discrepan:

1. Priorizar los archivos de resultados de `outputs/final_eval/master_20261104_082658/`.
2. Después, `Docs/TECHNICAL_AUDIT.md` y `README.md`.
3. Después, `Docs/REPORTE_DATASET_B_FINAL.md` y `Docs/NMT_CONTROLLED_EXPERIMENT_10K.md`.
4. `Docs/REVISION_INFORME_ACADEMICO_FINAL.md` es una guía de revisión, no una fuente de métricas.
