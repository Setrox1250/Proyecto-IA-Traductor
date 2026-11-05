"""Rutas canónicas del proyecto, independientes del directorio de ejecución."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def project_path(*parts: str) -> Path:
    """Devuelve una ruta anclada a la raíz del repositorio."""
    return PROJECT_ROOT.joinpath(*parts)
