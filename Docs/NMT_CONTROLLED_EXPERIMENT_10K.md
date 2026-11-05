# Experimento controlado NMT — MarianMT con 10 000 pares

**Estado:** experimento cerrado. No se ejecutó ni se implementó el entrenamiento de 100 000 pares.
**Commit de los artefactos originales:** `c8041497cd7d194eb5d1417f7f8d8b5f2cda273c`
**Evidencia:** los artefactos originales de la ejecución se retiraron del repositorio durante la limpieza; los valores consolidados están en este documento y en `Docs/NMT_CONTROLLED_EXPERIMENT_10K.json`.

## 1. Objetivo

Verificar que el flujo de ajuste fino de MarianMT funciona de extremo a extremo y comparar el modelo base con un checkpoint entrenado sobre un subconjunto controlado, sin presentar el resultado como mejora.

## 2. Datos

| Elemento | Valor |
|---|---:|
| Corpus | OPUS-100 `en-es` |
| Pares de entrenamiento disponibles | 100 000 |
| Pares usados en el ajuste | **10 000** |
| Pares de validación usados | **1 000** |
| Pares de test | **1 999** |
| Semilla | 42 |
| Split de test | oficial de OPUS-100, sin solapamiento con train/validation |

La selección de los 10 000 pares es la primera parte del `train.csv` preparado con semilla 42. No se barajó de nuevo en el experimento controlado; esto queda documentado para que la comparación sea reproducible.

## 3. Configuración del ajuste

| Hiperparámetro | Valor |
|---|---:|
| Modelo base | `Helsinki-NLP/opus-mt-es-en` |
| Optimizador | AdamW |
| Learning rate | `5e-5` |
| Weight decay | `0.01` |
| Label smoothing | `0.1` |
| Épocas | 1 |
| Batch size por dispositivo | 8 |
| FP16 | Sí, cuando CUDA está disponible |
| `max_length` | 128 |
| `num_beams` (evaluación) | 4 |
| Checkpoint | `models/checkpoints/controlled_10k` |

## 4. Resultados registrados

| Métrica | MarianMT base | Checkpoint 10k | Delta (10k − base) |
|---|---:|---:|---:|
| SacreBLEU | **43.4140** | **42.6499** | **−0.7641** |
| chrF | **64.4179** | **63.6674** | **−0.7506** |
| Eval loss | **1.3532** | **1.4047** | **+0.0514** |
| Muestras test | 1 999 | 1 999 | — |

Tiempo de entrenamiento registrado: `101.194 s`; VRAM pico: `2.713 GiB`; `training_loss`: `2.6417`.

## 5. Interpretación

El ajuste fino con 10 000 pares y una época **no mejora** al modelo base en el test de OPUS-100: baja SacreBLEU y chrF y sube la pérdida. Esto es consistente con un ajuste corto sobre una fracción pequeña del corpus, sin búsqueda de hiperparámetros ni varias épocas.

Por ese motivo:

- El pipeline productivo usa **MarianMT base**.
- El checkpoint se conserva como evidencia del experimento en `models/checkpoints/controlled_10k` y puede seleccionarse explícitamente con `translation_model_name_or_path` o activando `use_controlled_checkpoint` en `configs/translation.yaml`.
- Se verificó una inferencia real del pipeline con ese checkpoint sobre una muestra FLEURS; el metadata registra `translation_checkpoint=controlled_10k` cuando se selecciona explícitamente.
- No se presenta el checkpoint como “modelo mejorado”.
- No se ejecutaron entrenamientos adicionales: no hay justificación experimental para hacerlo sin un diseño nuevo (más épocas, learning rate distinto, currículum o datos adicionales).

## 6. Reproducción

El código del experimento está en `src/translation/train_controlled.py`.

```bash
# Requiere data/processed/translation/{train,validation,test}.csv
python -m src.translation.train_controlled
```

El módulo rechaza `train_samples > 10_000` y no implementa la ruta de 100 000 pares. El script `src/translation/train.py --full` también está bloqueado por diseño.

## 7. Limitaciones

- Una sola época y 10 % del corpus de entrenamiento.
- Sin búsqueda de hiperparámetros.
- Sin evaluación MOS (no aplica a NMT, pero el sistema completo tampoco la tiene).
- El test de 1 999 pares es el oficial de OPUS-100, pero el modelo base ya fue entrenado por sus autores con datos que pueden solaparse con OPUS-100; la comparación es descriptiva, no un benchmark externo limpio.
