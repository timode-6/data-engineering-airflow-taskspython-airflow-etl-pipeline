import unittest
from datetime import date

from hostel.errors import MappingError
from hostel.mappers import RoomMapper, StudentMapper
from hostel.models import Sex


class RoomMapperTest(unittest.TestCase):
    def test_maps_record(self) -> None:
        room = RoomMapper().map({"id": 7, "name": "Room #7"})
        self.assertEqual(room.id, 7)
        self.assertEqual(room.name, "Room #7")

    def test_missing_field(self) -> None:
        with self.assertRaises(MappingError):
            RoomMapper().map({"id": 7})


class StudentMapperTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mapper = StudentMapper()
        self.record = {
            "birthday": "2011-08-22T00:00:00.000000",
            "id": 0,
            "name": "Peggy Ryan",
            "room": 473,
            "sex": "M",
        }

    def test_maps_record(self) -> None:
        student = self.mapper.map(self.record)
        self.assertEqual(student.id, 0)
        self.assertEqual(student.name, "Peggy Ryan")
        self.assertEqual(student.birthday, date(2011, 8, 22))
        self.assertIs(student.sex, Sex.MALE)
        self.assertEqual(student.room_id, 473)

    def test_accepts_plain_iso_date(self) -> None:
        student = self.mapper.map({**self.record, "birthday": "1999-01-31"})
        self.assertEqual(student.birthday, date(1999, 1, 31))

    def test_rejects_unknown_sex(self) -> None:
        with self.assertRaises(MappingError):
            self.mapper.map({**self.record, "sex": "X"})

    def test_rejects_broken_date(self) -> None:
        with self.assertRaises(MappingError):
            self.mapper.map({**self.record, "birthday": "22.08.2011"})

    def test_rejects_non_numeric_room(self) -> None:
        with self.assertRaises(MappingError):
            self.mapper.map({**self.record, "room": "unknown"})


if __name__ == "__main__":
    unittest.main()
