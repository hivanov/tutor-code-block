.PHONY: build-data lint format typecheck test install all

PYTHON ?= python3

all: lint typecheck test

build-data:
	$(PYTHON) scripts/extract_languages.py

lint:
	ruff check .

format:
	ruff format .

typecheck:
	mypy code_block_xblock tutor_code_block tests

test:
	pytest -v --tb=short

install:
	pip install -e .
