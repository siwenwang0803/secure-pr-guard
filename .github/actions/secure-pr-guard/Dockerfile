FROM python:3.11-slim

# Set labels for GitHub Marketplace
LABEL "com.github.actions.name"="Secure PR Guard"
LABEL "com.github.actions.description"="AI code review with OWASP LLM compliance and cost monitoring"
LABEL "com.github.actions.icon"="shield"
LABEL "com.github.actions.color"="blue"
LABEL "repository"="https://github.com/siwenwang0803/secure-pr-guard"
LABEL "homepage"="https://github.com/siwenwang0803/secure-pr-guard"
LABEL "maintainer"="Siwen Wang <your-email@example.com>"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/entrypoint.sh"]