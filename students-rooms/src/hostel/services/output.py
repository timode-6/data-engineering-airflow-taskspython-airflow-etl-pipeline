"""Use case: put a report somewhere - a file or stdout."""

from __future__ import annotations

import logging
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import TextIO

from ..exporters.base import ReportExporter
from ..report import Report

logger = logging.getLogger(__name__)

STDOUT_ALIAS = "-"


class ReportWriter:

    def __init__(self, exporter: ReportExporter) -> None:
        self._exporter = exporter

    @contextmanager
    def _open(self, destination: Path | None) -> Iterator[TextIO]:
        if destination is None:
            yield sys.stdout
            return
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", encoding="utf-8") as stream:
            yield stream

    def write(self, report: Report, destination: Path | None = None) -> None:
        with self._open(destination) as stream:
            self._exporter.export(report, stream)
        if destination is not None:
            logger.info("Report written to %s", destination)

    def default_path(self, stem: str = "report") -> Path:
        return Path(f"{stem}.{self._exporter.extension}")
