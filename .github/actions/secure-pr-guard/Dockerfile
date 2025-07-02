FROM python:3.11-slim

LABEL "com.github.actions.name"="Secure PR Guard"
LABEL "com.github.actions.description"="AI code review with OWASP LLM compliance"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir \
    openai>=1.0.0 \
    requests>=2.28.0 \
    python-dotenv>=1.0.0 \
    PyYAML>=6.0 \
    GitPython>=3.1.40

# Copy all project files
COPY . .

# Set up entrypoint
COPY .github/actions/secure-pr-guard/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
