from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True, slots=True)
class ReportSection:

    name: str
    rows: Sequence[dict[str, Any]]

    @property
    def row_count(self) -> int:
        return len(self.rows)


@dataclass(frozen=True, slots=True)
class Report:

    sections: Sequence[ReportSection]
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
