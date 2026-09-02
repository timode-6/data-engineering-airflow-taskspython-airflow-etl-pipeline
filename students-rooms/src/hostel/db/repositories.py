from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator, Sequence
from typing import Generic, TypeVar

from ..models import Room, Student
from .connection import Database

logger = logging.getLogger(__name__)

T = TypeVar("T")

DEFAULT_BATCH_SIZE = 1_000


def chunked(items: Iterable[T], size: int) -> Iterator[list[T]]:
    if size < 1:
        raise ValueError("size must be >= 1")
    batch: list[T] = []
    for item in items:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


class Repository(ABC, Generic[T]):
    @abstractmethod
    def save_all(self, items: Iterable[T]) -> int:
        pass

    @abstractmethod
    def delete_all(self) -> int:
        pass


class RoomRepository(Repository[Room]):
    pass


class StudentRepository(Repository[Student]):
    pass


class _SqlRepository:
    table: str = ""
    insert_sql: str = ""

    def __init__(self, database: Database, batch_size: int = DEFAULT_BATCH_SIZE) -> None:
        self._database = database
        self._batch_size = batch_size

    def _save_rows(self, rows: Iterable[Sequence[object]]) -> int:
        saved = 0
        for batch in chunked(rows, self._batch_size):
            self._database.execute_many(self.insert_sql, batch)
            saved += len(batch)
            logger.debug("%s: %d rows written", self.table, saved)
        return saved

    def delete_all(self) -> int:
        return self._database.execute(f"DELETE FROM {self.table}")


class PostgresRoomRepository(_SqlRepository, RoomRepository):
    table = "rooms"
    insert_sql = (
        "INSERT INTO rooms (id, name) VALUES (%s, %s) "
        "ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name"
    )

    def save_all(self, items: Iterable[Room]) -> int:
        return self._save_rows((room.id, room.name) for room in items)


class PostgresStudentRepository(_SqlRepository, StudentRepository):
    table = "students"
    insert_sql = (
        "INSERT INTO students (id, name, birthday, sex, room) VALUES (%s, %s, %s, %s, %s) "
        "ON CONFLICT (id) DO UPDATE SET "
        "name = EXCLUDED.name, birthday = EXCLUDED.birthday, "
        "sex = EXCLUDED.sex, room = EXCLUDED.room"
    )

    def save_all(self, items: Iterable[Student]) -> int:
        return self._save_rows(
            (student.id, student.name, student.birthday, student.sex.value, student.room_id)
            for student in items
        )
