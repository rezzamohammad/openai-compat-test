# Makefile for OpenAI Compatible API Tester

.PHONY: help install install-dev test test-coverage lint clean run

help:
	@echo "OpenAI Compatible API Tester - Development Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make install        Install production dependencies"
	@echo "  make install-dev    Install development dependencies"
	@echo "  make test           Run test suite"
	@echo "  make test-coverage  Run tests with coverage report"
	@echo "  make lint           Run code quality checks"
	@echo "  make clean          Remove build artifacts and cache"
	@echo "  make run            Run the application (requires .env)"
	@echo ""

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

test:
	python3 -m pytest tests/

test-coverage:
	python3 -m pytest tests/ --cov=src --cov-report=term-missing --cov-report=html

lint:
	@echo "Checking Python syntax..."
	python3 -m py_compile main.py src/*.py tests/*.py
	@echo "✓ Syntax check passed"

clean:
	rm -rf __pycache__ src/__pycache__ tests/__pycache__
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf *.egg-info
	rm -rf dist build
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

run:
	@if [ ! -f .env ]; then \
		echo "Error: .env file not found. Copy .env.example to .env and configure."; \
		exit 1; \
	fi
	python3 main.py

# Development shortcuts
check: lint test

all: clean install-dev test
