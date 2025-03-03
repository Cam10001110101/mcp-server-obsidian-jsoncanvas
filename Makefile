.PHONY: setup test lint format clean

# Create virtual environment and install dependencies
setup:
	uv venv
	uv pip install -r requirements.txt
	uv pip install -e ".[dev]"

# Run tests
test:
	pytest

# Run linting
lint:
	black --check jsoncanvas tests examples
	isort --check jsoncanvas tests examples
	mypy jsoncanvas tests examples

# Format code
format:
	black jsoncanvas tests examples
	isort jsoncanvas tests examples

# Run example
example:
	python examples/create_canvas.py

# Clean up generated files
clean:
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
	rm -rf output
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
