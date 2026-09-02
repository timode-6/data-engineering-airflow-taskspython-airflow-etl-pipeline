from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator, Mapping
from typing import Any


class RecordSource(ABC):

    @abstractmethod
    def records(self) -> Iterator[Mapping[str, Any]]:
        pass

    def __iter__(self) -> Iterator[Mapping[str, Any]]:
        return self.records()
