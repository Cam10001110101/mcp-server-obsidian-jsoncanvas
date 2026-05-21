.PHONY: setup build-ui test lint format run example audit clean

# Create virtual environment and install dependencies (incl. dev extras)
setup:
	uv venv
	uv sync --extra dev

# Build the inline canvas viewer (MCP Apps UI) into jsoncanvas/_ui/viewer.html.
# Requires Node.js; the built bundle is committed, so this is only needed when
# the UI source under ui/ changes.
build-ui:
	cd ui && npm install && npm run build

# Run tests
test:
	uv run pytest

# Run linting
lint:
	uv run ruff check .
	uv run ruff format --check .

# Format code
format:
	uv run ruff format .
	uv run ruff check --fix .

# Run the MCP server (stdio). Use ARGS=... to pass flags, e.g.
#   make run ARGS="--transport streamable-http"
run:
	uv run mcp-server-jsoncanvas $(ARGS)

# Run the library example
example:
	uv run python examples/create_canvas.py

# Audit dependencies for known vulnerabilities.
# PYSEC-2025-183 (CVE-2025-45768) is a disputed pyjwt advisory with no fix; pyjwt
# is only reachable via mcp's optional OAuth path, which this server does not use.
audit:
	uv run --with pip-audit pip-audit --ignore-vuln PYSEC-2025-183

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
