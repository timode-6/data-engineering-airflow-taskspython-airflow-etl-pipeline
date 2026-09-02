from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Iterable, Sequence
from contextlib import AbstractContextManager
from typing import Any

logger = logging.getLogger(__name__)


class Database(ABC):

    @abstractmethod
    def execute(self, sql: str, params: Sequence[Any] | None = None) -> int:
        pass

    @abstractmethod
    def execute_many(self, sql: str, rows: Iterable[Sequence[Any]]) -> int:
        pass

    @abstractmethod
    def execute_ddl(self, sql: str) -> int:
        pass

    @abstractmethod
    def fetch_all(self, sql: str, params: Sequence[Any] | None = None) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    def transaction(self) -> AbstractContextManager[None]:
        pass

    @abstractmethod
    def close(self) -> None:
        pass

    def __enter__(self) -> Database:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
