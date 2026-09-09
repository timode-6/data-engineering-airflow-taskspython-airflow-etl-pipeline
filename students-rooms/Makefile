VENV ?= .venv

ifeq ($(OS),Windows_NT)
    PY        := $(VENV)/Scripts/python.exe
    SYSTEM_PY := python
else
    PY        := $(VENV)/bin/python
    SYSTEM_PY := python3
endif

STUDENTS ?= data/students.json
ROOMS ?= data/rooms.json
OUT ?= out/report.json

venv:
	$(SYSTEM_PY) -m venv $(VENV)

install: venv
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e ".[dev]"

db-up:
	docker compose up -d

db-down:
	docker compose down

db-reset:
	docker compose down -v

run:
	$(PY) main.py --students $(STUDENTS) --rooms $(ROOMS) --format json --output $(OUT)

run-xml:
	$(PY) main.py --students $(STUDENTS) --rooms $(ROOMS) --format xml --output out/report.xml

explain:
	$(PY) scripts/capture_plans.py

test:
	$(PY) -m pytest -q

lint:
	$(PY) -m ruff check src tests
	$(PY) -m mypy

clean:
	$(PY) -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]"
	$(PY) -c "import shutil; [shutil.rmtree(d, ignore_errors=True) for d in ('out', '.pytest_cache', '.mypy_cache', '.ruff_cache')]"