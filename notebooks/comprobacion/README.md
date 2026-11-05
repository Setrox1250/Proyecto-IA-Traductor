# Notebooks históricos de comprobación

> **Estado:** históricos y superados. El entregable final es
> `notebooks/Proyecto_IA_Traductor_MASTER_COLAB.ipynb`.

Estos notebooks conservan la evidencia de la primera comprobación. No deben
usarse para la evaluación final porque la reserva Dataset B v1 se construyó
sobre el split `train` de FLEURS, no sobre el split oficial `test`.

- `00_master_datasetA_opus100_nmt.ipynb` — experimento NMT de 10 000 pares.
  Sus métricas se conservan en `Docs/NMT_CONTROLLED_EXPERIMENT_10K.md` y
  `Docs/NMT_CONTROLLED_EXPERIMENT_10K.json`.
- `01_master_datasetB_fleurs_s2s.ipynb` — comprobación Dataset B v1. Superado
  por `Docs/REPORTE_DATASET_B_FINAL.md` y el notebook maestro.

La reserva vigente es:

`data/processed/manifests/fleurs_evaluation_v2_official_test.csv`

Para reproducir la evaluación final use:

```bash
python scripts/run_final_evaluation.py \
  --reservation data/processed/manifests/fleurs_evaluation_v2_official_test.csv \
  --output-dir outputs/final_eval/run_001
```
