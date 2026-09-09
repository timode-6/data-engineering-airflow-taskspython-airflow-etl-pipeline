# Hostel report

Loads two JSON files — a list of rooms and a list of students — into PostgreSQL, then
runs four analytical reports and exports the result as JSON or XML.

All aggregation happens in SQL. Python reads the files, writes the rows and moves the
results out; it never computes an average or a count itself. No ORM — every statement is
hand-written and executed through `psycopg`.

---

## Requirements

| | |
| --- | --- |
| Python | 3.10 or newer |
| PostgreSQL | 13 or newer (developed against 16) |
| Docker | optional, only for the bundled database |
| Dependencies | `psycopg[binary]`; `pytest`, `ruff`, `mypy` for development |

---

## Running it

```bash
git clone <repo> && cd students-rooms

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

cp .env.example .env               # adjust credentials if you are not using Docker
docker compose up -d               # PostgreSQL 16 on 127.0.0.1:5432

python main.py --students data/students.json \
               --rooms    data/rooms.json \
               --format   json \
               --output   out/report.json
```

`make install && make db-up && make run` does the same thing.

The database, the tables and the indexes are created on the first run. Running it again is
safe: rows are upserted on their primary key, so a repeat run updates rather than
duplicates.

### Configuration

Connection settings come from the environment, or from a `.env` file in the working
directory. Real environment variables take precedence.

| Variable | Default |
| --- | --- |
| `DB_HOST` | `127.0.0.1` |
| `DB_PORT` | `5432` |
| `DB_USER` | `postgres` |
| `DB_PASSWORD` | *(empty)* |
| `DB_NAME` | `hostel` |

Any of them can be overridden on the command line with `--db-host`, `--db-port` and so on.

### Command line

```
usage: hostel-report [-h] [--version] [--students STUDENTS] [--rooms ROOMS]
                     [--format {json,xml}] [--output OUTPUT] [--reset]
                     [--skip-import] [--no-indexes]
                     [--log-level {DEBUG,INFO,WARNING,ERROR}]
                     [--db-host DB_HOST] [--db-port DB_PORT] [--db-user DB_USER]
                     [--db-password DB_PASSWORD] [--db-name DB_NAME]
```

| Option | Meaning |
| --- | --- |
| `--students PATH` | Path to the students file |
| `--rooms PATH` | Path to the rooms file |
| `--format {json,xml}` | Output format (default `json`) |
| `--output PATH` | Output file; `-` writes to stdout |
| `--reset` | Delete existing rows before importing |
| `--skip-import` | Only run the reports |
| `--no-indexes` | Skip `indexes.sql`, for comparing query plans |

Exit codes: `0` success, `1` application error, `2` bad arguments, `130` interrupted.

---

## The data

1 000 rooms and 10 000 students. Every student references a room that exists, `sex` is
only ever `M` or `F`, and birthdays span 1903–2019. One room has no residents, which is
why the first report uses a `LEFT JOIN`.

### Schema

```
rooms                         students
─────                         ────────
id    INTEGER  PK   ◄─────────  room     INTEGER  FK
name  VARCHAR(64)               id       INTEGER  PK
                                name     VARCHAR(128)
                                birthday DATE
                                sex      student_sex  ENUM('M','F')
```

Many students to one room. The foreign key is `ON DELETE RESTRICT` — a room with
residents cannot be removed — and `ON UPDATE CASCADE`. Ids come from the source files
rather than being generated, because the files' own identifiers are what the upsert and
the foreign key rely on.

---

## The reports

| Name | Question it answers |
| --- | --- |
| `students_per_room` | Every room and how many students live in it |
| `rooms_with_smallest_average_age` | The five rooms with the lowest average age |
| `rooms_with_largest_age_difference` | The five rooms with the largest age gap |
| `rooms_with_mixed_sex_students` | Rooms holding students of both sexes |

Two decisions worth knowing about:

* **Ages are computed from whole days** and divided by 365.2425 only for display.
  `age()` is avoided deliberately: it returns an `interval`, and interval comparison
  normalises months to 30 days, which can invert the ranking on data where the correct
  order is unambiguous.
* **`ORDER BY` uses the raw expression, never the rounded alias**, so rounding to two
  decimals cannot create ties inside the top five.

Output is a list of sections, each with its name, description, row count and rows. XML
mirrors the JSON structure exactly.

---
## Indexes

```sql
CREATE INDEX idx_students_room_sex ON students (room, sex);
```

Report 4 groups by `room` and reads only `sex`, both carried by this index, so the scan
is index-only — the table is never visited. More importantly, index entries arrive
ordered by `room`, which turns the join into a merge, lets the aggregate stream instead
of building a hash table, and satisfies `ORDER BY r.id` for free. Half the buffers at
10 000 rows, a quarter at 5 million.

An index on `(room, birthday)` was created on the same reasoning for reports 2 and 3,
measured, and removed: the planner never chose it. Those reports read every row and
order by an aggregate, so index ordering cannot help them, and a sequential scan wins
at 10 000 rows while a parallel one wins at 5 million.

Measured plans and the full reasoning: [`docs/explain/explain.md`](docs/explain/explain.md).
---

## Project structure

```
src/hostel/
├── cli.py             argument parsing and the composition root
├── config.py          connection settings, .env reader
├── models.py          Room, Student, Sex
├── mappers.py         raw record → domain object, with validation
├── report.py          Report, ReportSection
├── errors.py          application exception hierarchy
├── readers/           RecordSource → JsonFileSource
├── db/                Database → PostgresDatabase, repositories, SchemaManager
├── queries/           the four reports as objects
├── exporters/         ReportExporter → JSON / XML, behind a factory
├── services/          ImportService, ReportService, ReportWriter
└── sql/               schema.sql, indexes.sql
```

Where the design principles land:

* **Single responsibility** — parsing a *format* (`JsonFileSource`) and interpreting a
  *schema* (`StudentMapper`) are separate classes, as are running the queries, serialising
  the result and writing it somewhere.
* **Open/closed** — a new output format is one `ReportExporter` registered in the factory;
  the CLI takes its `--format` choices from that factory, so it needs no edit. A new
  report is one `ReportQuery` added to the catalog.
* **Dependency inversion** — services depend on the `Database` and repository interfaces,
  never on `psycopg`, which is imported in exactly one module and only when a connection
  is opened.

Loading is streamed through generators and batched a thousand rows at a time, and the
whole import runs in a single transaction: if it fails halfway, nothing is committed.
Rooms are written before students because of the foreign key, and `--reset` deletes them
in the opposite order for the same reason.

---

## Tests

```bash
pytest -q
```

Fifty tests, none of which need a database — the services run against a fake `Database`.
They cover record mapping and its failure modes, malformed input files, insert batching,
transaction rollback, both exporters, the exporter factory, argument parsing and the query
catalog.

Not covered: the `psycopg` adapter itself, which would need an integration test against a
real server — `testcontainers` is the obvious way to close that gap.

```bash
ruff check src tests
mypy
```