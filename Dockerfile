# Krama AI Backend - Phase 0 Dockerfile
FROM python:3.12-slim

# Set working directory
WORKDIR /krama

# Install build tools required by some wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy core dependency manifest first (Docker layer-caching)
COPY backend/requirements.txt .

# Install core runtime dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Optional ML dependencies: uncomment to enable full OCR / AI pipeline
# COPY backend/requirements-ml.txt .
# RUN pip install --no-cache-dir -r requirements-ml.txt

# Copy application source
COPY backend/ ./backend/
COPY index.html ./
COPY assets/ ./assets/
COPY favicon.svg ./

# Create runtime directories
RUN mkdir -p /krama/backend/uploads /krama/backend/results

# Run as non-root user for security
RUN useradd -m -u 1001 kramauser && \
    chown -R kramauser:kramauser /krama
USER kramauser

# Expose application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/live')"

# Start the FastAPI application
WORKDIR /krama/backend
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
