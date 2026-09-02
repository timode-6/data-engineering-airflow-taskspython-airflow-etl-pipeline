from __future__ import annotations

import os
from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from pathlib import Path

from .errors import ConfigurationError

_IDENTIFIER_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_$")

def load_dotenv(path: str | Path = ".env", env: MutableMapping[str, str] | None = None) -> None:
    target = os.environ if env is None else env
    file_path = Path(path)
    if not file_path.is_file():
        return
    for raw_line in file_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'\"")
        if key and key not in target:
            target[key] = value


@dataclass(frozen=True, slots=True)
class DatabaseConfig:

    host: str = "127.0.0.1"
    port: int = 5432
    user: str = "postgres"
    password: str = ""
    database: str = "hostel"

    def __post_init__(self) -> None:
        if not self.database or not set(self.database) <= _IDENTIFIER_CHARS:
            raise ConfigurationError(f"Unsafe database name: {self.database!r}")
        if not 0 < self.port < 65536:
            raise ConfigurationError(f"Port out of range: {self.port}")

    @classmethod
    def from_env(
        cls, env: Mapping[str, str] | None = None
    ) -> DatabaseConfig:

        source = os.environ if env is None else env
        try:
            port = int(source.get("DB_PORT", "5432"))
        except ValueError as exc:
            raise ConfigurationError(f"DB_PORT must be an integer: {exc}") from exc
        return cls(
            host=source.get("DB_HOST", "127.0.0.1"),
            port=port,
            user=source.get("DB_USER", "postgres"),
            password=source.get("DB_PASSWORD", ""),
            database=source.get("DB_NAME", "hostel"),
        )
