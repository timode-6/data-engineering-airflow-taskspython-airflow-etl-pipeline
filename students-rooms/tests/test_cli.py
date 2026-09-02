import unittest
from pathlib import Path

from hostel.cli import parse_arguments
from hostel.exporters.factory import ExporterFactory

FORMATS = ExporterFactory().available_formats()

class ArgumentParsingTest(unittest.TestCase):
    def test_required_parameters(self) -> None:
        arguments = parse_arguments(
            ["--students", "data/students.json", "--rooms", "data/rooms.json", "--format", "xml"],
            FORMATS,
        )
        self.assertEqual(arguments.students, Path("data/students.json"))
        self.assertEqual(arguments.rooms, Path("data/rooms.json"))
        self.assertEqual(arguments.output_format, "xml")

    def test_output_defaults_to_the_chosen_format(self) -> None:
        arguments = parse_arguments(
            ["--students", "s.json", "--rooms", "r.json", "--format", "xml"], FORMATS
        )
        self.assertEqual(arguments.output, Path("report.xml"))

    def test_dash_means_stdout(self) -> None:
        arguments = parse_arguments(
            ["--students", "s.json", "--rooms", "r.json", "--output", "-"], FORMATS
        )
        self.assertIsNone(arguments.output)

    def test_database_options_override_the_environment(self) -> None:
        arguments = parse_arguments(
            ["--students", "s.json", "--rooms", "r.json", "--db-host", "10.0.0.5", "--db-port",
             "3307"],
            FORMATS,
        )
        self.assertEqual(arguments.database.host, "10.0.0.5")
        self.assertEqual(arguments.database.port, 3307)

    def test_unknown_format_is_rejected(self) -> None:
        with self.assertRaises(SystemExit):
            parse_arguments(["--students", "s.json", "--rooms", "r.json", "--format", "yaml"],
             FORMATS)

    def test_files_are_required_unless_import_is_skipped(self) -> None:
        with self.assertRaises(SystemExit):
            parse_arguments(["--format", "json"], FORMATS)
        arguments = parse_arguments(["--skip-import"], FORMATS)
        self.assertTrue(arguments.skip_import)

if __name__ == "__main__":
    unittest.main()
