.PHONY: test check format install clean

# Install dependencies
install:
	pip install -e ".[dev]"

# Run tests
test:
	pytest

# Run all checks (linting and type checking)
check:
	ruff check .
	mypy .

# Format code
format:
	ruff format .

# Clean up cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .coverage
