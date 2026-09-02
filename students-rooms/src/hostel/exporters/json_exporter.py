from __future__ import annotations

import json
from typing import Any, TextIO

from ..report import Report
from .base import ReportExporter, normalise


class JsonReportExporter(ReportExporter):
    format_name = "json"
    extension = "json"

    def __init__(self, indent: int = 2, ensure_ascii: bool = False) -> None:
        self._indent = indent
        self._ensure_ascii = ensure_ascii

    def _payload(self, report: Report) -> dict[str, Any]:
        return {
            "generated_at": report.generated_at.isoformat(),
            "reports": [
                {
                    "name": section.name,
                    "row_count": section.row_count,
                    "rows": [
                        {key: normalise(value) for key, value in row.items()}
                        for row in section.rows
                    ],
                }
                for section in report.sections
            ],
        }

    def export(self, report: Report, stream: TextIO) -> None:
        json.dump(
            self._payload(report),
            stream,
            indent=self._indent,
            ensure_ascii=self._ensure_ascii,
        )
        stream.write("\n")
