"""Almacén temporal de resultados, sin base de datos ni nombres originales."""

from __future__ import annotations

import json
import re
import shutil
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

_JOB_ID = re.compile(r"^[0-9a-f]{32}$")


def _now() -> datetime:
    return datetime.now(UTC)


def _iso(value: datetime) -> str:
    return value.isoformat(timespec="seconds").replace("+00:00", "Z")


class ResultStore:
    """Guarda resultados en directorios UUID con expiración y limpieza."""

    def __init__(self, root: Path, ttl_seconds: int) -> None:
        self.root = Path(root)
        self.ttl_seconds = ttl_seconds
        self._lock = threading.Lock()
        self.root.mkdir(parents=True, exist_ok=True)

    def job_dir(self, job_id: str) -> Path:
        if not _JOB_ID.fullmatch(job_id):
            raise ValueError("Identificador de resultado inválido.")
        return self.root / job_id

    def new_job_dir(self, job_id: str) -> Path:
        directory = self.job_dir(job_id)
        directory.mkdir(parents=True, exist_ok=False)
        return directory

    def save(self, job_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        directory = self.job_dir(job_id)
        if not directory.is_dir():
            raise FileNotFoundError("El directorio del resultado no existe.")
        created_at = _now()
        expires_at = created_at + timedelta(seconds=self.ttl_seconds)
        stored = {
            **payload,
            "created_at": _iso(created_at),
            "expires_at": _iso(expires_at),
        }
        target = directory / "result.json"
        temporary = directory / "result.json.tmp"
        with self._lock:
            temporary.write_text(
                json.dumps(stored, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            temporary.replace(target)
        return stored

    def get(self, job_id: str) -> dict[str, Any] | None:
        try:
            directory = self.job_dir(job_id)
        except ValueError:
            return None
        result_file = directory / "result.json"
        if not result_file.is_file():
            return None
        try:
            payload = json.loads(result_file.read_text(encoding="utf-8"))
            expires_at = datetime.fromisoformat(
                str(payload["expires_at"])
            )
        except (OSError, ValueError, KeyError, json.JSONDecodeError):
            self.delete(job_id)
            return None
        if expires_at <= _now():
            self.delete(job_id)
            return None
        return payload

    def audio_path(self, job_id: str) -> tuple[Path, dict[str, Any]] | None:
        payload = self.get(job_id)
        if payload is None:
            return None
        path = self.job_dir(job_id) / "output.wav"
        if not path.is_file():
            return None
        return path, payload

    def delete(self, job_id: str) -> None:
        try:
            directory = self.job_dir(job_id)
        except ValueError:
            return
        with self._lock:
            shutil.rmtree(directory, ignore_errors=True)

    def cleanup(self) -> int:
        """Elimina resultados vencidos y directorios incompletos antiguos."""
        removed = 0
        now = _now()
        for directory in self.root.iterdir():
            if not directory.is_dir() or not _JOB_ID.fullmatch(directory.name):
                continue
            result_file = directory / "result.json"
            expired = False
            if result_file.is_file():
                try:
                    payload = json.loads(result_file.read_text(encoding="utf-8"))
                    expires_at = datetime.fromisoformat(
                        str(payload["expires_at"])
                    )
                    expired = expires_at <= now
                except (OSError, ValueError, KeyError, json.JSONDecodeError):
                    expired = True
            else:
                try:
                    age = now.timestamp() - directory.stat().st_mtime
                    expired = age > self.ttl_seconds
                except OSError:
                    expired = True
            if expired:
                self.delete(directory.name)
                removed += 1
        return removed
