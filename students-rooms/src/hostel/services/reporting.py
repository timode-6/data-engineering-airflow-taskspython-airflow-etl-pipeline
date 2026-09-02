from __future__ import annotations

import logging
import time
from collections.abc import Iterable

from ..db.connection import Database
from ..queries.base import ReportQuery
from ..report import Report, ReportSection

logger = logging.getLogger(__name__)


class ReportService:

    def __init__(self, database: Database, queries: Iterable[ReportQuery]) -> None:
        self._database = database
        self._queries = tuple(queries)

    def build(self) -> Report:
        sections: list[ReportSection] = []
        for query in self._queries:
            started = time.perf_counter()
            rows = self._database.fetch_all(query.sql)
            logger.info(
                "%s: %d rows in %.3fs", query.name, len(rows), time.perf_counter() - started
            )
            sections.append(
                ReportSection(name=query.name, rows=rows)
            )
        return Report(sections=sections)
