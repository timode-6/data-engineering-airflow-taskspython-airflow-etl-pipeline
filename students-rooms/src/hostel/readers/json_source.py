from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any

from ..errors import SourceError
from .base import RecordSource


class JsonFileSource(RecordSource):

    def __init__(self, path: str | Path, encoding: str = "utf-8") -> None:
        self._path = Path(path)
        self._encoding = encoding

    @property
    def path(self) -> Path:
        return self._path

    def records(self) -> Iterator[Mapping[str, Any]]:
        try:
            with self._path.open(encoding=self._encoding) as stream:
                payload = json.load(stream)
        except FileNotFoundError as exc:
            raise SourceError(f"File not found: {self._path}") from exc
        except OSError as exc:
            raise SourceError(f"Cannot read {self._path}: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise SourceError(f"{self._path} is not valid JSON: {exc}") from exc

        if not isinstance(payload, list):
            raise SourceError(
                f"{self._path}: expected a JSON array at the top level, got {type(payload).__name__}"
            )

        for position, record in enumerate(payload):
            if not isinstance(record, dict):
                raise SourceError(
                    f"{self._path}: element #{position} is {type(record).__name__}, expected an object"
                )
            yield record

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"{type(self).__name__}({str(self._path)!r})"
