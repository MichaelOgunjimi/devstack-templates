# ── Build stage ──────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files first — changes here invalidate the install layer
COPY pyproject.toml uv.lock ./

# Install production deps into .venv; generates uv.lock if absent
RUN uv sync --no-dev --no-install-project

# ── Runtime stage ────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Create non-root user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Copy only the virtual environment from builder — no uv, no build tools
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY . /app

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

USER appuser

EXPOSE $PORT

CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}
