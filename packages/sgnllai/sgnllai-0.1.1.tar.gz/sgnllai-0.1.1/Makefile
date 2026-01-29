.PHONY: all
all: format lint type-check test

.PHONY: help
help:
	@echo
	@echo 'SGN-LLAI'
	@echo
	@echo 'Pipelines:'
	@echo '  make run              superevent pipeline'
	@echo '  make run-bayestar     Bayestar sky localization'
	@echo '  make publish          mock event publisher'
	@echo
	@echo 'Kafka:'
	@echo '  make topics           create topics'
	@echo '  make topics-reset     delete and recreate'
	@echo '  make listen-supers    watch superevent output'
	@echo
	@echo 'Grafana:'
	@echo '  make grafana-setup    datasource + dashboards'
	@echo
	@echo 'Development:'
	@echo '  make all              format, lint, type-check, test'
	@echo '  make test             run tests'
	@echo '  make lint             run linter'
	@echo '  make format           format code'
	@echo '  make install          pip install -e .'
	@echo

# ─────────────────────────────────────────────────────────────────────────────
# Installation
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: install
install:
	pip install -e .

.PHONY: install-dev
install-dev:
	pip install -e ".[dev]"

# ─────────────────────────────────────────────────────────────────────────────
# Code Quality
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: test
test:
	PYTHONPATH=src pytest -v .

.PHONY: test-cov
test-cov:
	PYTHONPATH=src pytest -v --cov=sgnllai --cov-report=term-missing .

.PHONY: lint
lint:
	flake8 .

.PHONY: format
format:
	isort .
	black .

.PHONY: format-check
format-check:
	isort --check-only .
	black --check .

.PHONY: type-check
type-check:
	mypy .

# ─────────────────────────────────────────────────────────────────────────────
# Cleanup
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: clean
clean:
	rm -rf build/ dist/ *.egg-info/ src/*.egg-info/
	rm -rf .pytest_cache/ .mypy_cache/ .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# ─────────────────────────────────────────────────────────────────────────────
# Runtime (pipelines, Kafka, Grafana)
# ─────────────────────────────────────────────────────────────────────────────

include Makefile.run
