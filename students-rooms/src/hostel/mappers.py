from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from datetime import date, datetime
from typing import Any, Generic, TypeVar

from .errors import MappingError
from .models import Room, Sex, Student

T = TypeVar("T")


class RecordMapper(ABC, Generic[T]):

    @abstractmethod
    def map(self, record: Mapping[str, Any]) -> T:
        pass

def _require(record: Mapping[str, Any], key: str) -> Any:
    try:
        return record[key]
    except KeyError as exc:
        raise MappingError(f"Missing required field {key!r} in record {dict(record)!r}") from exc


def _to_int(value: Any, field: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise MappingError(f"Field {field!r} must be an integer, got {value!r}") from exc


def _to_date(value: Any, field: str) -> date:
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        raise MappingError(f"Field {field!r} must be an ISO-8601 string, got {value!r}")
    try:
        return datetime.fromisoformat(value).date()
    except ValueError as exc:
        raise MappingError(f"Field {field!r} is not a valid ISO-8601 date: {value!r}") from exc


class RoomMapper(RecordMapper[Room]):
    def map(self, record: Mapping[str, Any]) -> Room:
        return Room(
            id=_to_int(_require(record, "id"), "id"),
            name=str(_require(record, "name")),
        )


class StudentMapper(RecordMapper[Student]):
    def map(self, record: Mapping[str, Any]) -> Student:
        raw_sex = _require(record, "sex")
        try:
            sex = Sex(str(raw_sex).upper())
        except ValueError as exc:
            expected = ", ".join(item.value for item in Sex)
            raise MappingError(f"Field 'sex' must be one of {expected}, got {raw_sex!r}") from exc

        return Student(
            id=_to_int(_require(record, "id"), "id"),
            name=str(_require(record, "name")),
            birthday=_to_date(_require(record, "birthday"), "birthday"),
            sex=sex,
            room_id=_to_int(_require(record, "room"), "room"),
        )
