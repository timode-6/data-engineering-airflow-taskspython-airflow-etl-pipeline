
from __future__ import annotations

import logging
import time
from collections.abc import Iterable
from dataclasses import dataclass

from ..db.connection import Database
from ..db.repositories import RoomRepository, StudentRepository
from ..models import Room, Student

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ImportStats:
    rooms: int
    students: int
    elapsed_seconds: float

    def __str__(self) -> str:
        return (
            f"{self.rooms} rooms and {self.students} students "
            f"imported in {self.elapsed_seconds:.2f}s"
        )


class ImportService:

    def __init__(
        self,
        database: Database,
        room_repository: RoomRepository,
        student_repository: StudentRepository,
    ) -> None:
        self._database = database
        self._rooms = room_repository
        self._students = student_repository

    def run(
        self,
        rooms: Iterable[Room],
        students: Iterable[Student],
        reset: bool = False,
    ) -> ImportStats:
        started = time.perf_counter()
        with self._database.transaction():
            if reset:
                deleted_students = self._students.delete_all()
                deleted_rooms = self._rooms.delete_all()
                logger.info(
                    "Reset: removed %d students and %d rooms", deleted_students, deleted_rooms
                )
            room_count = self._rooms.save_all(rooms)
            student_count = self._students.save_all(students)

        stats = ImportStats(
            rooms=room_count,
            students=student_count,
            elapsed_seconds=time.perf_counter() - started,
        )
        logger.info("%s", stats)
        return stats
