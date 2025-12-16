# Dobeu Undertaker - Multi-stage Dockerfile
# DevOps Standards Enforcement & Agent Orchestrator
#
# Build:   docker build -t dobeu-undertaker .
# Run:     docker run -e ANTHROPIC_API_KEY=xxx dobeu-undertaker scan --repo /workspace
# Dev:     docker run -it -v $(pwd):/workspace dobeu-undertaker bash

# =============================================================================
# Stage 1: Builder - Install dependencies and build
# =============================================================================
FROM python:3.11-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.7.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies (without dev dependencies for production)
RUN poetry install --no-dev --no-root

# Copy source code
COPY src/ ./src/
COPY standards/ ./standards/

# Install the package
RUN poetry install --no-dev

# =============================================================================
# Stage 2: Runtime - Minimal production image
# =============================================================================
FROM python:3.11-slim AS runtime

# Labels
LABEL org.opencontainers.image.title="Dobeu Undertaker" \
    org.opencontainers.image.description="DevOps Standards Enforcement & Agent Orchestrator" \
    org.opencontainers.image.vendor="Dobeu Tech Solutions LLC" \
    org.opencontainers.image.authors="jeremyw@dobeu.net" \
    org.opencontainers.image.source="https://github.com/dobeutech/dobeu-undertaker"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    # Default configuration
    DOBEU_ENVIRONMENT=production \
    DOBEU_MONITORING__LOG_LEVEL=INFO

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    # Create non-root user
    && useradd --create-home --shell /bin/bash undertaker

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application
COPY --from=builder /app/src /app/src
COPY --from=builder /app/standards /app/standards

# Set working directory
WORKDIR /workspace

# Switch to non-root user
USER undertaker

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from dobeu_undertaker import __version__; print(__version__)" || exit 1

# Default command
ENTRYPOINT ["python", "-m", "dobeu_undertaker.main"]
CMD ["--help"]

# =============================================================================
# Stage 3: Development - Full development environment
# =============================================================================
FROM builder AS development

# Install dev dependencies
RUN poetry install

# Install additional dev tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    vim \
    less \
    && rm -rf /var/lib/apt/lists/*

# Copy test files
COPY tests/ ./tests/

# Set working directory for development
WORKDIR /workspace

# Default command for development
CMD ["bash"]
