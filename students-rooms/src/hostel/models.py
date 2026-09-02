from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import cast


class Sex(str, Enum):

    MALE = "M"
    FEMALE = "F"

    def __str__(self) -> str:  
        return cast(str, self.value)


@dataclass(frozen=True, slots=True)
class Room:
    id: int
    name: str


@dataclass(frozen=True, slots=True)
class Student:
    id: int
    name: str
    birthday: date
    sex: Sex
    room_id: int
