import json
import tempfile
import unittest
from pathlib import Path

from hostel.errors import SourceError
from hostel.readers.json_source import JsonFileSource


class JsonFileSourceTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.directory = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _write(self, name: str, content: str) -> Path:
        path = self.directory / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_yields_records(self) -> None:
        path = self._write("rooms.json", json.dumps([{"id": 1, "name": "Room #1"}]))
        self.assertEqual(list(JsonFileSource(path)), [{"id": 1, "name": "Room #1"}])

    def test_missing_file(self) -> None:
        with self.assertRaises(SourceError):
            list(JsonFileSource(self.directory / "absent.json"))

    def test_invalid_json(self) -> None:
        path = self._write("broken.json", "{not json")
        with self.assertRaises(SourceError):
            list(JsonFileSource(path))

    def test_top_level_must_be_an_array(self) -> None:
        path = self._write("object.json", json.dumps({"id": 1}))
        with self.assertRaises(SourceError):
            list(JsonFileSource(path))

    def test_elements_must_be_objects(self) -> None:
        path = self._write("scalars.json", json.dumps([1, 2, 3]))
        with self.assertRaises(SourceError):
            list(JsonFileSource(path))


if __name__ == "__main__":
    unittest.main()
