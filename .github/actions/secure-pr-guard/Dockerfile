FROM python:3.11-slim

LABEL "com.github.actions.name"="Secure PR Guard"
LABEL "com.github.actions.description"="AI code review with OWASP LLM compliance"

# 安装基础依赖
RUN pip install requests openai python-dotenv

WORKDIR /app
COPY . .
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
