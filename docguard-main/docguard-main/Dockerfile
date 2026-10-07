# Builder Stage
FROM python:3.11-slim AS builder

WORKDIR /build

# System dependencies for building wheels (like psycopg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install the project and dependencies as a standard package (not editable)
RUN pip install --no-cache-dir .[mcp]


# Runtime Stage
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install runtime system dependencies (e.g., libpq for psycopg, curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r docguard && useradd -r -g docguard docguard

# Copy the virtual environment from builder
COPY --from=builder --chown=docguard:docguard /opt/venv /opt/venv

# Ensure the venv is active
ENV PATH="/opt/venv/bin:$PATH"

# Run as non-root user
USER docguard

# Expose port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["python", "-m", "uvicorn", "docguard.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
