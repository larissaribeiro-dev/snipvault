.PHONY: install run test lint format

install:
	pip install -e ".[dev]"

run:
	snipvault --reload

test:
	pytest

lint:
	ruff check .
	ruff format --check .

format:
	ruff check --fix .
	ruff format .
