from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path

from ..errors import DatabaseError, DuplicateObjectError, SourceError, UnknownObjectError
from .connection import Database

logger = logging.getLogger(__name__)

SQL_ROOT = Path(__file__).resolve().parent.parent / "sql"

SCHEMA_FILE = "schema.sql"
INDEXES_FILE = "indexes.sql"

def iter_statements(script: str) -> Iterator[str]:
    without_comments = "\n".join(
        line for line in script.splitlines() if not line.lstrip().startswith("--")
    )
    for chunk in without_comments.split(";"):
        statement = chunk.strip()
        if statement:
            yield statement


class SchemaManager:

    def __init__(self, database: Database, sql_dir: Path | str = SQL_ROOT) -> None:
        self._database = database
        self._sql_dir = Path(sql_dir)

    def _read(self, filename: str) -> str:
        path = self._sql_dir / filename
        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:
            raise SourceError(f"Cannot read DDL script {path}: {exc}") from exc

    def _apply(self, filename: str) -> None:
        for statement in iter_statements(self._read(filename)):
            try:
                self._database.execute_ddl(statement)
            except (DuplicateObjectError, UnknownObjectError) as exc:
                logger.info("Skipped (already applied): %s", str(exc).strip())
            except DatabaseError:
                logger.error("Failed statement:\n%s", statement)
                raise

    def create_schema(self) -> None:
        logger.info("Applying %s", SCHEMA_FILE)
        self._apply(SCHEMA_FILE)

    def create_indexes(self) -> None:
        logger.info("Applying %s", INDEXES_FILE)
        self._apply(INDEXES_FILE)
