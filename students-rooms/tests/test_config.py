import unittest

from hostel.config import DatabaseConfig, load_dotenv
from hostel.errors import ConfigurationError


class DatabaseConfigTest(unittest.TestCase):
    def test_reads_environment(self) -> None:
        config = DatabaseConfig.from_env(
            {
                "DB_HOST": "db.internal",
                "DB_PORT": "3307",
                "DB_USER": "hostel",
                "DB_PASSWORD": "secret",
                "DB_NAME": "hostel_test",
            }
        )
        self.assertEqual(config.host, "db.internal")
        self.assertEqual(config.port, 3307)
        self.assertEqual(config.database, "hostel_test")

    def test_falls_back_to_defaults(self) -> None:
        config = DatabaseConfig.from_env({})
        self.assertEqual(config.host, "127.0.0.1")
        self.assertEqual(config.port, 5432)

    def test_rejects_non_numeric_port(self) -> None:
        with self.assertRaises(ConfigurationError):
            DatabaseConfig.from_env({"DB_PORT": "not-a-port"})

    def test_rejects_unsafe_database_name(self) -> None:
        with self.assertRaises(ConfigurationError):
            DatabaseConfig(database="hostel; DROP DATABASE postgresql")


class DotenvTest(unittest.TestCase):
    def test_loads_file_without_overriding_environment(self) -> None:
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text("# comment\nDB_HOST=from-file\nDB_USER='quoted'\n", encoding="utf-8")
            env = {"DB_HOST": "from-environment"}
            load_dotenv(path, env)

        self.assertEqual(env["DB_HOST"], "from-environment")
        self.assertEqual(env["DB_USER"], "quoted")

    def test_missing_file_is_ignored(self) -> None:
        env: dict[str, str] = {}
        load_dotenv("/nonexistent/.env", env)
        self.assertEqual(env, {})


if __name__ == "__main__":
    unittest.main()
