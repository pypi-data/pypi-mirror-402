.PHONY: help install install-dev test lint format clean build run-cli

# DON'T FORGET TO USE VENV

help:
	@echo "Probely CLI Development Tasks"
	@echo "=============================="
	@echo "  make install       Install package in production mode"
	@echo "  make install-dev   Install package with dev dependencies"
	@echo "  make test          Run all tests with pytest"
	@echo "  make test-cov      Run tests with coverage report"
	@echo "  make lint          Run linting checks with ruff"
	@echo "  make format        Format code with ruff"
	@echo "  make clean         Remove build artifacts and cache"
	@echo "  make run           Run probely CLI (pass ARGS=\"command args\")"
	@echo "  make docs          Build documentation"
	@echo "  make tox           Run full test suite with tox"


install:
	python3 -m pip install -e .

install-dev:
	python3 -m pip install -e ".[dev]"
	python3 -m pip install pytest pytest-cov ruff pre-commit sphinx

test:
	python3 -m pytest tests/ -v

test-cov:
	python3 -m pytest tests/ -v --cov=probely --cov-report=html --cov-report=term

lint:
	ruff check probely/ tests/

format:
	ruff format probely/ tests/
	ruff check --fix probely/ tests/

run:
	python3 -m probely $(ARGS)

docs:
	cd docs && make html

tox:
	tox

.DEFAULT_GOAL := help
