FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

RUN apt-get update && apt-get install -y curl git && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash app

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p logs
RUN echo "timestamp,pr_url,operation,model,prompt_tokens,completion_tokens,total_tokens,cost_usd,latency_ms" > logs/cost.csv
RUN chown -R app:app /app

USER app

EXPOSE 8000

CMD ["python", "monitoring/pr_guard_monitor.py"]
