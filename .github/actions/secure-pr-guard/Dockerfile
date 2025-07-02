FROM python:3.11-slim

# 设置标签
LABEL "com.github.actions.name"="Secure PR Guard"
LABEL "com.github.actions.description"="AI code review with OWASP LLM compliance"

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y git curl && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
RUN pip install --no-cache-dir \
    requests \
    openai \
    python-dotenv

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]