from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, TextIO

from ..report import Report


class ReportExporter(ABC):

    format_name: str = ""
    extension: str = ""

    @abstractmethod
    def export(self, report: Report, stream: TextIO) -> None:
        pass

def normalise(value: Any) -> Any:
    
    if isinstance(value, Decimal):
        integral = value.to_integral_value()
        return int(integral) if value == integral else float(value)
    if isinstance(value, Enum):
        return normalise(value.value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8", errors="replace")
    return value
