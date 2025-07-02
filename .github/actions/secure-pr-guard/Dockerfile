FROM python:3.11-slim

LABEL "com.github.actions.name"="Secure PR Guard"
LABEL "com.github.actions.description"="AI code review with OWASP LLM compliance"
LABEL "com.github.actions.icon"="shield"
LABEL "com.github.actions.color"="blue"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install basic Python packages first
RUN pip install --no-cache-dir \
    requests \
    openai \
    python-dotenv

# Copy files
COPY . .
COPY .github/actions/secure-pr-guard/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
