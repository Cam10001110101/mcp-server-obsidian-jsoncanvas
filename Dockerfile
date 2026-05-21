# syntax=docker/dockerfile:1
FROM python:3.12-slim AS builder

# uv: copy a pinned static binary from the official image (no curl, no PATH guessing)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Install dependencies first (cached) using the lockfile, then the project.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-install-project --no-dev

COPY jsoncanvas ./jsoncanvas
RUN uv sync --frozen --no-dev


FROM python:3.12-slim

WORKDIR /app

# Copy the prepared virtual environment and the application.
COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH"

# Persistent output directory.
RUN mkdir -p /data/output
ENV OUTPUT_PATH=/data/output

# Run as a non-root user.
RUN useradd --create-home --uid 10001 appuser && chown -R appuser /app /data
USER appuser

# Default to stdio (works with `docker run -i`). For HTTP, append:
#   --transport streamable-http --host 0.0.0.0
# and EXPOSE/publish the port (note: HTTP binds localhost-only Origins by default).
EXPOSE 8000
ENTRYPOINT ["mcp-server-jsoncanvas"]
