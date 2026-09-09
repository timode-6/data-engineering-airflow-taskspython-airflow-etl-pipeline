from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from . import __version__
from .config import DatabaseConfig, load_dotenv
from .db.connection import Database
from .db.postgres import PostgresDatabase
from .db.repositories import PostgresRoomRepository, PostgresStudentRepository
from .db.schema import SchemaManager
from .errors import HostelError
from .exporters.factory import ExporterFactory
from .mappers import RoomMapper, StudentMapper
from .models import Room, Student
from .queries.catalog import QueryCatalog
from .queries.reports import REPORTS
from .readers.json_source import JsonFileSource
from .services.importing import ImportService
from .services.output import STDOUT_ALIAS, ReportWriter
from .services.reporting import ReportService

logger = logging.getLogger("hostel")


@dataclass(frozen=True, slots=True)
class Arguments:
    students: Path | None
    rooms: Path | None
    output_format: str
    output: Path | None
    reset: bool
    skip_import: bool
    create_indexes: bool
    log_level: str
    database: DatabaseConfig


def build_parser(formats: Sequence[str]) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hostel-report",
        description=(
            "load rooms.json and students.json into a relational database and "
            "export the four required reports as JSON or XML"
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    source = parser.add_argument_group("input")
    source.add_argument("--students", type=Path, help="path to the students file")
    source.add_argument("--rooms", type=Path, help="path to the rooms file")

    output = parser.add_argument_group("output")
    output.add_argument(
        "--format",
        dest="output_format",
        choices=list(formats),
        default="json",
        help="output format",
    )
    output.add_argument(
        "--output",
        type=str,
        default=None,
        help=f"output file; '{STDOUT_ALIAS}' writes to stdout (default: report.<format>)",
    )

    behaviour = parser.add_argument_group("behaviour")
    behaviour.add_argument(
        "--reset", action="store_true", help="delete existing rows before importing"
    )
    behaviour.add_argument(
        "--skip-import", action="store_true", help="only run the reports, do not load the files"
    )
    behaviour.add_argument(
        "--no-indexes",
        dest="create_indexes",
        action="store_false",
        default=True,
        help="apply indexes.sql after the import;--no-indexes to skip "
    )
    behaviour.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="logging verbosity",
    )

    database = parser.add_argument_group("database (defaults come from .env / environment)")
    database.add_argument("--db-host", default=None)
    database.add_argument("--db-port", type=int, default=None)
    database.add_argument("--db-user", default=None)
    database.add_argument("--db-password", default=None)
    database.add_argument("--db-name", default=None)

    return parser


def parse_arguments(argv: Sequence[str] | None, formats: Sequence[str]) -> Arguments:
    load_dotenv()
    parser = build_parser(formats)
    namespace = parser.parse_args(argv)

    if not namespace.skip_import and (namespace.students is None or namespace.rooms is None):
        parser.error("--students and --rooms are required unless --skip-import is given")

    defaults = DatabaseConfig.from_env()
    database = DatabaseConfig(
        host=namespace.db_host or defaults.host,
        port=namespace.db_port or defaults.port,
        user=namespace.db_user or defaults.user,
        password=defaults.password if namespace.db_password is None else namespace.db_password,
        database=namespace.db_name or defaults.database,
    )

    if namespace.output is None:
        output: Path | None = Path(f"report.{namespace.output_format}")
    elif namespace.output == STDOUT_ALIAS:
        output = None
    else:
        output = Path(namespace.output)

    return Arguments(
        students=namespace.students,
        rooms=namespace.rooms,
        output_format=namespace.output_format,
        output=output,
        reset=namespace.reset,
        skip_import=namespace.skip_import,
        create_indexes=namespace.create_indexes,
        log_level=namespace.log_level,
        database=database,
    )


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )


class Application:

    def __init__(
        self,
        exporters: ExporterFactory | None = None,
        database_factory: Callable[[DatabaseConfig], Database] = PostgresDatabase,
    ) -> None:
        self._exporters = exporters or ExporterFactory()
        self._database_factory = database_factory

    @staticmethod
    def _rooms(path: Path) -> Iterable[Room]:
        mapper = RoomMapper()
        return (mapper.map(record) for record in JsonFileSource(path))

    @staticmethod
    def _students(path: Path) -> Iterable[Student]:
        mapper = StudentMapper()
        return (mapper.map(record) for record in JsonFileSource(path))

    def run(self, argv: Sequence[str] | None = None) -> int:
        arguments = parse_arguments(argv, self._exporters.available_formats())
        configure_logging(arguments.log_level)

        try:
            with self._database_factory(arguments.database) as database:
                schema = SchemaManager(database)
                schema.create_schema()

                if not arguments.skip_import:
                    assert arguments.rooms is not None and arguments.students is not None
                    ImportService(
                        database,
                        PostgresRoomRepository(database),
                        PostgresStudentRepository(database),
                    ).run(
                        rooms=self._rooms(arguments.rooms),
                        students=self._students(arguments.students),
                        reset=arguments.reset,
                    )

                if arguments.create_indexes:
                    schema.create_indexes()

                report = ReportService(database, QueryCatalog(REPORTS)).build()
            writer = ReportWriter(self._exporters.create(arguments.output_format))
            writer.write(report, arguments.output)
        except HostelError as error:
            logger.error("%s", error)
            return 1
        except KeyboardInterrupt:
            logger.warning("Interrupted")
            return 130
        return 0


def main(argv: Sequence[str] | None = None) -> int:
    return Application().run(argv)
