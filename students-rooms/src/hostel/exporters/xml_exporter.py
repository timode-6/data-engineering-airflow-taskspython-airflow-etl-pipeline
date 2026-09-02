from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import TextIO

from ..report import Report
from .base import ReportExporter, normalise

_ALLOWED_EXTRA = {"_", "-", "."}


def _tag(name: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in _ALLOWED_EXTRA else "_" for ch in name)
    if not cleaned or not (cleaned[0].isalpha() or cleaned[0] == "_"):
        cleaned = f"_{cleaned}"
    return cleaned


class XmlReportExporter(ReportExporter):
    format_name = "xml"
    extension = "xml"

    def __init__(self, indent: str = "  ") -> None:
        self._indent = indent

    def _build_tree(self, report: Report) -> ET.Element:
        root = ET.Element("report", {"generated_at": report.generated_at.isoformat()})
        for section in report.sections:
            section_element = ET.SubElement(
                root,
                "query",
                {
                    "name": section.name,
                    "row_count": str(section.row_count),
                },
            )
            for row in section.rows:
                row_element = ET.SubElement(section_element, "row")
                for key, value in row.items():
                    cell = ET.SubElement(row_element, _tag(key))
                    normalised = normalise(value)
                    if normalised is None:
                        cell.set("null", "true")
                    else:
                        cell.text = str(normalised)
        return root

    def export(self, report: Report, stream: TextIO) -> None:
        root = self._build_tree(report)
        ET.indent(root, space=self._indent)
        stream.write('<?xml version="1.0" encoding="utf-8"?>\n')
        stream.write(ET.tostring(root, encoding="unicode"))
        stream.write("\n")
