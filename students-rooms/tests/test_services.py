import unittest
from datetime import date

from doubles import FakeDatabase, FakeRoomRepository, FakeStudentRepository
from hostel.db import PostgresStudentRepository
from hostel.db.repositories import chunked
from hostel.models import Room, Sex, Student
from hostel.queries.reports import REPORTS
from hostel.services.importing import ImportService
from hostel.services.reporting import ReportService


def student(id_: int, room: int = 1) -> Student:
    return Student(id=id_, name=f"S{id_}", birthday=date(2000, 1, 1), sex=Sex.MALE, room_id=room)


class ImportServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.log: list[str] = []
        self.database = FakeDatabase()
        self.service = ImportService(
            self.database,
            FakeRoomRepository(self.log),
            FakeStudentRepository(self.log),
        )

    def test_parents_are_written_before_children(self) -> None:
        stats = self.service.run(rooms=[Room(1, "Room #1")], students=[student(1)])
        self.assertEqual(self.log, ["save:rooms", "save:students"])
        self.assertEqual((stats.rooms, stats.students), (1, 1))

    def test_reset_deletes_children_first(self) -> None:
        self.service.run(rooms=[], students=[], reset=True)
        self.assertEqual(
            self.log, ["delete:students", "delete:rooms", "save:rooms", "save:students"]
        )

    def test_commits_once(self) -> None:
        self.service.run(rooms=[Room(1, "Room #1")], students=[])
        self.assertEqual(self.database.commits, 1)
        self.assertEqual(self.database.rollbacks, 0)

    def test_rolls_back_on_failure(self) -> None:
        def exploding_rooms():
            raise RuntimeError("boom")
            yield  

        with self.assertRaises(RuntimeError):
            self.service.run(rooms=exploding_rooms(), students=[])
        self.assertEqual(self.database.rollbacks, 1)
        self.assertEqual(self.database.commits, 0)


class RepositoryTest(unittest.TestCase):
    def test_chunked_splits_the_stream(self) -> None:
        self.assertEqual(list(chunked(range(5), 2)), [[0, 1], [2, 3], [4]])
        self.assertEqual(list(chunked([], 2)), [])

    def test_students_are_written_in_batches(self) -> None:
        database = FakeDatabase()
        repository = PostgresStudentRepository(database, batch_size=2)

        saved = repository.save_all(student(i) for i in range(5))

        self.assertEqual(saved, 5)
        self.assertEqual([len(rows) for _, rows in database.batches], [2, 2, 1])
        first_sql, first_rows = database.batches[0]
        self.assertIn("INSERT INTO students", first_sql)
        self.assertEqual(first_rows[0], (0, "S0", date(2000, 1, 1), "M", 1))


class ReportServiceTest(unittest.TestCase):
    def test_runs_every_query_and_keeps_the_order(self) -> None:
        rows = [[{"room_id": 1}] for _ in REPORTS]
        database = FakeDatabase(results=rows)

        report = ReportService(database, REPORTS).build()

        self.assertEqual(len(report.sections), len(REPORTS))
        self.assertEqual(
            [section.name for section in report.sections],
            [query.name for query in REPORTS],
        )
        self.assertEqual(len(database.queries), len(REPORTS))
        self.assertEqual(report.sections[0].row_count, 1)


if __name__ == "__main__":
    unittest.main()
