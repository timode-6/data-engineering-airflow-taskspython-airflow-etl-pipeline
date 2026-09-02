import json
import tempfile
import unittest
from pathlib import Path

from doubles import FakeDatabase
from hostel.cli import Application
from hostel.queries.catalog import QueryCatalog
from hostel.queries.reports import REPORTS

ROOMS = [{"id": 1, "name": "Room #1"}]
STUDENTS = [
    {"id": 1, "name": "A", "birthday": "2000-01-01T00:00:00.000000", "sex": "M", "room": 1},
    {"id": 2, "name": "B", "birthday": "1990-06-30T00:00:00.000000", "sex": "F", "room": 1},
]


class ApplicationTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.directory = Path(self._tmp.name)
        (self.directory / "rooms.json").write_text(json.dumps(ROOMS), encoding="utf-8")
        (self.directory / "students.json").write_text(json.dumps(STUDENTS), encoding="utf-8")
        self.database = FakeDatabase(results=[[{"room_id": 1}] for _ in range(4)])
        self.application = Application(database_factory=lambda config: self.database)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, *extra: str) -> int:
        output = self.directory / "report.json"
        return self.application.run(
            [
                "--students", str(self.directory / "students.json"),
                "--rooms", str(self.directory / "rooms.json"),
                "--output", str(output),
                "--log-level", "ERROR",
                *extra,
            ]
        )

    def test_full_pipeline(self) -> None:
        self.assertEqual(self._run(), 0)

        payload = json.loads((self.directory / "report.json").read_text(encoding="utf-8"))
        self.assertEqual(
            [section["name"] for section in payload["reports"]],
            [query.name for query in QueryCatalog(REPORTS)],
        )
        self.assertEqual(
            [sql.split()[2] for sql, _ in self.database.batches], ["rooms", "students"]
        )
        self.assertTrue(any("CREATE TABLE" in statement for statement in self.database.ddl))
        self.assertTrue(any("CREATE INDEX" in statement for statement in self.database.ddl))
        self.assertEqual(self.database.commits, 1)
        self.assertTrue(self.database.closed)

    def test_no_indexes_flag(self) -> None:
        self.assertEqual(self._run("--no-indexes"), 0)
        self.assertFalse(any("CREATE INDEX" in s for s in self.database.ddl))

    def test_missing_input_file_exits_with_one(self) -> None:
        code = self.application.run(
            [
                "--students", str(self.directory / "absent.json"),
                "--rooms", str(self.directory / "rooms.json"),
                "--log-level", "ERROR",
            ]
        )
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
