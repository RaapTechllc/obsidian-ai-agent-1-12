# syntax=docker/dockerfile:1

# Multi-stage build for optimized production image
# Using official uv images and Python 3.12 on Debian Bookworm Slim

# Stage 1: Builder - Install dependencies
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

# Set working directory
WORKDIR /app

# Enable bytecode compilation for faster startup
ENV UV_COMPILE_BYTECODE=1

# Use copy link mode for cache mounts
ENV UV_LINK_MODE=copy

# Copy dependency files first (better layer caching)
COPY pyproject.toml uv.lock ./

# Install dependencies only (not the project itself)
# This layer is cached unless dependencies change
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-dev

# Copy application source code
COPY . .

# Install the project itself with non-editable install
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable --no-dev

# Stage 2: Runtime - Minimal production image
FROM python:3.12-slim-bookworm

# Build arguments for versioning
ARG VERSION=dev
ARG COMMIT_SHA=unknown

# Set working directory
WORKDIR /app

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only the virtual environment from builder
# This significantly reduces the final image size
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy application code
COPY --chown=appuser:appuser . .

# Ensure the virtual environment is used
ENV PATH="/app/.venv/bin:$PATH"

# Set version metadata
ENV VERSION=${VERSION} \
    COMMIT_SHA=${COMMIT_SHA}

# Create vault mount point and ensure permissions
RUN mkdir -p /vault && chown appuser:appuser /vault

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8123

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8123/health || exit 1

# Run the application with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8123"]
