VENV ?= .venv
PY   := $(VENV)/bin/python

.PHONY: venv install db-up db-up-pg db-down run run-pg run-xml test lint clean

venv:
	python3 -m venv $(VENV)

install: venv
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -r requirements-dev.txt
	$(PY) -m pip install -e .

db-up-pg:
	docker compose --profile postgresql up -d

db-down:
	docker compose --profile all down

run:
	$(PY) main.py --students data/students.json --rooms data/rooms.json --format json --output out/report.json

run-xml:
	$(PY) main.py --students data/students.json --rooms data/rooms.json --format xml --output out/report.xml

test:
	$(PY) -m pytest -q

lint:
	$(PY) -m ruff check src tests
	$(PY) -m mypy

clean:
	rm -rf out .pytest_cache .mypy_cache .ruff_cache
	find . -name __pycache__ -type d -exec rm -rf {} +
