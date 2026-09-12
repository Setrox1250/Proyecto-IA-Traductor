"""Inspección del metadata de CoVoST 2 (español a inglés) sin descargar Common Voice.

CoVoST 2 es un corpus de traducción Speech-to-Text construido sobre las grabaciones
de Common Voice. El *metadata* de traducciones se distribuye por separado en un TSV
comprimido con 3 columnas: `path` (clip de audio), `translation` (inglés) y `split`.
La transcripción (`sentence`) y el identificador de hablante (`client_id`) NO están
en el TSV: provienen del `validated.tsv` de Common Voice (versión 4) al hacer la
unión completa. Por eso este módulo nunca descarga Common Voice.
"""

from __future__ import annotations

import tarfile
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from tqdm.auto import tqdm

#: URL oficial del metadata de CoVoST 2 es->en (README de facebookresearch/covost).
COVOST2_ES_EN_URL = "https://dl.fbaipublicfiles.com/covost/covost_v2.es_en.tsv.tar.gz"

#: Columnas reales del TSV de CoVoST 2 (verificado con la versión actual del corpus).
COVOST_COLUMNS = ["path", "translation", "split"]

#: Columnas que solo existen tras unir con Common Voice (validated.tsv).
COMMON_VOICE_COLUMNS = ["sentence", "client_id"]

SEED = 42


def _download_with_progress(url: str, dest: Path) -> Path:
    """Descarga `url` en `dest` mostrando una barra de progreso."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        total = int(response.headers.get("content-length", 0))
        with open(dest, "wb") as file, tqdm(
            total=total, unit="B", unit_scale=True, desc=dest.name
        ) as bar:
            for chunk in response.iter_content(chunk_size=256 * 1024):
                file.write(chunk)
                bar.update(len(chunk))
    return dest


def download_covost_metadata(
    url: str = COVOST2_ES_EN_URL,
    dest_dir: str | Path = "data/raw/metadata",
    force: bool = False,
) -> Path:
    """Descarga y extrae el TSV de metadata de CoVoST 2 es→en.

    Si el TSV ya existe no vuelve a descargar (útil en Colab, las celdas se
    re-ejecutan). Devuelve la ruta al TSV extraído.
    """
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    tsv_path = dest_dir / "covost_v2.es_en.tsv"
    if tsv_path.exists() and not force:
        print(f"El TSV ya existe en {tsv_path}. Se omite la descarga.")
        return tsv_path

    tarball_path = dest_dir / "covost_v2.es_en.tsv.tar.gz"
    _download_with_progress(url, tarball_path)

    with tarfile.open(tarball_path, "r:gz") as archive:
        member = next(m for m in archive.getmembers() if m.name.endswith(".tsv"))
        archive.extract(member, dest_dir)
        extracted = dest_dir / Path(member.name).name

    if extracted != tsv_path:
        extracted.replace(tsv_path)
    print(f"Metadata de CoVoST 2 (es->en) listo en {tsv_path}")
    return tsv_path


def load_covost_metadata(tsv_path: str | Path) -> pd.DataFrame:
    """Carga el TSV de CoVoST 2 en un DataFrame de pandas."""
    tsv_path = Path(tsv_path)
    if not tsv_path.exists():
        raise FileNotFoundError(
            f"No existe {tsv_path}. Ejecuta primero download_covost_metadata()."
        )
    df = pd.read_csv(tsv_path, sep="\t", encoding="utf-8")
    missing = [col for col in COVOST_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"El TSV no contiene las columnas esperadas: {missing}")
    return df


def inspect_covost_metadata(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Devuelve un dict con DataFrames de inspección (columnas, nulos y splits)."""
    return {
        "columns": pd.DataFrame(
            {"column": df.columns, "dtype": df.dtypes.astype(str).values}
        ),
        "missing_values": df.isna().sum().rename("missing").to_frame(),
        "split_distribution": df["split"].value_counts().rename("count").to_frame(),
    }


def random_examples(df: pd.DataFrame, n: int = 5, seed: int = SEED) -> pd.DataFrame:
    """Ejemplos aleatorios reproducibles del metadata."""
    return df.sample(n=n, random_state=seed)


def sample_covost_metadata(
    df: pd.DataFrame,
    n: int = 100,
    seed: int = SEED,
    output_path: str | Path | None = "data/external/translation/covost2_es_en_sample.csv",
) -> pd.DataFrame:
    """Toma una muestra aleatoria reproducible de `n` registros.

    Si `output_path` no es None, guarda la muestra en CSV (UTF-8). Se usa solo
    para inspección local: el metadata no contiene el audio.
    """
    sample = df.sample(n=n, random_state=seed).reset_index(drop=True)
    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        sample.to_csv(output_path, index=False, encoding="utf-8")
        print(f"Muestra guardada en {output_path}")
    return sample


def summarize_covost(
    df: pd.DataFrame, n_examples: int = 5, n_sample: int = 100
) -> dict[str, Any]:
    """Resumen completo de CoVoST 2 es→en para el notebook 00.

    Devuelve informes de inspección, ejemplos y uso previsto, de forma que el
    notebook solo tenga que mostrar el resultado.
    """
    reports = inspect_covost_metadata(df)
    reports["examples"] = df.head(n_examples)
    reports["random_examples"] = random_examples(df, n=n_examples)
    reports["sample"] = sample_covost_metadata(df, n=n_sample)
    reports["total_rows"] = pd.DataFrame(
        {"metric": ["total_registros"], "value": [len(df)]}
    )
    return reports