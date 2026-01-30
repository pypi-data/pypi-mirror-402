# Backend Dockerfile for human-eval coordination API
# Multi-stage build for smaller final image

FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN pip install --no-cache-dir hatchling

# Copy project files
COPY pyproject.toml .
COPY app/ app/

# Build wheel
RUN pip wheel --no-cache-dir --wheel-dir /wheels .

# ---
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies from wheel
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl && rm -rf /wheels

# Copy application code
COPY app/ app/

# Create data directory for SQLite and eval logs
RUN mkdir -p /app/data/eval_logs

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
