from __future__ import annotations

import logging
from collections.abc import Iterable, Iterator, Sequence
from contextlib import contextmanager
from typing import Any

from ..config import DatabaseConfig
from ..errors import ConfigurationError, DatabaseError, DuplicateObjectError, UnknownObjectError
from .connection import Database

logger = logging.getLogger(__name__)

DUPLICATE_TABLE = "42P07"
DUPLICATE_OBJECT = "42710"
DUPLICATE_COLUMN = "42701"
UNDEFINED_TABLE = "42P01"
UNDEFINED_OBJECT = "42704"

ALREADY_EXISTS = frozenset({DUPLICATE_TABLE, DUPLICATE_OBJECT, DUPLICATE_COLUMN})
DOES_NOT_EXIST = frozenset({UNDEFINED_TABLE, UNDEFINED_OBJECT})


class PostgresDatabase(Database):

    def __init__(self, config: DatabaseConfig, create_database: bool = True) -> None:
        self._config = config
        self._create_database = create_database
        self._connection: Any | None = None


    @staticmethod
    def _driver() -> Any:
        try:
            import psycopg
        except ImportError as exc:
            raise ConfigurationError(
                "psycopg is not installed. Run: pip install 'psycopg[binary]'"
            ) from exc
        return psycopg

    def _ensure_database(self, psycopg: Any) -> None:
        cfg = self._config
        with psycopg.connect(
            host=cfg.host,
            port=cfg.port,
            user=cfg.user,
            password=cfg.password,
            dbname="postgres",
            autocommit=True,  
        ) as bootstrap:
            exists = bootstrap.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s", (cfg.database,)
            ).fetchone()
            if exists is None:
                bootstrap.execute(f'CREATE DATABASE "{cfg.database}"')
                logger.info("Created database %s", cfg.database)

    def _connect(self) -> Any:
        psycopg = self._driver()
        cfg = self._config
        try:
            if self._create_database:
                self._ensure_database(psycopg)
            connection = psycopg.connect(
                host=cfg.host,
                port=cfg.port,
                user=cfg.user,
                password=cfg.password,
                dbname=cfg.database,
                autocommit=False,
            )
        except psycopg.Error as exc:
            raise DatabaseError(
                f"Cannot connect to PostgreSQL at {cfg.host}:{cfg.port}: {exc}"
            ) from exc

        logger.debug("Connected to postgresql://%s:%s/%s", cfg.host, cfg.port, cfg.database)
        return connection

    @property
    def connection(self) -> Any:
        if self._connection is None:
            self._connection = self._connect()
        return self._connection

    @contextmanager
    def _cursor(self, dictionary: bool = False) -> Iterator[Any]:
        psycopg = self._driver()
        from psycopg.rows import dict_row

        cursor = self.connection.cursor(row_factory=dict_row) if dictionary else self.connection.cursor()
        try:
            yield cursor
        except psycopg.Error as exc:
            raise self._translate(exc) from exc
        finally:
            cursor.close()

    @staticmethod
    def _translate(exc: Any) -> DatabaseError:
        sqlstate = getattr(exc, "sqlstate", None)
        if sqlstate in ALREADY_EXISTS:
            return DuplicateObjectError(str(exc))
        if sqlstate in DOES_NOT_EXIST:
            return UnknownObjectError(str(exc))
        return DatabaseError(str(exc))

    def execute(self, sql: str, params: Sequence[Any] | None = None) -> int:
        with self._cursor() as cursor:
            cursor.execute(sql, tuple(params) if params else None)
            return int(cursor.rowcount)

    def execute_ddl(self, sql: str) -> int:
        with self.connection.transaction():
            return self.execute(sql)

    def execute_many(self, sql: str, rows: Iterable[Sequence[Any]]) -> int:
        batch = [tuple(row) for row in rows]
        if not batch:
            return 0
        with self._cursor() as cursor:
            cursor.executemany(sql, batch)
            return int(cursor.rowcount)

    def fetch_all(self, sql: str, params: Sequence[Any] | None = None) -> list[dict[str, Any]]:
        with self._cursor(dictionary=True) as cursor:
            cursor.execute(sql, tuple(params) if params else None)
            return list(cursor.fetchall())

    @contextmanager
    def transaction(self) -> Iterator[None]:
        connection = self.connection
        try:
            yield
        except Exception:
            connection.rollback()
            raise
        connection.commit()

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None
            logger.debug("Connection closed")
