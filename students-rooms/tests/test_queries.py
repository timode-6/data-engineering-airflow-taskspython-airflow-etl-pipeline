import unittest

from hostel.db.schema import iter_statements
from hostel.queries.base import ReportQuery
from hostel.queries.catalog import QueryCatalog
from hostel.queries.reports import REPORTS


class CatalogTest(unittest.TestCase):
    def test_contains_the_four_required_reports(self) -> None:
        self.assertEqual(
            QueryCatalog(REPORTS).names,
            (
                "students_per_room",
                "rooms_with_smallest_average_age",
                "rooms_with_largest_age_difference",
                "rooms_with_mixed_sex_students",
            ),
        )

    def test_every_query_is_described_and_executable_sql(self) -> None:
        for query in REPORTS:
            with self.subTest(query=query.name):
                self.assertIsInstance(query, ReportQuery)
                self.assertIn("SELECT", query.sql)
                self.assertIn("FROM rooms", query.sql)

    def test_aggregation_happens_in_sql(self) -> None:
        for query in REPORTS:
            with self.subTest(query=query.name):
                self.assertIn("GROUP BY", query.sql)

    def test_top_five_reports_are_limited(self) -> None:
        for name in ("rooms_with_smallest_average_age", "rooms_with_largest_age_difference"):
            with self.subTest(query=name):
                self.assertIn("LIMIT 5", QueryCatalog(REPORTS).get(name).sql)

    def test_rooms_without_students_are_kept_in_the_count_report(self) -> None:
        self.assertIn("LEFT JOIN", QueryCatalog(REPORTS).get("students_per_room").sql)

    def test_duplicate_names_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            QueryCatalog([REPORTS[0], REPORTS[0]])

    def test_unknown_name(self) -> None:
        with self.assertRaises(KeyError):
            QueryCatalog(REPORTS).get("nope")


class SqlScriptTest(unittest.TestCase):
    def test_comments_are_stripped_and_statements_split(self) -> None:
        script = """
        -- a comment
        CREATE INDEX a ON t (x);

        -- another comment
        DROP INDEX b ON t;
        """
        self.assertEqual(
            list(iter_statements(script)),
            ["CREATE INDEX a ON t (x)", "DROP INDEX b ON t"],
        )

    def test_empty_script(self) -> None:
        self.assertEqual(list(iter_statements("-- nothing\n\n;")), [])


if __name__ == "__main__":
    unittest.main()
