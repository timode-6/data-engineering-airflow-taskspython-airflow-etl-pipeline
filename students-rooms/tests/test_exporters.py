import io
import json
import unittest
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from decimal import Decimal

from hostel.errors import UnsupportedFormatError
from hostel.exporters.factory import ExporterFactory
from hostel.exporters.json_exporter import JsonReportExporter
from hostel.exporters.xml_exporter import XmlReportExporter
from hostel.report import Report, ReportSection


def sample_report() -> Report:
    return Report(
        generated_at=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
        sections=[
            ReportSection(
                name="students_per_room",
                rows=[
                    {"room_id": 1, "room_name": "Room #1", "students_count": 3},
                    {
                        "room_id": 2,
                        "room_name": "Room #2",
                        "students_count": 0,
                        "average_age_years": Decimal("21.50"),
                        "oldest": date(1999, 5, 4),
                        "note": None,
                    },
                ],
            )
        ],
    )


class JsonExporterTest(unittest.TestCase):
    def test_structure_and_value_conversion(self) -> None:
        stream = io.StringIO()
        JsonReportExporter().export(sample_report(), stream)
        payload = json.loads(stream.getvalue())

        self.assertEqual(payload["generated_at"], "2026-01-01T12:00:00+00:00")
        self.assertEqual(len(payload["reports"]), 1)

        section = payload["reports"][0]
        self.assertEqual(section["name"], "students_per_room")
        self.assertEqual(section["row_count"], 2)

        self.assertEqual(section["rows"][1]["average_age_years"], 21.5)
        self.assertEqual(section["rows"][1]["oldest"], "1999-05-04")
        self.assertIsNone(section["rows"][1]["note"])


class XmlExporterTest(unittest.TestCase):
    def test_structure_and_value_conversion(self) -> None:
        stream = io.StringIO()
        XmlReportExporter().export(sample_report(), stream)
        root = ET.fromstring(stream.getvalue())

        self.assertEqual(root.tag, "report")
        self.assertEqual(root.get("generated_at"), "2026-01-01T12:00:00+00:00")

        query = root.find("query")
        assert query is not None
        self.assertEqual(query.get("name"), "students_per_room")
        self.assertEqual(query.get("row_count"), "2")

        rows = query.findall("row")
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].findtext("room_name"), "Room #1")
        self.assertEqual(rows[1].findtext("average_age_years"), "21.5")
        note = rows[1].find("note")
        assert note is not None
        self.assertEqual(note.get("null"), "true")

    def test_output_is_well_formed_with_declaration(self) -> None:
        stream = io.StringIO()
        XmlReportExporter().export(sample_report(), stream)
        self.assertTrue(stream.getvalue().startswith('<?xml version="1.0" encoding="utf-8"?>'))


class ExporterFactoryTest(unittest.TestCase):
    def test_default_formats(self) -> None:
        self.assertEqual(ExporterFactory().available_formats(), ("json", "xml"))

    def test_creates_by_name_case_insensitively(self) -> None:
        self.assertIsInstance(ExporterFactory().create("JSON"), JsonReportExporter)

    def test_unknown_format(self) -> None:
        with self.assertRaises(UnsupportedFormatError):
            ExporterFactory().create("yaml")

    def test_new_format_needs_no_change_elsewhere(self) -> None:
        factory = ExporterFactory()
        factory.register("compact", lambda: JsonReportExporter(indent=0))
        self.assertIn("compact", factory.available_formats())


if __name__ == "__main__":
    unittest.main()
