from __future__ import annotations

import sys
from collections.abc import Iterable, Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from hostel.db.connection import Database
from hostel.db.repositories import RoomRepository, StudentRepository

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

class FakeDatabase(Database):

    def __init__(self, results: Sequence[list[dict[str, Any]]] | None = None) -> None:
        self.statements: list[tuple[str, Any]] = []
        self.ddl: list[str] = []
        self.batches: list[tuple[str, list[Sequence[Any]]]] = []
        self.queries: list[str] = []
        self.commits = 0
        self.rollbacks = 0
        self.closed = False
        self._results = list(results or [])

    def execute(self, sql: str, params: Sequence[Any] | None = None) -> int:
        self.statements.append((sql, params))
        return 0

    def execute_ddl(self, sql: str) -> int:
        self.ddl.append(sql)
        return self.execute(sql)

    def execute_many(self, sql: str, rows: Iterable[Sequence[Any]]) -> int:
        materialised = [tuple(row) for row in rows]
        self.batches.append((sql, materialised))
        return len(materialised)

    def fetch_all(self, sql: str, params: Sequence[Any] | None = None) -> list[dict[str, Any]]:
        self.queries.append(sql)
        return self._results.pop(0) if self._results else []

    @contextmanager
    def transaction(self) -> Iterator[None]:
        try:
            yield
        except Exception:
            self.rollbacks += 1
            raise
        self.commits += 1

    def close(self) -> None:
        self.closed = True


class RecordingRepository:

    def __init__(self, log: list[str], label: str) -> None:
        self._log = log
        self._label = label
        self.saved: list[Any] = []
        self.deleted = False

    def save_all(self, items: Iterable[Any]) -> int:
        self._log.append(f"save:{self._label}")
        self.saved = list(items)
        return len(self.saved)

    def delete_all(self) -> int:
        self._log.append(f"delete:{self._label}")
        self.deleted = True
        return 0


class FakeRoomRepository(RecordingRepository, RoomRepository):
    def __init__(self, log: list[str]) -> None:
        super().__init__(log, "rooms")


class FakeStudentRepository(RecordingRepository, StudentRepository):
    def __init__(self, log: list[str]) -> None:
        super().__init__(log, "students")
