from __future__ import annotations

from collections.abc import Callable, Mapping

from ..errors import UnsupportedFormatError
from .base import ReportExporter
from .json_exporter import JsonReportExporter
from .xml_exporter import XmlReportExporter


class ExporterFactory:

    def __init__(self, exporters: Mapping[str, Callable[[], ReportExporter]] | None = None) -> None:
        self._exporters: dict[str, Callable[[], ReportExporter]] = dict(
            exporters
            if exporters is not None
            else {
                JsonReportExporter.format_name: JsonReportExporter,
                XmlReportExporter.format_name: XmlReportExporter,
            }
        )

    def register(self, name: str, factory: Callable[[], ReportExporter]) -> None:
        self._exporters[name.lower()] = factory

    def available_formats(self) -> tuple[str, ...]:
        return tuple(sorted(self._exporters))

    def create(self, name: str) -> ReportExporter:
        try:
            factory = self._exporters[name.lower()]
        except KeyError as exc:
            supported = ", ".join(self.available_formats())
            raise UnsupportedFormatError(
                f"Unsupported output format {name!r}. Supported formats: {supported}"
            ) from exc
        return factory()
