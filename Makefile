.PHONY: help venv lock install install-dev test lint format check typecheck clean build all
.DEFAULT_GOAL := help

# ==============================================================================
# VARIABLES
# ==============================================================================
PYTHON_INTERP := python3
VENV_DIR      := .venv
PYTHON        := $(VENV_DIR)/bin/python
TEST_DIR      := tests/

# ==============================================================================
# SETUP & DEPENDENCIES
# ==============================================================================
help: ## Display this help message.
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

venv: $(PYTHON) ## Create a virtual environment and install dev dependencies.
$(PYTHON):
	@echo "Creating virtual environment in $(VENV_DIR)..."
	$(PYTHON_INTERP) -m venv $(VENV_DIR)
	$(PYTHON) -m pip install -U pip pip-tools
	$(MAKE) install-dev
	$(MAKE) format

lock: $(PYTHON) ## Lock production and development dependencies.
	@echo "Locking dependencies..."
	$(PYTHON) -m piptools compile --resolver=backtracking -o requirements.txt requirements.in
	$(PYTHON) -m piptools compile --resolver=backtracking -o requirements-dev.txt requirements-dev.in

install: $(PYTHON) ## Sync production dependencies and install the project.
	$(PYTHON) -m piptools sync requirements.txt
	$(PYTHON) -m pip install -e .

install-dev: $(PYTHON) ## Sync development dependencies and install the project.
	$(PYTHON) -m piptools sync requirements-dev.txt
	$(PYTHON) -m pip install -e .

# ==============================================================================
# QUALITY & TESTING
# ==============================================================================
test: $(PYTHON) ## Run tests with pytest.
	$(PYTHON) -m pytest $(TEST_DIR) -v

lint: $(PYTHON) ## Check for linting errors with Ruff.
	$(PYTHON) -m ruff check .

format: $(PYTHON) ## Format code and fix all auto-fixable issues with Ruff.
	@echo "Formatting code..."
	$(PYTHON) -m ruff format .
	@echo "Fixing lint issues..."
	$(PYTHON) -m ruff check . --fix --show-fixes

typecheck: $(PYTHON) ## Run static type checking with Mypy.
	$(PYTHON) -m mypy src

check: $(PYTHON) ## Run all checks (format check, lint, typecheck, test).
	@echo "Running all checks..."
	$(PYTHON) -m ruff format --check .
	$(PYTHON) -m ruff check .
	$(PYTHON) -m mypy src
	$(PYTHON) -m pytest $(TEST_DIR)

# ==============================================================================
# BUILD & CLEAN
# ==============================================================================
clean: ## Remove build artifacts, caches, and compiled files.
	@echo "Cleaning up project..."
	# Remove package build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf .eggs/
	find . -type d -name "*.egg-info" -exec rm -rf {} +

	# Remove caches and compiled files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.py[co]" -delete
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -f .coverage

	# Remove the virtual environment
	rm -rf $(VENV_DIR)

build: clean $(PYTHON) ## Build the package.
	$(PYTHON) -m build

all: venv check
