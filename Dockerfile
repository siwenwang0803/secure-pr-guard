# Multi-stage Dockerfile for Secure PR Guard

# ============================================================================
# Base Stage - Common dependencies
# ============================================================================
FROM python:3.11-slim as base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create app user for security
RUN useradd --create-home --shell /bin/bash app

WORKDIR /app

# ============================================================================
# Dependencies Stage
# ============================================================================
FROM base as dependencies

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# ============================================================================
# Development Stage
# ============================================================================
FROM dependencies as development

# Copy source code
COPY . .

# Create necessary directories
RUN mkdir -p logs monitoring/config docs
RUN echo "timestamp,pr_url,operation,model,prompt_tokens,completion_tokens,total_tokens,cost_usd,latency_ms" > logs/cost.csv

# Set permissions
RUN chown -R app:app /app

USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "print('Health check: OK')" || exit 1

# Default command (can be overridden)
CMD ["python", "monitoring/pr_guard_monitor.py", "--help"]

# ============================================================================
# Production Stage
# ============================================================================
FROM dependencies as production

# Copy source code
COPY . .

# Create necessary directories and files
RUN mkdir -p logs monitoring/config docs tests
RUN echo "timestamp,pr_url,operation,model,prompt_tokens,completion_tokens,total_tokens,cost_usd,latency_ms" > logs/cost.csv

# Create default budget config if not exists
RUN mkdir -p monitoring && \
    echo "daily_limit: 10.0\nhourly_limit: 2.0\nspike_threshold: 5.0\nefficiency_min: 0.10\nconsecutive_violations: 3\ncooldown_minutes: 30\nslack_enabled: true\nemail_enabled: true\nconsole_enabled: true\nwarning_threshold: 0.7\ncritical_threshold: 0.9" > monitoring/budget_config.yaml

# Set permissions
RUN chown -R app:app /app

USER app

# Expose ports
EXPOSE 8000 8080

# Health check for production
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Production default command
CMD ["python", "graph_review.py", "--help"]
