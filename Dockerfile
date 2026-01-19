# Multi-stage build for efficiency
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies (opencv needs these)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /root/.local /usr/local

# Copy application code
COPY ./app ./app
COPY ./frontend ./frontend
COPY ./run.py ./run.py

# Create non-root user
RUN useradd -m -u 1000 apiuser && chown -R apiuser:apiuser /app
USER apiuser

# Make Python packages available
ENV PATH=/usr/local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Expose port (Railway sets PORT dynamically)
EXPOSE ${PORT:-8000}

# Health check - use environment variable
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,os; urllib.request.urlopen(f'http://localhost:{os.getenv(\"PORT\",8000)}/health')"

# Run application - use Python script to read PORT variable with debugging
CMD ["python", "run.py"]
